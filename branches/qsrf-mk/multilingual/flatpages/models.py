from django.core import validators
from django.db import models
from django.contrib.sites.models import Site
import multilingual

try:
    from django.utils.translation import ugettext as _
except:
    # if this fails then _ is a builtin
    pass

class MultilingualFlatPage(models.Model):
    # non-translatable fields first
    url = models.CharField(_('URL'), maxlength=100, validator_list=[validators.isAlphaNumericURL], db_index=True,
        help_text=_("Example: '/about/contact/'. Make sure to have leading and trailing slashes."))
    enable_comments = models.BooleanField(_('enable comments'))
    template_name = models.CharField(_('template name'), maxlength=70, blank=True,
        help_text=_("Example: 'flatpages/contact_page.html'. If this isn't provided, the system will use 'flatpages/default.html'."))
    registration_required = models.BooleanField(_('registration required'), help_text=_("If this is checked, only logged-in users will be able to view the page."))
    sites = models.ManyToManyField(Site)
    

    
    # And now the translatable fields
    class Translation(multilingual.Translation):
        """
        The definition of translation model.

        The multilingual machinery will automatically add these to the
        Category class:
        
         * get_title(language_id=None)
         * set_title(value, language_id=None)
         * get_content(language_id=None)
         * set_content(value, language_id=None)
         * title and content properties using the methods above
        """
        title = models.CharField(_('title'), maxlength=200)
        content = models.TextField(_('content'))
    
    class Meta:
        db_table = 'multilingual_flatpage'
        verbose_name = _('multilingual flat page')
        verbose_name_plural = _('multilingual flat pages')
        ordering = ('url',)
    class Admin:
        fields = (
            (None, {'fields': ('url', 'sites')}),
            ('Advanced options', {'classes': 'collapse', 'fields': ('enable_comments', 'registration_required', 'template_name')}),
        )
        list_filter = ('sites',)
        search_fields = ('url', 'title')

    def __str__(self):
        # this method can be removed after the landing of newforms-admin
        try:
            return "%s -- %s" % (self.url, self.title)
        except multilingual.TranslationDoesNotExist:
            return "-not-available-"

    def __unicode__(self):
        # note that you can use name and description fields as usual
        try:
            return u"%s -- %s" % (self.url, self.title)
        except multilingual.TranslationDoesNotExist:
            return u"-not-available-"

    def get_absolute_url(self):
        return self.url
