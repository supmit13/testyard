// Detect browser type
var isOpera = (!!window.opr && !!opr.addons) || !!window.opera || navigator.userAgent.indexOf(' OPR/') >= 0;
var isFirefox = typeof InstallTrigger !== 'undefined';
var isSafari = /constructor/i.test(window.HTMLElement) || (function (p) { return p.toString() === "[object SafariRemoteNotification]"; })(!window['safari'] || (typeof safari !== 'undefined' && safari.pushNotification));
var isIE = /*@cc_on!@*/false || !!document.documentMode;
var isEdge = !isIE && !!window.StyleMedia;
var isChrome = !!window.chrome && !!window.chrome.webstore;
var isBlink = (isChrome || isOpera) && !!window.CSS;

try {
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  var recognition = new SpeechRecognition();
}
catch(e) {
  //console.error(e);
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
if(!isFirefox && !isOpera){
    recognition.continuous = true;
    recognition.interimResults = true;
}
alert("Outside reco");
// This block is called every time the Speech APi captures a line. 
if(recognition){
recognition.onresult = function(event){
  // event is a SpeechRecognitionEvent object.
  // It holds all the lines we have captured so far. 
  // We only need the current line.
  var current = event.resultIndex;
  alert("In reco");
  // Get a transcript of what was said.
  var transcript += event.results[current][0].transcript;
  alert("Transcript: " + transcript);
  // Handle Android bug
  var mobileRepeatBug = (current == 1 && transcript == event.results[0][0].transcript);

  if(!mobileRepeatBug) {
    challengecontent = transcript;
    alert(challengecontent);
    //challengetextarea.val(challengecontent);
    $("textarea#statement").val(challengecontent);
    //alert("challenge content = " + challengecontent);
  }
  
};
}

recognition.onstart = function() { 
  alert("Voice recognition activated. Try speaking into the microphone");
  instructions.text('Voice recognition activated. Try speaking into the microphone.');
};

recognition.onspeechend = function() {
  instructions.text('You were quiet for a while so voice recognition turned itself off.');
  transcript = "";
  challengecontent = "";
};

recognition.onerror = function(event) {
  if(event.error == 'no-speech') {
    instructions.text('No speech was detected. Try again.');  
  };
};

function makeLink() {
  let blob = new Blob(chunks, {type: media.type });
  let fd = new FormData;
  fd.append("audioRecording", blob);
  let request = new XMLHttpRequest();
  request.open("POST", "skillstest/test/listenaudio/", true);
  request.onload = function() {
    // stream audio to server using javascript from microphone
  }
  request.onerror = function() {
   // handle error
  }
  request.send(fd);
}

/*-----------------------------
      App buttons and input 
------------------------------*/


function start_recording(){
  if (challengecontent.length) {
    challengecontent += ' ';
  }
  //alert(isChrome);
  if(!isChrome && !isFirefox){
    //alert("Cannot start voice recognition. Please note that as of now, this feature is available only on Google Chrome browser. It looks like you are using some other browser, so you would need to type down the challenges/questions. This inconvenience is regretted.");
    //recognition.start();
    makeLink();
  }
  else{
    //alert("Starting voice recognition.");
    recognition.start();
  }

}


function pause_recording(){
  recognition.stop();
  instructions.text('Voice recognition paused.');
}


// Sync the text inside the text area with the challengecontent variable.
challengetextarea.on('input', function() {
  challengecontent = $(this).val();
  alert(challengecontent);
})


/* For Firefox :
media.useAudioChannelAPI;true
media.webspeech.recognition.enable;true
media.webspeech.recognition.force_enable;true
media.webspeech.synth.enabled;true
media.webspeech.synth.force_global_queue;true
media.webspeech.test.enable;true
media.webspeech.test.fake_fsm_events;true
media.webspeech.test.fake_recognition_service;true
media.getusermedia.browser.enabled;true
media.getusermedia.audiocapture.enabled;true
dom.streams.enabled;true
media.getusermedia.channels;1
*/


