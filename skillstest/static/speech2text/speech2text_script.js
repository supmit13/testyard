try {
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  var recognition = new SpeechRecognition();
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

// This block is called every time the Speech APi captures a line. 
recognition.onresult = function(event){
  // event is a SpeechRecognitionEvent object.
  // It holds all the lines we have captured so far. 
  // We only need the current line.
  var current = event.resultIndex;

  // Get a transcript of what was said.
  var transcript = event.results[current][0].transcript;
  //alert("Transcript: " + transcript);
  // Handle Android bug
  var mobileRepeatBug = (current == 1 && transcript == event.results[0][0].transcript);

  if(!mobileRepeatBug) {
    challengecontent += transcript;
    //challengetextarea.val(challengecontent);
    $("textarea#statement").val(challengecontent);
    //alert("challenge content = " + challengecontent);
  }
};

recognition.onstart = function() { 
  alert("Voice recognition activated. Try speaking into the microphone");
  instructions.text('Voice recognition activated. Try speaking into the microphone.');
};

recognition.onspeechend = function() {
  instructions.text('You were quiet for a while so voice recognition turned itself off.');
};

recognition.onerror = function(event) {
  if(event.error == 'no-speech') {
    instructions.text('No speech was detected. Try again.');  
  };
};



/*-----------------------------
      App buttons and input 
------------------------------*/


function start_recording(){
  if (challengecontent.length) {
    challengecontent += ' ';
  }
  alert("Starting voice recognition");
  recognition.start();
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





