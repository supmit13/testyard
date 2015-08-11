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
    url(r'%s$'%mysettings.SEND_TEST_DATA_URL,'skillstest.Tests.views.sendtestdata', name='sendtestdata'),
    url(r'%s$'%mysettings.MANAGE_INVITATIONS_URL,'skillstest.Tests.views.manageinvitations', name='manageinvitations'),
    url(r'%s$'%mysettings.SHOW_TEST_CANDIDATE_MODE_URL,'skillstest.Tests.views.showtestcandidatemode', name='showtestcandidatemode'),
    url(r'%s$'%mysettings.INVITATION_ACTIVATION_URL,'skillstest.Tests.views.invitationactivation', name='invitationactivation'),
    url(r'%s$'%mysettings.INVITATION_CANCEL_URL,'skillstest.Tests.views.invitationcancellation', name='invitationcancellation'),
    url(r'%s$'%mysettings.ADD_MORE_URL,'skillstest.Tests.views.addmorechallenges', name='addmorechallenges'),
    url(r'%s$'%mysettings.SEARCH_URL, 'skillstest.Tests.views.search', name='searchtests'),
    url(r'%s$'%mysettings.CLEAR_NEGATIVE_SCORE_URL, 'skillstest.Tests.views.clearnegativescoreurl', name='clearnegativescoreurl'),
    url(r'%s$'%mysettings.DELETE_TEST_URL,'skillstest.Tests.views.deletetest', name='deletetesturl'),
    url(r'%s$'%mysettings.NETWORK_URL, 'skillstest.Network.views.network', name='network'),
    url(r'%s$'%mysettings.ANALYTICS_URL, 'skillstest.Tests.views.analytics', name='analytics'),
    url(r'%s$'%mysettings.ABOUTUS_URL, 'skillstest.views.aboutus', name='aboutus'),
    url(r'%s$'%mysettings.HELP_URL, 'skillstest.views.helpndocs', name='helpndocs'),
    url(r'%s$'%mysettings.CAREER_URL, 'skillstest.views.careers', name='careers'),
    url(r'%s$'%mysettings.availabilityURL, 'skillstest.Auth.views.checkavailability', name='checkavailability'),
    url(r'%s$'%mysettings.ACCTACTIVATION_URL, 'skillstest.Auth.views.acctactivation', name='acctactivation'),
    url(r'%s$'%mysettings.PROFIMG_CHANGE_URL[1:], 'skillstest.views.profileimagechange', name='profileimagechange'),
    url(r'%s$'%mysettings.TEST_EVALUATION_URL, 'skillstest.Tests.views.evaluate', name='evaluate'),
    url(r'%s$'%mysettings.EVALUATE_RESPONSE_URL, 'skillstest.Tests.views.evaluateresponses', name='evaluateresponses'),
    url(r'%s$'%mysettings.GET_CURRENT_EVALUATION_DATA_URL, 'skillstest.Tests.views.getevaluationdetails', name='getevaluationdetails'),
    url(r'%s$'%mysettings.TEST_BULK_UPLOAD_URL, 'skillstest.Tests.views.createtestbulkupload', name='createtestbulkupload'),
    url(r'%s$'%mysettings.SHOW_TEST_INFO_URL, 'skillstest.Tests.views.showtestinfo', name='showtestpage'),
    url(r'%s$'%mysettings.SET_VISIBILITY_URL, 'skillstest.Tests.views.setvisibility', name='setvisibility'),

    url(r'%s$'%mysettings.CREATE_NETWORK_GROUP_URL, 'skillstest.Network.views.creategroup', name='creategroup'),
    url(r'%s$'%mysettings.CHECK_GRPNAME_AVAIL_URL, 'skillstest.Network.views.checkgrpnameavailability', name='creategroup'),
    url(r'%s$'%mysettings.SEARCH_GROUP_URL, 'skillstest.Network.views.searchgroups', name='searchgroups'),
    url(r'%s$'%mysettings.GET_GROUP_INFO_URI, 'skillstest.Network.views.getgroupinfo', name='getgroupinfo'),
    url(r'%s$'%mysettings.SEND_JOIN_REQUEST_URL, 'skillstest.Network.views.handlejoinrequest', name='handlejoinrequest'),
    url(r'%s$'%mysettings.SEND_GENTLE_REMINDER_URL, 'skillstest.Network.views.sendgentlereminder', name='sendgentlereminder'),
    url(r'%s$'%mysettings.GET_GROUP_DATA_URL, 'skillstest.Network.views.getgroupdata', name='getgroupdata'),
    url(r'%s$'%mysettings.GROUP_IMG_UPLOAD_URL, 'skillstest.Network.views.groupimgupload', name='groupimgupload'),
    url(r'%s$'%mysettings.SAVE_GROUP_DATA_URL, 'skillstest.Network.views.savegroupdata', name='savegroupdata'),
    url(r'%s$'%mysettings.PAYMENT_GW_URL, 'skillstest.Network.views.showpaymentscreen', name='showpaymentscreen'),
    url(r'%s$'%mysettings.PAYU_CONFIRM_URL, 'skillstest.Network.views.confirmpayment_payu', name='confirmpayment_payu'),
    url(r'%s$'%mysettings.SEARCH_USER_URL, 'skillstest.Network.views.searchuser', name='searchuser'),
    url(r'%s$'%mysettings.SEND_CONNECTION_URL, 'skillstest.Network.views.sendconnectionrequest', name='sendconnectionrequest'),
    url(r'%s$'%mysettings.SAVE_GROUP_JOIN_STATUS_URL, 'skillstest.Network.views.savegroupjoinstatus', name='savegroupjoinstatus'),
    url(r'%s$'%mysettings.CONNECTION_INVITE_HANDLER_URL, 'skillstest.Network.views.handleconnectinvitation', name='handleconnectinvitation'),
    url(r'%s$'%mysettings.POST_MESSAGE_CONTENT_URL, 'skillstest.Network.views.postmessagecontent', name='postmessagecontent'),
    url(r'%s$'%mysettings.POST_REPLY_CONTENT_URL, 'skillstest.Network.views.postreplycontent', name='postreplycontent'),
    url(r'%s$'%mysettings.NEXT_POST_LIST_URL, 'skillstest.Network.views.nextpostlist', name='nextpostlist'),
    url(r'%s$'%mysettings.NEW_MESSAGE_READ_URL, 'skillstest.Network.views.newmessageread', name='newmessageread'),
    url(r'%s$'%mysettings.SEND_MSG_RESPONSE_URL, 'skillstest.Network.views.sendmsgresponse', name='sendmsgresponse'),
    url(r'%s$'%mysettings.MESSAGE_SEARCH_URL, 'skillstest.Network.views.msgsearch', name='msgsearch'),
)

