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
    url(r'%s$'%mysettings.SEND_TEST_DATA_URL,'skillstest.Tests.views.gettestdata', name='gettestdata'),
    url(r'%s$'%mysettings.MANAGE_INVITATIONS_URL,'skillstest.Tests.views.manageinvitations', name='manageinvitations'),
    url(r'%s$'%mysettings.SHOW_TEST_CANDIDATE_MODE_URL,'skillstest.Tests.views.showtestcandidatemode', name='showtestcandidatemode'),
    url(r'%s$'%mysettings.INVITATION_ACTIVATION_URL,'skillstest.Tests.views.invitationactivation', name='invitationactivation'),
    url(r'%s$'%mysettings.INVITATION_CANCEL_URL,'skillstest.Tests.views.invitationcancellation', name='invitationcancellation'),
    url(r'%s$'%mysettings.ADD_MORE_URL,'skillstest.Tests.views.addmorechallenges', name='addmorechallenges'),
    url(r'%s$'%mysettings.SEARCH_URL, 'skillstest.AdvSearch.views.advsearch', name='advsearch'),
    url(r'%s$'%mysettings.TESTS_CHALLENGE_SEARCH_URL, 'skillstest.AdvSearch.views.testschallengesearch', name='testschallengesearch'),
    url(r'%s$'%mysettings.USER_SEARCH_URL, 'skillstest.AdvSearch.views.usersearch', name='usersearch'),
    url(r'%s$'%mysettings.CLEAR_NEGATIVE_SCORE_URL, 'skillstest.Tests.views.clearnegativescoreurl', name='clearnegativescoreurl'),
    url(r'%s$'%mysettings.DELETE_TEST_URL,'skillstest.Tests.views.deletetest', name='deletetesturl'),
    url(r'%s$'%mysettings.NETWORK_URL, 'skillstest.Network.views.network', name='network'),
    url(r'%s$'%mysettings.ANALYTICS_URL, 'skillstest.Analytics.views.analytics', name='analytics'),
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
    url(r'%s$'%mysettings.GET_CANVAS_URL, 'skillstest.Tests.views.getcanvas', name='getcanvas'),
    url(r'%s$'%mysettings.SAVE_DRAWING_URL, 'skillstest.Tests.views.savedrawing', name='savedrawing'),
    url(r'%s$'%mysettings.DISQUALIFY_CANDIDATE_URL, 'skillstest.Tests.views.disqualifycandidate', name='disqualifycandidate'),
    url(r'%s$'%mysettings.COPY_TEST_URL, 'skillstest.Tests.views.copytest', name='copytest'),
    url(r'%s$'%mysettings.GET_TEST_SCHEDULE_URL, 'skillstest.Tests.views.gettestschedule', name='gettestschedule'),
    url(r'%s$'%mysettings.ACTIVATE_TEST_BY_CREATOR, 'skillstest.Tests.views.activatetestbycreator', name='activatetestbycreator'),
    url(r'%s$'%mysettings.DEACTIVATE_TEST_BY_CREATOR, 'skillstest.Tests.views.deactivatetestbycreator', name='deactivatetestbycreator'),
    url(r'%s$'%mysettings.CAPTURE_AUDIOVISUAL_URL, 'skillstest.Tests.views.captureaudiovisual', name='captureaudiovisual'),
    url(r'%s$'%mysettings.CREATE_INTERVIEW_URL, 'skillstest.Tests.views.createinterview', name='createinterview'),
    url(r'%s$'%mysettings.CHECK_INT_NAME_AVAILABILITY_URL, 'skillstest.Tests.views.checknameavailability', name='checknameavailability'),
    url(r'%s$'%mysettings.CHALLENGE_STORE_URL, 'skillstest.Tests.views.interviewchallengestore', name='interviewchallengestore'),
    url(r'%s$'%mysettings.BLOB_UPLOAD_URL, 'skillstest.Tests.views.uploadblobdata', name='uploadblobdata'),
    url(r'%s$'%mysettings.ASK_QUESTION_URL, 'skillstest.Tests.views.askquestion', name='askquestion'),
    url(r'%s$'%mysettings.ATTEND_INTERVIEW_URL, 'skillstest.Tests.views.attendinterview', name='attendinterview'),
    url(r'%s$'%mysettings.UPDATE_INTERVIEW_META_URL, 'skillstest.Tests.views.updateinterviewmeta', name='updateinterviewmeta'),

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
    url(r'%s$'%mysettings.TEST_TO_GROUPS_URL, 'skillstest.Network.views.givetesttogroups', name='givetesttogroups'),
    url(r'%s$'%mysettings.GET_TEST_GROUPS_URL, 'skillstest.Network.views.gettestsandgroups', name='gettestsandgroups'),
    url(r'%s$'%mysettings.GET_CONNECTION_INFO_URL, 'skillstest.Network.views.getconnectioninfo', name='getconnectioninfo'),
    url(r'%s$'%mysettings.GET_GROUPS_OWNED_URL, 'skillstest.Network.views.getgroupsownedinfo', name='getgroupsownedinfo'),
    url(r'%s$'%mysettings.GET_GROUPS_MEMBER_URL, 'skillstest.Network.views.getgroupsmemberinfo', name='getgroupsmemberinfo'),
    url(r'%s$'%mysettings.GET_CONN_DICT_URL, 'skillstest.Network.views.getconnectioninfolevel2', name='getconnectioninfolevel2'),
    url(r'%s$'%mysettings.BLOCK_USER_URL, 'skillstest.Network.views.blockuser', name='blockuser'),
    url(r'%s$'%mysettings.UNBLOCK_USER_URL, 'skillstest.Network.views.unblockuser', name='unblockuser'),
    url(r'%s$'%mysettings.REMOVE_USER_URL, 'skillstest.Network.views.removeuser', name='removeuser'),
    url(r'%s$'%mysettings.SEND_MESSAGE_URL, 'skillstest.Network.views.sendmessage', name='sendmessage'),
    url(r'%s$'%mysettings.MANAGE_GROUP_MEMBERS_URL, 'skillstest.Network.views.managegroupmembers', name='managegroupmembers'),
    url(r'%s$'%mysettings.SAVE_GROUP_MEMBERS_URL, 'skillstest.Network.views.savegroupmembers', name='savegroupmembers'),
    url(r'%s$'%mysettings.MEMBER_SEARCH_URL, 'skillstest.Network.views.searchmember', name='searchmember'),

    url(r'%s$'%mysettings.SAVE_OPTIONAL_INFO_URL, 'skillstest.views.saveoptionalinfo', name='saveoptionalinfo'),
    url(r'%s$'%mysettings.SET_TEST_SCHEDULE_URL, 'skillstest.Tests.views.setschedule', name='setschedule'),

    url(r'%s$'%mysettings.DETAIL_HELP_URL, 'skillstest.views.detailedhelp', name='detailedhelp'),

    url(r'%s$'%mysettings.MOBILE_VERIFY_CREDS_URL, 'skillstest.Auth.views.mobile_verifypassword', name='mobile_verifypassword'),
    url(r'%s$'%mysettings.MOBILE_LIST_TESTS_INTERVIEWS_URL, 'skillstest.Tests.views.mobile_listtestsandinterviews', name='mobile_listtestsandinterviews'),
    url(r'%s$'%mysettings.MOBILE_TEST_CREATE_URL, 'skillstest.Tests.views.mobile_createtest', name='mobile_createtest'),
    url(r'%s$'%mysettings.MOBILE_CHALLENGE_ADDITION_URL, 'skillstest.Tests.views.mobile_addchallenge', name='mobile_addchallenge'),
)

