// Detect browser type
//var isOpera = (!!window.opr && !!opr.addons) || !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
//var isFirefox = typeof InstallTrigger !== 'undefined';
//var isSafari = /constructor/i.test(window.HTMLElement) || (function (p) { return p.toString() === "[object SafariRemoteNotification]"; })(!window['safari'] || (typeof safari !== 'undefined' && safari.pushNotification));
//var isIE = /*@cc_on!@*/false || !!document.documentMode;
//var isEdge = !isIE && !!window.StyleMedia;
//var isChrome = !!window.chrome && !!window.chrome.webstore;
//var isBlink = (isChrome || isOpera) && !!window.CSS;
// https://stackoverflow.com/questions/39784986/speechrecognition-is-not-working-in-firefox
try {
  const tySpeechRecognition = window.speechRecognition || window.webkitSpeechRecognition;
  const recognition = new tySpeechRecognition();
  //console.log("HIIIIIIII");
}
catch(e) {
  console.error(e);
  $('.no-browser-support').show();
  $('.app').hide();
}


var challengetextarea = $('#statement');
var instructions = $('#recording-instructions');

var challengecontent = '';

/*-----------------------------
      Voice Recognition 
------------------------------*/

// If false, the recording will stop after a few seconds of silence.
// When true, the silence period is longer (about 15 seconds),
// allowing us to keep recording even when the user pauses. 

recognition.continuous = true;
//recognition.interimResults = true;

// This block is called every time the Speech APi captures a line. 

recognition.onresult = function(event){
  // event is a SpeechRecognitionEvent object.
  // It holds all the lines we have captured so far. 
  // We only need the current line.
  var current = event.resultIndex;
  console.log(current);
  // Get a transcript of what was said.
  var transcript = event.results[current][0].transcript;
  // Handle Android bug
  var mobileRepeatBug = (current == 1 && transcript == event.results[0][0].transcript);

  if(!mobileRepeatBug) {
    challengecontent += transcript;
    //challengetextarea.val(challengecontent);
    $("textarea#statement").val(challengecontent);
  }
  else{
    //alert(challengecontent);
  }
};


recognition.onstart = function() { 
  alert("Voice recognition activated. Try speaking into the microphone");
  instructions.text('Voice recognition activated. Try speaking into the microphone.');
  //console.log("Voice recognition activated. Try speaking into the microphone");
};

recognition.onspeechend = function() {
  instructions.text('You were quiet for a while so voice recognition turned itself off.');
  transcript = "";
  challengecontent = "";
  recognition.stop();
};

recognition.onerror = function(event) {
  if(event.error == 'no-speech') {
    instructions.text('No speech was detected. Try again.');
    console.log('No speech was detected. Try again.');
  };
};



/*-----------------------------
      App buttons and input 
------------------------------*/


function start_recording(){
  if (challengecontent.length) {
    challengecontent += ' ';
  }
  //alert(isChrome);
  //if(!isChrome && !isFirefox){
    //alert("Cannot start voice recognition. Please note that as of now, this feature is available only on Google Chrome browser. It looks like you are using some other browser, so you would need to type down the challenges/questions. This inconvenience is regretted.");
    //recognition.start();
    //makeLink();
 // }
  //else{
    recognition.start();
    console.log("Starting voice recognition.");
  //}

}


function pause_recording(){
  recognition.stop();
  instructions.text('Voice recognition paused.');
}


// Sync the text inside the text area with the challengecontent variable.
challengetextarea.on('input', function() {
  challengecontent = $(this).val();
  //alert(challengecontent);
})




