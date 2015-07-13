// Operations on a child window created by 'popupjoinrequests()'.
function listselectedstatus(grpname, joinrequestsinfo_strb64){
    selectedstate = document.frmjoingroupaction.requeststate.options[document.frmjoingroupaction.requeststate.selectedIndex].value;
    //alert(selectedstate);
    contentdiv = document.getElementById('contentspace');
    html = window.opener.joinpopupcontent(grpname, joinrequestsinfo_strb64, selectedstate);
    contentdiv.innerHTML = html;
}

function savethisrecord(saveurl, displayname, groupname, ctr){
    postdata = "displaynames=" + displayname + "&groupname=" + groupname + "&states=";
    selectid = "action_" + displayname + "_" + ctr;
    selectctrl = document.getElementById(selectid)
    selectedstate = selectctrl.value;
    postdata += selectedstate;
    csrftoken = document.frmjoingroupaction.csrfmiddlewaretoken.value;
    postdata += "&csrfmiddlewaretoken=" + csrftoken;
    alert(postdata);
    window.opener.senddataasync(postdata, 'POST', saveurl);
    return;
}


function savealljoinrequestchanges(winhndl, groupname){
}
	
