<font color='red'>NOTE: This library is very old and no longer maintained. Do not use it in new projects.</font>

A library providing support for multilingual content
in [Django](http://www.djangoproject.com/) models.

See the [Introduction](Introduction.md) page for a description, installation instructions and some examples to get you started.

Have a question?  Join our [discussion group](http://groups.google.pl/group/django-multilingual?lnk=)!

**Please note**: this library is the result of dozens of contributions from multiple authors, see the [AUTHORS](http://code.google.com/p/django-multilingual/source/browse/trunk/AUTHORS) file for the full list.  To everyone who put their time into reporting bugs, submitting patches or answered questions: thank you VERY much for making it easier to write great, multilingual software with Django :)

## Current status ##

Django-multilingual supports all versions of Django 1.0 and later.

Plan summary:

  * model API: almost done.  There might be some backwards-incompatible changes to the way the library and multilingual models are configured, but they will not affect the way translation data is stored in the database.
  * admin pages: working, but need to be rewritten.  This will not affect the API.
  * easy way to create forms that allow editing translatable content with oldforms: in progress.
  * configuration: the definitions of LANGUAGES and DEFAULT\_LANGUAGE will change.   See [this post](http://groups.google.com/group/django-users/tree/browse_frm/thread/6a96426735ffd7f1/6018f109f26b735e?rnum=31&_done=%2Fgroup%2Fdjango-users%2Fbrowse_frm%2Fthread%2F6a96426735ffd7f1%2F218eacd2b926ece7%3F#doc_b062f37ebf12ba92) for a description of the most probable direction.
  * documentation: in progress.

If you have questions or suggestions feel free to ask them on [our discussion group](http://groups.google.com/group/django-multilingual).

The library is already being used in real world projects, but there are still quirks to fix and features to add.  With your help we could make it happen faster, so if you would be interested in contributing your time to this project please contact me at [marcin.kaszynski@gmail.com](mailto:marcin.kaszynski@gmail.com).
