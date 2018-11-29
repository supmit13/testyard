
	  MathJax.Hub.Config({ 
	    extensions: ['tex2jax.js'], 
	    jax: ['input/TeX','output/HTML-CSS'], 
	    tex2jax: {inlineMath: [['\[','\]'],['\\(','\\)']]} 
	  }); 
	</script> 
        <script src='static/mathlib/math.min.js'></script> 
        <script type='text/javascript' async src='static/MathJax/MathJax.js?config=TeX-MML-AM_CHTML'> 
        </script> 
        <script> 
 
        function displayMathExprEvalRespView(){ 
            //alert("HELLO"); 
	    mathexprcndtrespdiv = document.getElementById('mathexprcdusvwcndtresp'); 
	    txtContents = mathexprcndtrespdiv.innerHTML; 
	    MathJax.Hub.Queue(['Typeset', MathJax.Hub, mathexprcndtrespdiv]); 
 
            mathexprcndtchlngdiv = document.getElementById('mathexprcdusvwcndtch'); 
	    txtContents = mathexprcndtchlngdiv.innerHTML;  
	    MathJax.Hub.Queue(['Typeset', MathJax.Hub, mathexprcndtchlngdiv]); 
	} 
 


