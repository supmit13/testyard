from django.conf.urls import patterns, include, url
from django.conf import settings
from skillstest import settings as mysettings
import skillstest.utils as skillutils

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'/static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': mysettings.STATIC_ROOT}),

)

urlpatterns += patterns('',
    (r'/media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': mysettings.MEDIA_ROOT}),

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
    url(r'%s$'%mysettings.SUBSCRIPTION_URL, 'skillstest.Subscription.views.subscriptions', name='subscriptions'),
    url(r'%s$'%mysettings.PROFILE_URL, 'skillstest.views.profile', name='profile'),
    url(r'%s$'%mysettings.LOGOUT_URL, 'skillstest.views.logout', name='logout'),
    url(r'%s$'%mysettings.MANAGE_TEST_URL, 'skillstest.Tests.views.manage', name='managetests'),
    url(r'%s$'%mysettings.CREATE_TEST_URL, 'skillstest.Tests.views.create', name='createtests'),
    url(r'%s$'%mysettings.EDIT_TEST_URL, 'skillstest.Tests.views.edit', name='edittests'),
    url(r'%s$'%mysettings.EDIT_CHALLENGE_URL, 'skillstest.Tests.views.editchallenge', name='editchallenge'),
    url(r'%s$'%mysettings.TEST_SUMMARY_URL,'skillstest.Tests.views.testsummary', name='testsummary'),
    url(r'%s$'%mysettings.VIEW_TEST_URL,'skillstest.Tests.views.viewtest', name='viewtest'),
    url(r'%s$'%mysettings.DELETE_CHALLENGE_URL, 'skillstest.Tests.views.deletechallenges', name='deletechallenges'),
    url(r'%s$'%mysettings.SAVE_CHANGES_URL,'skillstest.Tests.views.savechanges', name='savechanges'),
    url(r'%s$'%mysettings.SHOW_USER_VIEW_URL,'skillstest.Tests.views.showuserview', name='showuserview'),
    url(r'%s$'%mysettings.EDIT_EXISTING_TEST_URL,'skillstest.Tests.views.editexistingtest', name='editexistingtest'),
    url(r'%s$'%mysettings.SEND_TEST_INVITATION_URL,'skillstest.Tests.views.sendtestinvitations', name='sendtestinvitations'),
    url(r'%s$'%mysettings.SHOW_TEST_CANDIDATE_MODE_URL,'skillstest.Tests.views.showtestcandidatemode', name='showtestcandidatemode'),
    url(r'%s$'%mysettings.ADD_MORE_URL,'skillstest.Tests.views.addmorechallenges', name='addmorechallenges'),
    url(r'%s$'%mysettings.SEARCH_URL, 'skillstest.Tests.views.search', name='searchtests'),
    url(r'%s$'%mysettings.CLEAR_NEGATIVE_SCORE_URL, 'skillstest.Tests.views.clearnegativescoreurl', name='clearnegativescoreurl'),
    url(r'%s$'%mysettings.DELETE_TEST_URL,'skillstest.Tests.views.deletetest', name='deletetesturl'),
    url(r'%s$'%mysettings.NETWORK_URL, 'skillstest.Users.views.network', name='network'),
    url(r'%s$'%mysettings.ANALYTICS_URL, 'skillstest.Tests.views.analytics', name='analytics'),
    url(r'%s$'%mysettings.ABOUTUS_URL, 'skillstest.views.aboutus', name='aboutus'),
    url(r'%s$'%mysettings.HELP_URL, 'skillstest.views.helpndocs', name='helpndocs'),
    url(r'%s$'%mysettings.CAREER_URL, 'skillstest.views.careers', name='careers'),
    url(r'%s$'%mysettings.availabilityURL, 'skillstest.Auth.views.checkavailability', name='checkavailability'),
    url(r'%s$'%mysettings.ACCTACTIVATION_URL, 'skillstest.Auth.views.acctactivation', name='acctactivation'),
    url(r'%s$'%mysettings.PROFIMG_CHANGE_URL[1:], 'skillstest.views.profileimagechange', name='profileimagechange'),
)

