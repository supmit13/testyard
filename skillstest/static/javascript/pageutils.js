// Javascript content for skillstest - various page manipulation utilities.
// - Supriyo.


String.prototype.trim = function() {
    a = this.replace(/^\s+/, '');
    return a.replace(/\s+$/, '');
};

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
    thediv.style.display = "";
    thediv.innerHTML = "<form name='profimageuploadform' action='" + viewurl + "' enctype='multipart/form-data' method='POST'><center><input type='file' name='profpic' value=''><input type='button' name='btnupload' value='Go' onClick='javascript:uploadimage();'></center><input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "'></form>";
  }
  else{
    thediv.style.display = "none";
    thediv.innerHTML = '';
  }
  return false;
}


// This has to make an xmlhttp POST request.
function uploadimage(){
  var targeturl = document.profimageuploadform.action;
  var profpic = document.profimageuploadform.profpic.value;
  var csrftoken = document.profimageuploadform.csrfmiddlewaretoken.value;
  var postdata = "profpic=" + profpic + "&csrfmiddlewaretoken=" + csrftoken;
  //alert(postdata);
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
    }
    else{
      alert("Error uploading image: " + xmlhttp.responseText);
    }
    document.getElementById('uploadbox').style.display = 'none';
    document.getElementById('uploadbox').innerHTML = '';
  }
  };
  xmlhttp.open("POST",targeturl,true); // ajax call (async=true)
  xmlhttp.setRequestHeader("Content-type","application/x-www-form-urlencoded");
  xmlhttp.send(postdata);
  // Display the rotating activity small icon
  document.getElementById('uploadbox').style.display = '';
  document.getElementById('uploadbox').innerHTML += "<br /><img src='static/images/loading_small.gif'>";
}


