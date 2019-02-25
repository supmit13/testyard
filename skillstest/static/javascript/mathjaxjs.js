// Javascript for displaying mathjax symbols in questions and answers on evaluation page. -- Supriyo.

function displayMathExprEvalRespView(countresp){ 
    //alert(countresp);
    //alert(typeof MathJax.Hub); // Works! Prints 'object'.
    for(i=1; i < countresp; i++){
        mathexprcndtrespdiv = document.getElementById("mathexprcdusvwcndtresp_" + i.toString());
        mathrespcontent = mathexprcndtrespdiv.innerHTML;
        mathrespcontent = mathrespcontent.replace(/^\\?\[\s*/, "");
        mathrespcontent = mathrespcontent.replace(/\\?\]\s*$/, "");
        mathexprcndtrespdiv.innerHTML = mathrespcontent;
        //alert(mathexprcndtrespdiv.innerHTML);
	MathJax.Hub.Queue(["Typeset", MathJax.Hub, mathexprcndtrespdiv]);
	//alert("mathexprcdusvwcndtch_" + i.toString());
        mathexprcndtchlngdiv = document.getElementById("mathexprcdusvwcndtch_" + i.toString());
	//mathexprcndtchlngdiv = document.getElementById("challengestatement");
        mathexprcontent = mathexprcndtchlngdiv.innerHTML;
        mathexprcontent = mathexprcontent.replace(/\\?\[\s*/, "");
        mathexprcontent = mathexprcontent.replace(/\\?\]\s*/, "");
        mathexprcndtchlngdiv.innerHTML = mathexprcontent;
        //alert(mathexprcndtchlngdiv.innerHTML);
        MathJax.Hub.Queue(["Typeset", MathJax.Hub, mathexprcndtchlngdiv]);
        //MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
    }
    //alert("Number = " + countresp);
    //alert(MathJax.Hub.Queue.length); // Prints 0.
}

