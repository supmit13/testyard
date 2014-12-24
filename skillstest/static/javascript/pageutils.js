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
    return String(e).search (valid_name_pattern) != -1;
}

function validate_phonenum(p){
    var filter = /^\d+$/;
    return String(p).search (filter) != -1;
}




