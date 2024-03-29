// Javascript content for skillstest - various page manipulation utilities.
// - Supriyo.


String.prototype.trim = function() {
    a = this.replace(/^\s+/, '');
    return a.replace(/\s+$/, '');
};

// Serialize object/dictionary to urlencoded query string
function serialize(obj) {
  var str = [];
  for(var p in obj)
     str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
  return str.join("&");
}

// Function to validate user inputs
function validate_user_input(formname){
    return true;
}

// Function to submit login form details.
function process_login(){
    if (!validate_user_input('loginform')){
	return false;
    }
    else{
	document.loginform.submit();
    }
}

function validate_email(e) {
    var filter = /^\s*[\w\-\+_]+(\.[\w\-\+_]+)*\@[\w\-\+_]+\.[\w\-\+_]+(\.[\w\-\+_]+)*\s*$/;
    return String(e).search (filter) != -1;
}


function check_name(e){
    var valid_name_pattern = /^[a-zA-Z]+$/;
    return String(e).search(valid_name_pattern) != -1;
}

function validate_phonenum(p){
    var filter = /^\d+$/;
    return String(p).search (filter) != -1;
}

// Function to check the strength of the password. Returns
// an integer between 1 and 5 with 5 being the strongest and
// 1 being the weakest. 0 denotes the absence of any character 
// (empty string '').
function check_passwd_strength(passwd){
  if(passwd.trim() == ""){
    return(0);
  }
  var strength = 0;
  if(passwd.length > 6){
    strength = strength + 1;
  }
  var charlist = [];
  for(var i=0;i < passwd.length; i++){
    charlist[i] = passwd.substring(i, 1);
  }
  var contains_digits = 0;
  var contains_special_char = 0;
  var contains_lowercase = 0;
  var contains_uppercase = 0;
  var spchars = "~`!#$%^&*+=-[]\\\';,/{}|\":<>?";
  for(var i=0;i < charlist.length; i++){
    if(parseInt(charlist[i])){
      strength +=  1;
      continue;
    }
    if(!parseInt(charlist[i]) && charlist[i] == charlist[i].toUpperCase()){ // contains lowercase character
      strength += 1;
      continue;
    }
    if(!parseInt(charlist[i]) && charlist[i] == charlist[i].toLowerCase()){ // contains uppercase character
      strength += 1;
      continue;
    }
    if(spchars.indexOf(charlist[i])){ // contains special character
      strength += 1;
      continue;
    }
  }
  return strength; 
}


function generateuuid(){
  var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
  });
  return(uuid);
}


// Function to display the semi-transparent profile image upload form screen.
function uploader(viewurl, csrftoken){
  var thediv=document.getElementById('uploadbox');
  if(thediv.style.display == "none"){
    thediv.style = "opacity:1.0;display:;background-color:#ccffff;height:125px;";
    thediv.innerHTML = "<form name='profimageuploadform' action='" + viewurl + "' enctype='multipart/form-data' method='POST'><div class='row' style='text-align:center;display:flex;position:relative;top:20px;left:40px;border-radius:3px;border-style:groove;border-color:#aaaacc;width:450px;padding:5px;'><input type='file' name='profpic' value='' class='form-control' style='width:200px;'>&nbsp;&nbsp;<input type='button' name='btnupload' value='Go' onClick='javascript:uploadimage();' class='btn btn-primary' style='width:100px;'>&nbsp;&nbsp;<input type='button' name='btnclose' value='Close' onClick='javascript:closeimgscreen();' class='btn btn-testyard1' style='width:100px;'></div><input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "'></form>";
  }
  else{
    thediv.style.display = "none";
    thediv.innerHTML = '';
  }
  return false;
}


function closeimgscreen(){
  var thediv=document.getElementById('uploadbox');
  thediv.innerHTML = "";
  thediv.style.display = "none";
}


// This has to make an xmlhttp POST request.
function uploadimage(){
  var targeturl = document.profimageuploadform.action;
  var postdata = new FormData(document.forms.namedItem("profimageuploadform"));
  var xmlhttp;
  if (window.XMLHttpRequest){
    xmlhttp=new XMLHttpRequest();
  }
  else{
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  // Register the handler
  xmlhttp.onreadystatechange = function(){
  if(xmlhttp.readyState == 4 && xmlhttp.status==200){
    if(xmlhttp.responseText == 'success'){
      alert("Image was uploaded successfully");
      window.location.href = window.location.href; // refresh the window.
    }
    else{
      alert("Error uploading image: " + xmlhttp.responseText);
    }
    document.getElementById('uploadbox').style.display = 'none';
    document.getElementById('uploadbox').innerHTML = '';
  }
  else if(xmlhttp.readyState == 3 && xmlhttp.status==413){
    alert("The uploaded image is larger than the allowed size (5 MB). Please select a smaller image to upload.");
    document.getElementById('uploadbox').style.display = 'none';
    document.getElementById('uploadbox').innerHTML = '';
    return(0);
  }
  };
  xmlhttp.open("POST",targeturl,true); // ajax call (async=true)
  xmlhttp.send(postdata);
  // Display the rotating activity small icon
  document.getElementById('uploadbox').style.display = '';
  document.getElementById('uploadbox').innerHTML += "<br/><img src='static/images/loading_small.gif'>";
}

function checknumeric(field){
  fieldval = field.value.trim();
  if(isNaN(+fieldval) || !isFinite(fieldval)){
    alert(field.name + " field cannot be non-numeric");
    field.value = "";
    field.focus();
    return false;
  }
  return true;
}

function showworking(){
  var workstatusdiv = document.getElementById('workstatus');
  workstatusdiv.style.display = "";
  workstatusdiv.innerHTML = "<img src='static/images/loading_small.gif'>";
}

function hideworking(){
  var workstatusdiv = document.getElementById('workstatus');
  workstatusdiv.innerHTML = "";
  workstatusdiv.style.display = "none";
}

function showerror(msg){
  var workstatusdiv = document.getElementById('workstatus');
  workstatusdiv.style.display = "";
  workstatusdiv.innerHTML = msg;
}


function checkbrowser(){
    var nVer = navigator.appVersion;
    var nAgt = navigator.userAgent;
    var browserName  = navigator.appName;
    var fullVersion  = ''+parseFloat(navigator.appVersion); 
    var majorVersion = parseInt(navigator.appVersion,10);
    var nameOffset,verOffset,ix;

    minsupportedversiondict = {};
    minsupportedversiondict['Chrome'] = 26;
    minsupportedversiondict['Firefox'] = 37;
    minsupportedversiondict['Microsoft Internet Explorer'] = 37;
    minsupportedversiondict['Opera'] = 29;
    minsupportedversiondict['Safari'] = 37;

    // In Opera 15+, the true version is after "OPR/" 
    if ((verOffset=nAgt.indexOf("OPR/"))!=-1) {
	browserName = "Opera";
	fullVersion = nAgt.substring(verOffset+4);
    }
    // In older Opera, the true version is after "Opera" or after "Version"
    else if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
        browserName = "Opera";
        fullVersion = nAgt.substring(verOffset+6);
    	if ((verOffset=nAgt.indexOf("Version"))!=-1){
            fullVersion = nAgt.substring(verOffset+8);
	}
    }
    // In MSIE, the true version is after "MSIE" in userAgent
    else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
        browserName = "Microsoft Internet Explorer";
        fullVersion = nAgt.substring(verOffset+5);
    }
    // In Chrome, the true version is after "Chrome" 
    else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
 	browserName = "Chrome";
 	fullVersion = nAgt.substring(verOffset+7);
    }
    // In Safari, the true version is after "Safari" or after "Version" 
    else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
 	browserName = "Safari";
 	fullVersion = nAgt.substring(verOffset+7);
 	if ((verOffset=nAgt.indexOf("Version"))!=-1){
   	     fullVersion = nAgt.substring(verOffset+8);
	}
    }
    // In Firefox, the true version is after "Firefox" 
    else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
 	browserName = "Firefox";
 	fullVersion = nAgt.substring(verOffset+8);
    }
    // In most other browsers, "name/version" is at the end of userAgent 
    else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < (verOffset=nAgt.lastIndexOf('/')) ){
        browserName = nAgt.substring(nameOffset,verOffset);
 	fullVersion = nAgt.substring(verOffset+1);
 	if (browserName.toLowerCase()==browserName.toUpperCase()) {
  	    browserName = navigator.appName;
 	}
    }
    // trim the fullVersion string at semicolon/space if present
    if ((ix=fullVersion.indexOf(";"))!=-1){
   	fullVersion=fullVersion.substring(0,ix);
    }
    if ((ix=fullVersion.indexOf(" "))!=-1){
   	fullVersion=fullVersion.substring(0,ix);
    }
    majorVersion = parseInt(''+fullVersion,10);
    if (isNaN(majorVersion)) {
 	fullVersion  = ''+parseFloat(navigator.appVersion); 
 	majorVersion = parseInt(navigator.appVersion,10);
    }
    //alert(majorVersion);
    if(browserName != "Microsoft Internet Explorer" && browserName != "Chrome" && browserName != "Firefox" && browserName != "Safari" && browserName != "Opera"){
	document.write("<center><font color='#AA0000' style='font-weight:bold;'>The browser you are using is not supported by this application. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of one of the following browsers: Mozilla Firefox, Microsoft Internet Explorer, Opera, Google Chrome, Safari.</font></center>");
	return (false);
    }
    if(browserName == "Chrome" && majorVersion < minsupportedversiondict[browserName]){
	document.write("<center><font color='#AA0000' style='font-weight:bold;'>The version of Chrome you are using is not supported by this website. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of Chrome.</font></center>");
	return(false);
    }
    else if(browserName == "Firefox" && majorVersion < minsupportedversiondict[browserName]){
        document.write("<center><font color='#AA0000' style='font-weight:bold;'>The version of Firefox you are using is not supported by this website. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of Firefox.</font></center>");
	return(false);
    }
    else if(browserName == "Microsoft Internet Explorer" && majorVersion < minsupportedversiondict[browserName]){
	document.write("<center><font color='#AA0000' style='font-weight:bold;'>The version of Internet Explorer you are using is not supported by this website. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of Internet Explorer.</font></center>");
	return(false);
    }
    else if(browserName == "Opera" && majorVersion < minsupportedversiondict[browserName]){
	document.write("<center><font color='#AA0000' style='font-weight:bold;'>The version of Opera you are using is not supported by this website. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of Opera.</font></center>");
	return(false);
    }
    else if(browserName == "Safari" && majorVersion < minsupportedversiondict[browserName]){
	document.write("<center><font color='#AA0000' style='font-weight:bold;'>The version of Safari you are using is not supported by this website. Hence, some functions available on this website might not work as expected.<br />To surpass this issue, please download the latest version of Safari.</font></center>");
	return(false);
    }
    return (true);
}

// Utility routine, mostly used for dumping large amount of data to a file.
function WriteFile(textcontent){
    var fso  = new ActiveXObject("Scripting.FileSystemObject"); 
    var fh = fso.CreateTextFile("/home/supriyo/work/testyard/dump.txt", true); 
    fh.WriteLine(textcontent); 
    fh.Close(); 
}


// Function to execute <script> tags in innerHTML (in order make tinymce.init() work).
function stripandexecutescript(text){
    var scripts = '';
    var cleaned = text.replace(/<script[^>]*>([\s\S]*?)<\/script>/gi, function(){
        scripts += arguments[1] + '\n';
        return '';
    });
    if (window.execScript){
        window.execScript(scripts);
    } 
    else {
        var head = document.getElementsByTagName('head')[0];
        var scriptElement = document.createElement('script');
        scriptElement.setAttribute('type', 'text/javascript');
        scriptElement.innerText = scripts;
        head.appendChild(scriptElement);
	//alert(scripts);
        head.removeChild(scriptElement);
    }
    return cleaned;
}


function decodejwt(jwt){
  tokens = jwt.split(".");
  decodedlist = new Array();
  for(var i=0;i < tokens.length;i++){
    //console.log(atob(tokens[i]));
    try{
      decodedcontent = JSON.parse(atob(tokens[i]));
      decodedlist.push(decodedcontent);
    }
    catch(err){
      console.log(err.message);
    }
  }
  return (decodedlist);
}


function google_signin_callback(response){
  responsepayload = decodejwt(response.credential);
  var targeturl = "/skillstest/googleinfo/";
  let signindiv = document.getElementById('dummysignindiv');
  signindiv.style.display = "";
  signinform = document.createElement("form");
  signinform.method = "POST";
  signinform.action = targeturl;
  emailcontainer = document.createElement("input");
  emailcontainer.type = "hidden";
  emailcontainer.name = "emailid";
  firstnamecontainer = document.createElement("input");
  firstnamecontainer.type = "hidden";
  firstnamecontainer.name = "firstname";
  lastnamecontainer = document.createElement("input");
  lastnamecontainer.type = "hidden";
  lastnamecontainer.name = "lastname";
  googleidcontainer = document.createElement("input");
  googleidcontainer.type = "hidden";
  googleidcontainer.name = "googleid";
  gendercontainer = document.createElement("input");
  gendercontainer.type = "hidden";
  gendercontainer.name = "gender";
  profpiccontainer = document.createElement("input");
  profpiccontainer.type = "hidden";
  profpiccontainer.name = "profpic";
  csrfcontainer = document.createElement("input");
  csrfcontainer.type = "hidden";
  csrfcontainer.name = "csrfmiddlewaretoken";
  csrf = document.loginform.csrfmiddlewaretoken.value;
  pluspattern = new RegExp("\\+", "g");
  specialcharspattern = new RegExp("[\\.,\\-\\'\\:\\/]+", "g");
  for(j=0;j < responsepayload.length;j++){
    datadict = responsepayload[j];
    if(datadict.hasOwnProperty("email")){ // Check if the dictionary has a key named 'email'
      if(datadict['email'] != null){
        emailcontainer.value = datadict['email'];
      }
      else{
        emailcontainer.value = "";
      }
      if(datadict['given_name'] != null){
        firstname = datadict['given_name'];
      }
      else{
        firstname = "";
      }
      if(datadict['family_name'] != null){
        lastname = datadict['family_name'];
      }
      else{
        lastname = "";
      }
      if(datadict['name'] != null){
        username = datadict['name'];
      }
      else{
        username = "";
      }
      firstname = firstname.replace(pluspattern, " ");
      lastname = lastname.replace(pluspattern, " ");
      username = username.replace(pluspattern, "");
      firstname = firstname.replace(specialcharspattern, "");
      lastname = lastname.replace(specialcharspattern, "");
      username = username.replace(specialcharspattern, "");
      //alert(username);
      firstnamecontainer.value = firstname;
      lastnamecontainer.value = lastname;
      googleidcontainer.value = username;
      gendercontainer.value = "unknown";
      if(datadict['picture'] != null){
        profpiccontainer.value = datadict['picture'];
      }
      else{
        profpiccontainer.value = "";
      }
      csrfcontainer.value = csrf;
      signinform.appendChild(emailcontainer);
      signinform.appendChild(firstnamecontainer);
      signinform.appendChild(lastnamecontainer);
      signinform.appendChild(googleidcontainer);
      signinform.appendChild(gendercontainer);
      signinform.appendChild(profpiccontainer);
      signinform.appendChild(csrfcontainer);
      signindiv.appendChild(signinform);
      //alert(signinform);
      signinform.submit();
      break;
    }
  }
}


function signinwithlinkedin(clientid, redirecturi){
  //let randomnonce = document.getElementById('lirandomnonce').value; 
  let randomnonce = document.loginform.csrfmiddlewaretoken.value; // Assuming that we are being called from the login page (login.html).
  let authurl = "https://www.linkedin.com/oauth/v2/authorization";
  let datadict = {'response_type' : 'code', 'client_id' : clientid, 'redirect_uri' : redirecturi, 'state' : randomnonce, 'scope' : 'r_liteprofile r_emailaddress'};
  let qs = serialize(datadict);
  authurlqs = authurl + "?" + qs;
  liwin = window.open(authurlqs, "liauthwindow", "width=640, height=480, location=no, status=yes, menubar=no, scrollbars=yes,toolbar=no, titlebar=yes, resizable=false");
}

function emailty(){
  let targeturl = "https://testyard.in/skillstest/contactty/";
  var postdata = new FormData(document.forms.namedItem("frmcontactty"));
  var xmlhttp;
  if (window.XMLHttpRequest){
    xmlhttp=new XMLHttpRequest();
  }
  else{
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  // Register the handler
  xmlhttp.onreadystatechange = function(){
    if(xmlhttp.readyState == 4 && xmlhttp.status==200){
      alert(xmlhttp.responseText);
      window.location.href = window.location.href;
    }
  }
  xmlhttp.open("POST",targeturl,true); // ajax call (async=true)
  xmlhttp.send(postdata);
  document.getElementById('btnsend').disabled=true;
  document.getElementById('sendingimgp').style.display = "";
}


// Forgot password handler
function forgotpassword(){
  uname = document.loginform.username.value;
  let targeturl = "https://testyard.in/skillstest/forgotpasswdemail/";
  var postdata = "uname=" + uname + "&csrfmiddlewaretoken=" + document.loginform.csrfmiddlewaretoken.value;
  var xmlhttp;
  if (window.XMLHttpRequest){
    xmlhttp=new XMLHttpRequest();
  }
  else{
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  // Register the handler
  xmlhttp.onreadystatechange = function(){
    if(xmlhttp.readyState == 4 && xmlhttp.status==200){
      notifyparatag = document.getElementById('emailnotification');
      if(xmlhttp.responseText == "sent"){
        notifyparatag.innerHTML = "An email has been sent to your email address. Please follow the instructions therein.";
        notifyparatag.style = "display:;font-size:small;color:#0000aa;";
      }
      else{
        notifyparatag.innerHTML = "Failed to send email to your email address. Please contact support at support@testyard.in";
        notifyparatag.style = "color:#aa0000;font-size:small;";
      }
    }
  }
  xmlhttp.open("POST",targeturl,true); // ajax call (async=true)
  xmlhttp.send(postdata);
}


function resetpassword(){
  newpassword = document.frmresetpasswd.newpasswd.value;
  repeatnewpassword = document.frmresetpasswd.repeatnewpasswd.value;
  trxkeyval = document.frmresetpasswd.trxkey.value;
  targeturl = document.frmresetpasswd.action;
  if(newpassword.trim() == "" || repeatnewpassword.trim() == ""){
    alert("New password or Confirm password should not be empty");
    document.frmresetpasswd.newpasswd.focus();
    return (false);
  }
  if(newpassword != repeatnewpassword){
    alert("The passwords do not match!");
    return (false);
  }
  var postdata = "newpasswd=" + encodeURIComponent(newpassword) + "&repeatnewpasswd=" + encodeURIComponent(repeatnewpassword) + "&csrfmiddlewaretoken=" + document.frmresetpasswd.csrfmiddlewaretoken.value + "&trxkey=" + trxkeyval;
  var xmlhttp;
  if (window.XMLHttpRequest){
    xmlhttp=new XMLHttpRequest();
  }
  else{
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  // Register the handler
  xmlhttp.onreadystatechange = function(){
    if(xmlhttp.readyState == 4 && xmlhttp.status==200){
      alert(xmlhttp.responseText);
      window.close();
    }
  }
  xmlhttp.open("POST",targeturl,true); // ajax call (async=true)
  xmlhttp.send(postdata);
}

// Function to enable sending an emailer to notify a user about a feature update.
function featureupdate(featureurl){

}


