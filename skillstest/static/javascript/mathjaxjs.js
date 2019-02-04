
	
        function displayMathExprEvalRespView(countresp){ 
	    MathJax.Hub.Config({
	        extensions: ["tex2jax.js"],
	        jax: ["input/TeX","output/HTML-CSS"],
		showProcessingMessages: true,
	        tex2jax: {inlineMath: [['$','$'], ["\[","\]"],["\\(","\\)"]]}
	    });

            for(var i=1; i < countresp; i++){
	        var mathexprcndtrespdiv = document.getElementById("mathexprcdusvwcndtresp_" + i);
	        var mathrespcontent = mathexprcndtrespdiv.innerHTML;
	        mathrespcontent = mathrespcontent.replace(/\\?\[\s*/, "");
	        mathrespcontent = mathrespcontent.replace(/\\?\]\s*/, "");
	        mathexprcndtrespdiv.innerHTML = mathrespcontent;
	        //alert(mathexprcndtrespdiv.innerHTML);
	        var mathexprcndtchlngdiv = document.getElementById("mathexprcdusvwcndtch_" + i);
	        var mathexprcontent = mathexprcndtchlngdiv.innerHTML;
	        mathexprcontent = mathexprcontent.replace(/\\?\[\s*/, "");
	        mathexprcontent = mathexprcontent.replace(/\\?\]\s*/, "");
	        mathexprcndtchlngdiv.innerHTML = mathexprcontent;
	        try{
		    MathJax.Hub.Queue(['Typeset', MathJax.Hub, mathexprcndtchlngdiv]);
		    MathJax.Hub.Queue(['Typeset', MathJax.Hub, mathexprcndtrespdiv]);
	        }
	        catch(err){
		    alert(err.message);
	        }
            }
	    //alert("Number = " + countresp);
	    //alert(MathJax.Hub.Queue);
	} 
 
