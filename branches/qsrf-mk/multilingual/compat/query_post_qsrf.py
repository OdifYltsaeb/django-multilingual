"""
Django-multilingual: a QuerySet subclass for models with translatable
fields.

This file contains the implementation for QSRF Django.
"""

from django.core.exceptions import FieldError
from django.db import connection
from django.db.models.fields import FieldDoesNotExist
from django.db.models.query import QuerySet, Q
from django.db.models.sql.query import Query
from django.db.models.sql.where import WhereNode, EverythingNode, AND, OR

from multilingual.languages import (get_translation_table_alias, get_language_id_list,
                                    get_default_language, get_translated_field_alias)

__ALL__ = ['MultilingualModelQuerySet']

class MultilingualQuery(Query):
    def __init__(self, model, connection, where=WhereNode):
        super(MultilingualQuery, self).__init__(model, connection, where)

    def pre_sql_setup(self):
        """
        Add all the JOINS and WHERES for multilingual data.
        """
        super(MultilingualQuery, self).pre_sql_setup()

    def _setup_joins_with_translation(self, names, opts, alias,
                                      dupe_multis, allow_many=True,
                                      allow_explicit_fk=False, can_reuse=None):
        """
        This is based on a full copy of Query.setup_joins because
        currently I see no way to handle it differently.

        TO DO: there might actually be a way, by splitting a single
        multi-name setup_joins call into separate calls.  Check it.

        -- marcin@elksoft.pl
        
        Compute the necessary table joins for the passage through the fields
        given in 'names'. 'opts' is the Options class for the current model
        (which gives the table we are joining to), 'alias' is the alias for the
        table we are joining to. If dupe_multis is True, any many-to-many or
        many-to-one joins will always create a new alias (necessary for
        disjunctive filters).

        Returns the final field involved in the join, the target database
        column (used for any 'where' constraint), the final 'opts' value and the
        list of tables joined.
        """
        translation_opts = opts.translation_model._meta

        import sys; sys.stderr.write("setup_joins %r, %r, %r\n" % (names,opts, alias))

        joins = [alias]
        last = [0]
        for pos, name in enumerate(names):
            last.append(len(joins))
            if name == 'pk':
                name = opts.pk.name

            try:
                field, model, direct, m2m = opts.get_field_by_name(name)
            except FieldDoesNotExist:
                for f in opts.fields:
                    if allow_explicit_fk and name == f.attname:
                        # XXX: A hack to allow foo_id to work in values() for
                        # backwards compatibility purposes. If we dropped that
                        # feature, this could be removed.
                        field, model, direct, m2m = opts.get_field_by_name(f.name)
                        break
                else:
                    names = opts.get_all_field_names()
                    raise FieldError("Cannot resolve keyword %r into field. "
                            "Choices are: %s" % (name, ", ".join(names)))
            if not allow_many and (m2m or not direct):
                for alias in joins:
                    self.unref_alias(alias)
                raise MultiJoin(pos + 1)

            # translation machinery appears here
            if model == opts.translation_model:
                language_id = translation_opts.translated_fields[name][1]
                if language_id is None:
                    language_id = get_default_language()

                target = field
                continue
            elif model:
                # The field lives on a base class of the current model.
                alias_list = []
                for int_model in opts.get_base_chain(model):
                    lhs_col = opts.parents[int_model].column
                    opts = int_model._meta
                    alias = self.join((alias, opts.db_table, lhs_col,
                            opts.pk.column), exclusions=joins)
                    joins.append(alias)
            cached_data = opts._join_cache.get(name)
            orig_opts = opts

            if direct:
                if m2m:
                    # Many-to-many field defined on the current model.
                    if cached_data:
                        (table1, from_col1, to_col1, table2, from_col2,
                                to_col2, opts, target) = cached_data
                    else:
                        table1 = field.m2m_db_table()
                        from_col1 = opts.pk.column
                        to_col1 = field.m2m_column_name()
                        opts = field.rel.to._meta
                        table2 = opts.db_table
                        from_col2 = field.m2m_reverse_name()
                        to_col2 = opts.pk.column
                        target = opts.pk
                        orig_opts._join_cache[name] = (table1, from_col1,
                                to_col1, table2, from_col2, to_col2, opts,
                                target)

                    int_alias = self.join((alias, table1, from_col1, to_col1),
                            dupe_multis, joins, nullable=True, reuse=can_reuse)
                    alias = self.join((int_alias, table2, from_col2, to_col2),
                            dupe_multis, joins, nullable=True, reuse=can_reuse)
                    joins.extend([int_alias, alias])
                elif field.rel:
                    # One-to-one or many-to-one field
                    if cached_data:
                        (table, from_col, to_col, opts, target) = cached_data
                    else:
                        opts = field.rel.to._meta
                        target = field.rel.get_related_field()
                        table = opts.db_table
                        from_col = field.column
                        to_col = target.column
                        orig_opts._join_cache[name] = (table, from_col, to_col,
                                opts, target)

                    alias = self.join((alias, table, from_col, to_col),
                            exclusions=joins, nullable=field.null)
                    joins.append(alias)
                else:
                    # Non-relation fields.
                    target = field
                    break
            else:
                orig_field = field
                field = field.field
                if m2m:
                    # Many-to-many field defined on the target model.
                    if cached_data:
                        (table1, from_col1, to_col1, table2, from_col2,
                                to_col2, opts, target) = cached_data
                    else:
                        table1 = field.m2m_db_table()
                        from_col1 = opts.pk.column
                        to_col1 = field.m2m_reverse_name()
                        opts = orig_field.opts
                        table2 = opts.db_table
                        from_col2 = field.m2m_column_name()
                        to_col2 = opts.pk.column
                        target = opts.pk
                        orig_opts._join_cache[name] = (table1, from_col1,
                                to_col1, table2, from_col2, to_col2, opts,
                                target)

                    int_alias = self.join((alias, table1, from_col1, to_col1),
                            dupe_multis, joins, nullable=True, reuse=can_reuse)
                    alias = self.join((int_alias, table2, from_col2, to_col2),
                            dupe_multis, joins, nullable=True, reuse=can_reuse)
                    joins.extend([int_alias, alias])
                else:
                    # One-to-many field (ForeignKey defined on the target model)
                    if cached_data:
                        (table, from_col, to_col, opts, target) = cached_data
                    else:
                        local_field = opts.get_field_by_name(
                                field.rel.field_name)[0]
                        opts = orig_field.opts
                        table = opts.db_table
                        from_col = local_field.column
                        to_col = field.column
                        target = opts.pk
                        orig_opts._join_cache[name] = (table, from_col, to_col,
                                opts, target)

                    alias = self.join((alias, table, from_col, to_col),
                            dupe_multis, joins, nullable=True, reuse=can_reuse)
                    joins.append(alias)

        if pos != len(names) - 1:
            raise FieldError("Join on field %r not permitted." % name)

        return field, target, opts, joins, last

    def setup_joins(self, names, opts, alias, dupe_multis, allow_many=True,
            allow_explicit_fk=False, can_reuse=None):
        if hasattr(opts, 'translation_model'):
            return self._setup_joins_with_translation(names, opts, alias, dupe_multis,
                                                      allow_many, allow_explicit_fk,
                                                      can_reuse)
        else:
            return super(MultilingualQuery, self).setup_joins(names, opts, alias, dupe_multis,
                                                              allow_many, allow_explicit_fk,
                                                              can_reuse)

class MultilingualModelQuerySet(QuerySet):
    """
    A specialized QuerySet that knows how to handle translatable
    fields in ordering and filtering methods.
    """

    def __init__(self, model=None, query=None):
        query = query or MultilingualQuery(model, connection)
        super(MultilingualModelQuerySet, self).__init__(model, query)

    def for_language(self, language_id_or_code):
        """
        Set the default language for all objects returned with this
        query.
        """
        clone = self._clone()
        clone._default_language = get_language_id_from_id_or_code(language_id_or_code)
        return clone

    def iterator(self):
        """
        Add the default language information to all returned objects.
        """
        default_language = getattr(self, '_default_language', None)

        for obj in super(MultilingualModelQuerySet, self).iterator():
            obj._default_language = default_language
            yield obj

    def _clone(self, klass=None, **kwargs):
        """
        Override _clone to preserve additional information needed by
        MultilingualModelQuerySet.
        """
        clone = super(MultilingualModelQuerySet, self)._clone(klass, **kwargs)
        clone._default_language = getattr(self, '_default_language', None)
        return clone

    def order_by(self, *field_names):
        if hasattr(self.model._meta, 'translation_model'):
            trans_opts = self.model._meta.translation_model._meta
            new_field_names = []
            for fn in field_names:
                prefix = ''
                if fn[0] == '-':
                    prefix = '-'
                    fn = fn[1:]
                field_and_lang = trans_opts.translated_fields.get(fn)
                if field_and_lang:
                    field, language_id = field_and_lang
                    if language_id is None:
                        language_id = getattr(self, '_default_language', None)
                    real_name = get_translated_field_alias(field.attname,
                                                           language_id)
                    new_field_names.append(prefix + real_name)
                else:
                    new_field_names.append(prefix + field_name)
            return super(MultilingualModelQuerySet, self).order_by(*new_field_names)
        else:
            return super(MultilingualModelQuerySet, self).order_by(*field_names)

