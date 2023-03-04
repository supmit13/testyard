
// This is the same function (with the exact same name + 'njs') as defined in
// network.html. This is not good design, and it is the result of a
// lack of planning as to where to put what functionality in javascript.
// I intend to mend it later on, such that there is no redundant code.
// -supriyo.

var Base64={_keyStr:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",encode:function(e){var t="";var n,r,i,s,o,u,a;var f=0;e=Base64._utf8_encode(e);while(f<e.length){n=e.charCodeAt(f++);r=e.charCodeAt(f++);i=e.charCodeAt(f++);s=n>>2;o=(n&3)<<4|r>>4;u=(r&15)<<2|i>>6;a=i&63;if(isNaN(r)){u=a=64}else if(isNaN(i)){a=64}t=t+this._keyStr.charAt(s)+this._keyStr.charAt(o)+this._keyStr.charAt(u)+this._keyStr.charAt(a)}return t},decode:function(e){var t="";var n,r,i;var s,o,u,a;var f=0;e=e.replace(/[^A-Za-z0-9\+\/\=]/g,"");while(f<e.length){s=this._keyStr.indexOf(e.charAt(f++));o=this._keyStr.indexOf(e.charAt(f++));u=this._keyStr.indexOf(e.charAt(f++));a=this._keyStr.indexOf(e.charAt(f++));n=s<<2|o>>4;r=(o&15)<<4|u>>2;i=(u&3)<<6|a;t=t+String.fromCharCode(n);if(u!=64){t=t+String.fromCharCode(r)}if(a!=64){t=t+String.fromCharCode(i)}}t=Base64._utf8_decode(t);return t},_utf8_encode:function(e){e=e.replace(/\r\n/g,"\n");var t="";for(var n=0;n<e.length;n++){var r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r)}else if(r>127&&r<2048){t+=String.fromCharCode(r>>6|192);t+=String.fromCharCode(r&63|128)}else{t+=String.fromCharCode(r>>12|224);t+=String.fromCharCode(r>>6&63|128);t+=String.fromCharCode(r&63|128)}}return t},_utf8_decode:function(e){var t="";var n=0;var r=c1=c2=0;while(n<e.length){r=e.charCodeAt(n);if(r<128){t+=String.fromCharCode(r);n++}else if(r>191&&r<224){c2=e.charCodeAt(n+1);t+=String.fromCharCode((r&31)<<6|c2&63);n+=2}else{c2=e.charCodeAt(n+1);c3=e.charCodeAt(n+2);t+=String.fromCharCode((r&15)<<12|(c2&63)<<6|c3&63);n+=3}}return t}};

function senddataasync_njs(uriencodeddata, httpmethod, targeturl){
    var xmlhttp;
    if (window.XMLHttpRequest){
        xmlhttp=new XMLHttpRequest();
    }
    else{
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function(){
        if(xmlhttp.readyState == 4 && xmlhttp.status==200){
	    alert(xmlhttp.responseText);
        }
    };
    xmlhttp.open(httpmethod, targeturl, true);
    xmlhttp.send(uriencodeddata);
}


// Operations on a child window created by 'popupjoinrequests()'.
function listselectedstatus(grpname, joinrequestsinfo_strb64){
    selectedstate = document.frmjoingroupaction.requeststate.options[document.frmjoingroupaction.requeststate.selectedIndex].value;
    contentdiv = document.getElementById('contentspace');
    html = window.opener.joinpopupcontent(grpname, joinrequestsinfo_strb64, selectedstate);
    contentdiv.innerHTML = html;
}

function savethisrecord(saveurl, displayname, groupname, ctr){
    usrresp = confirm("Commit the changes to this entry?");
    if(!usrresp){
        return(0);
    }
    postdata = "displaynames=" + displayname + "&groupname=" + groupname + "&states=";
    selectid = "action_" + displayname + "_" + ctr;
    selectctrl = document.getElementById(selectid)
    selectedstate = selectctrl.value;
    chkblock = document.getElementById('chkblock_' + (ctr).toString());
    chkremv = document.getElementById('chkremv_' + (ctr).toString());
    postdata += selectedstate;
    csrftoken = document.frmjoingroupaction.csrfmiddlewaretoken.value;
    postdata += "&csrfmiddlewaretoken=" + csrftoken;
    if(chkblock && chkblock.checked == true){
        postdata += "&chkblock_" + ctr.toString() + "=" + chkblock.value;
    }
    if(chkremv && chkremv.checked == true){
        postdata += "&chkremv_" + ctr.toString() + "=" + chkremv.value;
    }
    postdata += "&hit=single&counter=" + ctr.toString();
    //alert(postdata);
    senddataasync_njs(postdata, 'POST', saveurl);
    return;
}


function savealljoinrequestchanges(saveurl, groupname){
    usrresp = confirm("Commit all the changes on this screen?");
    if(!usrresp){
        return(0);
    }
    formelements = document.frmjoingroupaction.elements;
    displaynames_actionstatus = {};
    displaynames_block = {};
    displaynames_remove = {};
    statusdict = {};
    statusdict['open'] = 1;
    statusdict['close'] = 2;
    statusdict['refuse'] = 3;
    statusdict['accept'] = 4;
    actionpattern = new RegExp("action_");
    for(var i=0; i < formelements.length;i++){
	elementname = formelements[i].name;
        if(actionpattern.exec(elementname)){
	    elementparts = elementname.split("_");
	    displayname = elementparts[1];
	    controlobj = document.getElementById(elementname); // elementname is the same as the element's Id
	    statusvalue = controlobj.value;
	    if(!displaynames_actionstatus.hasOwnProperty(displayname)){
	    	displaynames_actionstatus[displayname] = statusdict[statusvalue];
	    }
	    else{// If the present state is lower than the state being considered, then it is replace with the new state.
		// So if a user has multiple join requests for the group and one of the status is 'accept', other status entries are ignored.
		if(displaynames_actionstatus[displayname] < statusdict[statusvalue]){
		    displaynames_actionstatus[displayname] = statusdict[statusvalue];
		}
	    }
	    blockstatus = formelements[i+1].checked;
	    removestatus = formelements[i+2].checked;
	    if(!displaynames_block.hasOwnProperty(displayname)){
		displaynames_block[displayname] = blockstatus;
	    }
	    else{ // If there are multiple entries for the same user, do a logical 'or' 
		//of the current 'blockstatus' entry with the entry stored earlier. So, if one
		// of the entries is 'true', the 'blockstatus' for that user will emerge as
		// true after all the entries for that particular user have been considered.
		displaynames_block[displayname] = displaynames_block[displayname] || blockstatus;
	    }
	    if(!displaynames_remove.hasOwnProperty(displayname)){
		displaynames_remove[displayname] = removestatus;
	    }
	    else{ // If there are multiple entries for the same user, do a logical 'or' 
		//of the current 'removestatus' entry with the entry stored earlier. So, if one
		// of the entries is 'true', the 'removestatus' for that user will emerge as
		// true after all the entries for that particular user have been considered.
		displaynames_remove[displayname] = displaynames_remove[displayname] || removestatus;
	    }
	}
    }
    dispnames_str = "";
    states_str = "";
    blocks_str = "";
    remove_str = "";
    for (dname in displaynames_actionstatus){
	dispnames_str += dname + "##";
        intactionstate = displaynames_actionstatus[dname];
	actionstatus = "open";
	if(intactionstate == 2){
	    actionstatus = "close";
	}
        else if(intactionstate == 3){
	    actionstatus = "refuse";
	}
	else if(intactionstate == 4){
	    actionstatus = "accept";
	}
	else{
	    alert("Unknown status in group join request. Setting status to 'open'");
	}
	states_str += actionstatus + "##";
   	blockstate = displaynames_block[dname];
	if(blockstate){ // If blockstate is true
	    blocks_str += "1##";
	}
	else{
	    blocks_str += "0##";
	}
	removestate = displaynames_remove[dname];
	if(removestate){ // If blockstate is true
	    remove_str += "1##";
	}
	else{
	    remove_str += "0##";
	}
    }
    postdata = "displaynames=" + dispnames_str + "&groupname=" + groupname + "&states=" + states_str + "&hit=multi&blockstates=" + blocks_str + "&removestates=" + remove_str + "&csrfmiddlewaretoken=" + document.frmjoingroupaction.csrfmiddlewaretoken.value;
    //alert(postdata);
    senddataasync_njs(postdata, 'POST', saveurl);
    return;
}


// csrfmiddlewaretoken should be part of paramsdict
function getpage(pageno, requesturl, requestmethod, paramsdict={}){
    data = "";
    for(p in paramsdict){
        if(paramsdict.hasOwnProperty(p)){
	    data += p + "=" + encodeURI(paramsdict[p]) + "&";
        }
    }
    data = data + "pageno=" + pageno.toString();
    //data = data.substring(0, data.length - 1); // chop last '&' off.
    var xmlhttp;
    if (window.XMLHttpRequest){
        xmlhttp=new XMLHttpRequest();
    }
    else{
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange = function(){
        if(xmlhttp.readyState == 4 && xmlhttp.status==200){
	    //return(xmlhttp.responseText);
            document.getElementsByTagName('html')[0].innerHTML = xmlhttp.responseText;
        }
    };
    if (requestmethod == 'post'){
        xmlhttp.open('POST', requesturl, false);
	xmlhttp.send(data);
    }
    else if(requestmethod == 'get'){
        requesturl = requesturl + "?" + data;
        xmlhttp.open('GET', requesturl, false);
        xmlhttp.send();
    }
    else{
    }
}

function joinpopupcontent2(grpname, joinrequestsinfo_strb64, state, pageno=1){
    joinrequestsinfo_str = Base64.decode(joinrequestsinfo_strb64);
    joinrequestsinfo = JSON.parse(joinrequestsinfo_str);
    showhidediv = document.getElementById("showhidejoinrequests");
    html = "";
    html += "<center><font color='#0000AA' style='font-weight:bold' size='+1'>Join Requests to Group '" + grpname + "'</font></center><br><br><br>";
    if(state == 'open' || state == '' || !state){
	html += "<center><font color='#0000AA' face='Verdana'>List Requests by Status:&nbsp;&nbsp;</font><select name='requeststate' onChange='javascript:listselectedstatus(\"" + grpname + "\", \"" + joinrequestsinfo_strb64 + "\");' class='form-control' style='width:200px;'><option value='open' selected>Open</option><option value='close'>Closed</option><option value='refuse'>Refused</option><option value='accept'>Accepted</option></select></center>";
    }
    else if(state == 'close'){
	html += "<center><font color='#0000AA' face='Verdana'>List Requests by Status:&nbsp;&nbsp;</font><select name='requeststate' onChange='javascript:listselectedstatus(\"" + grpname + "\", \"" + joinrequestsinfo_strb64 + "\");' class='form-control' style='width:200px;'><option value='open'>Open</option><option value='close' selected>Closed</option><option value='refuse'>Refused</option><option value='accept'>Accepted</option></select></center>";
    }
    else if(state == 'refuse'){
	 html += "<center><font color='#0000AA' face='Verdana'>List Requests by Status:&nbsp;&nbsp;</font><select name='requeststate' onChange='javascript:listselectedstatus(\"" + grpname + "\", \"" + joinrequestsinfo_strb64 + "\");' class='form-control' style='width:200px;'><option value='open'>Open</option><option value='close'>Closed</option><option value='refuse' selected>Refused</option><option value='accept'>Accepted</option></select></center>";
    }
    else if(state == 'accept'){
	 html += "<center><font color='#0000AA' face='Verdana'>List Requests by Status:&nbsp;&nbsp;</font><select name='requeststate' onChange='javascript:listselectedstatus(\"" + grpname + "\", \"" + joinrequestsinfo_strb64 + "\");' class='form-control' style='width:200px;'><option value='open'>Open</option><option value='close'>Closed</option><option value='refuse'>Refused</option><option value='accept' selected>Accepted</option></select></center>";
    }
    html += "<br><span style='block:left;clear:both;width:600px;padding-left:50px;word-wrap:break-all;overflow-wrap:break-word;'><font color='#550000' style='font-weight:bold'><i>Note: A 'blocked' user would not be able to post messages in the group, but would remain visible to other members. 'Blocked' users<br> would also be able to view other's posts to the group. A 'removed' user would neither be able to post messages to the group, nor would she/he be able to view messages posted by other members in the group. Also, other members would not be able to see a 'removed' user. </i></font></span><br /><br />";
    //html += "{% csrf_token %}";
    html += "<center><table border='0' cellspacing='3' cellpadding='4'>";
    html += "<tr><td align='center' colspan='6'><input type='button' name='btnsaveall' id='btnsaveall' value='Save Changes' onClick='savealljoinrequestchanges(\"skillstest/network/group/savejoinstatus/\", \"" + grpname + "\");' class='btn btn-primary'>&nbsp;&nbsp;<input type='button' name='btnclose' id='btnclose' value='Close Popup' onClick='javascript:window.close();' class='btn btn-testyard1' style='background-color:#b3b3ff;'></td></tr>";
    if(state == "open"){
	reqslist = joinrequestsinfo['open'];
	if(reqslist.length > 0){
	    html += "<tr><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Profile Image</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Full Name</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Username</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Date of Request</font></td><td nowrap align='right' colspan=2><font color='#0000AA' style='font-weight:bold' size=-1>Action</font></td><td>&nbsp;</td></tr>";
	}
	else{
	    html += "<tr><td colspan='6' align='center'><font color='#AA0000' style='font-weight:bold' size=-1>No records found</font></td></tr>"
	}
	i=0;
	for (indx in reqslist){
	    request = reqslist[indx];
	    imglink = request[3];
	    displayname = request[0];
	    fullname = request[1];
	    requestdate = request[2];
            html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td align='right'><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;'><option value='open' selected='selected'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept'>Accept</option></select></td><td nowrap align='right' colspan=2><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    indx++;
	    i++;
	}
    }
    else if(state == "close"){
	reqslist = joinrequestsinfo['close'];
	if(reqslist.length > 0){
	    html += "<tr><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Profile Image</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Full Name</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Username</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Date of Request</font></td><td nowrap align='right' colspan=2><font color='#0000AA' style='font-weight:bold' size=-1>Action</font></td><td>&nbsp;</td></tr>";
	}
	else{
	    html += "<tr><td colspan='6' align='center'><font color='#AA0000' style='font-weight:bold' size=-1>No records found</font></td></tr>"
	}
	i = 0;
	for (indx in reqslist){
	    request = reqslist[indx];
	    imglink = request[3];
	    displayname = request[0];
	    fullname = request[1];
	    requestdate = request[2];
            html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td align='right'><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;'><option value='open'>Open</option><option value='close' selected='selected'>Close</option><option value='refuse'>Refuse</option><option value='accept'>Accept</option></select></td><td nowrap align='right' colspan=2><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    i++;
	    indx++;
	}
    }
    else if(state == "refuse"){
	reqslist = joinrequestsinfo['refuse'];
	if(reqslist.length > 0){
	    html += "<tr><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Profile Image</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Full Name</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Username</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Date of Request</font></td><td nowrap align='right' colspan=2><font color='#0000AA' style='font-weight:bold' size=-1>Action</font></td><td>&nbsp;</td></tr>";
	}
	else{
	    html += "<tr><td colspan='6' align='center'><font color='#AA0000' style='font-weight:bold' size=-1>No records found</font></td></tr>"
	}
	i = 0;
	for (indx in reqslist){
	    request = reqslist[indx];
	    imglink = request[3];
	    displayname = request[0];
	    fullname = request[1];
	    requestdate = request[2];
            html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td align='right'><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse' selected='selected'>Refuse</option><option value='accept'>Accept</option></select></td><td nowrap align='right' colspan=2><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    indx++;
	    i++;
	}
    }
    else if(state == "accept"){
	reqslist = joinrequestsinfo['accept'];
	if(reqslist.length > 0){
	    html += "<tr><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Profile Image</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Full Name</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Username</font></td><td nowrap><font color='#0000AA' style='font-weight:bold' size=-1>Date of Request</font></td><td nowrap align='right' colspan=2><font color='#0000AA' style='font-weight:bold' size=-1>Action</font></td><td>&nbsp;</td></tr>";
	}
	else{
	    html += "<tr><td colspan='6' align='center'><font color='#AA0000' style='font-weight:bold' size=-1>No records found</font></td></tr>"
	}
	i = 0;
	for (indx in reqslist){
	    request = reqslist[indx];
	    imglink = request[3];
	    displayname = request[0];
	    fullname = request[1];
	    requestdate = request[2];
	    removed = request[4]
 	    blocked = request[5]
	    if(blocked == true && removed == false){
                html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td style='width:300px;white-space:nowrap;display: inline-block;' nowrap><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;padding-right:10px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept' selected='selected'>Accept</option></select></td><td style='width:200px;white-space:nowrap;display: inline-block;color:#0000AA;font-size:smaller;' nowrap> <div class='row'><div class='form-group'><input type='checkbox' name='chkblock_" + i + "' id='chkblock_" + i + "' value='blocked' class='form-control' checked>Block</div>&nbsp;|&nbsp;<div class='form-group'><input type='checkbox' name='chkremv_" + i + "' id='chkremv_" + i + "' value='removed' class='form-control'>Remove</div></div></td><td nowrap><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    }
	    else if(blocked == true && removed == true){
		html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td style='width:300px;white-space:nowrap;display: inline-block;' nowrap><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;padding-right:10px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept' selected='selected'>Accept</option></select></td><td style='width:200px;white-space:nowrap;display: inline-block;color:#0000AA;font-size:smaller;' nowrap> <div class='row'><div class='form-group'><input type='checkbox' name='chkblock_" + i + "' id='chkblock_" + i + "' value='blocked' class='form-control' checked>Block</div>&nbsp;|&nbsp;<div class='form-group'><input type='checkbox' name='chkremv_" + i + "' id='chkremv_" + i + "' value='removed' class='form-control' checked>Remove</div></div> </td><td nowrap><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    }
	    else if(blocked == false && removed == true){
		html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td style='width:300px;white-space:nowrap;display: inline-block;' nowrap><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;padding-right:10px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept' selected='selected'>Accept</option></select> </td><td style='width:200px;white-space:nowrap;display: inline-block;color:#0000AA;font-size:smaller;' nowrap><div class='row'><div class='form-group'><input type='checkbox' name='chkblock_" + i + "' id='chkblock_" + i + "' value='blocked' class='form-control'>Block</div>&nbsp;|&nbsp;<div class='form-group'><input type='checkbox' name='chkremv_" + i + "' id='chkremv_" + i + "' value='removed' class='form-control' checked>Remove </div></div></td><td nowrap><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    }
	    else if(blocked == false && removed == false){
		html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td style='width:300px;white-space:nowrap;display: inline-block;' nowrap><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;padding-right:10px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept' selected='selected'>Accept</option></select> </td><td style='width:200px;white-space:nowrap;display: inline-block;color:#0000AA;font-size:smaller;' nowrap><div class='row'><div class='form-group'><input type='checkbox' name='chkblock_" + i + "' id='chkblock_" + i + "' value='blocked' class='form-control'>Block</div>&nbsp;|&nbsp;<div class='form-group'><input type='checkbox' name='chkremv_" + i + "' id='chkremv_" + i + "' value='removed' class='form-control'>Remove</div></div></td><td nowrap><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    }
	    else if(blocked == -1 || removed == -1){
		html += "<tr><td align='center'><img src='" + imglink + "' height='40px' width='40px'></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + fullname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + displayname + "</font></td><td nowrap><font face='Verdana' color='#0000AA' size=-1>" + requestdate + "</font></td><td style='width:300px;white-space:nowrap;display: inline-block;' nowrap><select name='action_" + displayname + "_" + i.toString() + "' id='action_" + displayname + "_" + i.toString() + "' class='form-control' style='width:110px;padding-right:10px;'><option value='open'>Open</option><option value='close'>Close</option><option value='refuse'>Refuse</option><option value='accept' selected='selected'>Accept</option></select> </td><td style='width:200px;white-space:nowrap;display: inline-block;color:#0000AA;font-size:smaller;' nowrap><div class='row'><div class='form-group'><input type='checkbox' name='chkblock_" + i + "' id='chkblock_" + i + "' value='blocked' class='form-control' disabled title='You cannot block the owner of the group'>Block </div>&nbsp;|&nbsp;<div class='form-group'><input type='checkbox' name='chkremv_" + i + "' id='chkremv_" + i + "' value='removed' class='form-control' disabled title='You cannot remove the owner of the group'>Remove </div></div></td><td nowrap><input type='button' name='btnsaverec_" + displayname + "' id='btnsaverec_" + displayname + "' value='Save' onClick='javascript:savethisrecord(\"skillstest/network/group/savejoinstatus/\", \"" + displayname + "\", \"" + grpname + "\", \"" + i.toString() + "\");' class='btn btn-primary' style='width:110px;'></td></tr>";
	    }
	    indx++;
	    i++;
	}
    }
    html += "<tr><td align='center' colspan='6'>";
    nextpage = pageno + 1;
    prevpage = pageno - 1;
    if(prevpage > 0){
        html += "<a href='#/' onclick='javascript:getmorejoinrequests(\"" + grpname + "\", \"" + state + "\"," + prevpage.toString() + ");'>< Prev</a>|";
    }
    html += "<a href='#/' onclick='javascript:getmorejoinrequests(\"" + grpname + "\", \"" + state + "\"," + nextpage.toString() + ");'>Next ></a>";
    html += "</td></tr>";
    html += "<tr><td align='center' colspan='6'><input type='button' name='btnsaveall' id='btnsaveall' value='Save Changes' onClick='savealljoinrequestchanges(\"skillstest/network/group/savejoinstatus/\", \"" + grpname + "\");' class='btn btn-primary'>&nbsp;&nbsp;<input type='button' name='btnclose' id='btnclose' value='Close Popup' onClick='javascript:window.close();' class='btn btn-testyard1' style='background-color:#b3b3ff;'></td></tr>";
    html += "</table></center>";
    return (html);
}

