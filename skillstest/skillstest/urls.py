from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'skillstest.views.home', name='home'),
    # url(r'^skillstest/', include('skillstest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'skillstest.views.entry', name='home'),
    url(r'skillstest/$', 'skillstest.views.dashboard', name='dashboard'),
    url(r'skillstest/login/$', 'skillstest.Auth.views.login', name='login'),
    url(r'skillstest/landing/$', 'skillstest.views.entry', name='landing')
)
