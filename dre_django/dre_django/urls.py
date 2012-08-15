from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'dreapp.views.browse', name='browse'),

    # Examples:
    # url(r'^$', 'dre_django.views.home', name='home'),
    # url(r'^dre_django/', include('dre_django.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
