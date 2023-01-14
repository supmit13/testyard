
// This is the same function (with the exact same name + 'njs') as defined in
// network.html. This is not good design, and it is the result of a
// lack of planning as to where to put what functionality in javascript.
// I intend to mend it later on, such that there is no redundant code.
// -supriyo.
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

