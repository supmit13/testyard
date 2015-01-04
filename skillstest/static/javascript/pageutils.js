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

