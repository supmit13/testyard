from django.conf.urls import patterns, include, url
from django.conf import settings
from skillstest import settings as mysettings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'/static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': mysettings.STATIC_ROOT}),

)

urlpatterns += patterns('',
    # Examples:
    # url(r'^$', 'skillstest.views.home', name='home'),
    # url(r'^skillstest/', include('skillstest.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^skillstest/admin/$', include(admin.site.urls)),
                        
    url(r'^%s$'%mysettings.REGISTER_URL, 'skillstest.Auth.views.register', name='newuser'),
    url(r'^%s$'%mysettings.DASHBOARD_URL, 'skillstest.views.dashboard', name='dashboard'),
    url("%s$"%mysettings.LOGIN_URL, 'skillstest.Auth.views.login', name='login'),
    url(r'%s$'%mysettings.LOGIN_REDIRECT_URL, 'skillstest.views.profile', name='profile'),
    url(r'%s$'%mysettings.SUBSCRIPTION_URL, 'skillstest.Subscription.views.subscriptions', name='subscription'),
    url(r'%s$'%mysettings.PROFILE_URL, 'skillstest.views.profile', name='profile'),
)
