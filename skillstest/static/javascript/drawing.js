
// Keep everything in anonymous function, called on window load.
if(window.addEventListener){
window.addEventListener('dblclick', function (){
  var canvas, context, canvaso, contexto;
  // The active tool instance.
  var tool;
  var tool_default = 'line';

  function init () {
    // Find the canvas element.
    canvaso = document.getElementById('imageView');
    if (!canvaso) {
      alert('Error: I cannot find the canvas element!');
      return;
    }

    if (!canvaso.getContext) {
      alert('Error: no canvas.getContext!');
      return;
    }

    // Get the 2D canvas context.
    contexto = canvaso.getContext('2d');
    if (!contexto) {
      alert('Error: failed to getContext!');
      return;
    }

    // Add the temporary canvas.
    var container = canvaso.parentNode;
    canvas = document.createElement('canvas');
    if (!canvas) {
      alert('Error: I cannot create a new canvas element!');
      return;
    }

    canvas.id     = 'imageTemp';
    canvas.width  = canvaso.width;
    canvas.height = canvaso.height;
    container.appendChild(canvas);

    context = canvas.getContext('2d');

    // Get the tool select input.
    var tool_select = document.getElementById('dtool');
    if (!tool_select) {
      alert('Error: failed to get the dtool element!');
      return;
    }
    tool_select.addEventListener('change', ev_tool_change, false);

    // Activate the default tool.
    if (tools[tool_default]) {
      tool = new tools[tool_default]();
      tool_select.value = tool_default;
    }

    // Attach the mousedown, mousemove and mouseup event listeners.
    canvas.addEventListener('mousedown', ev_canvas, false);
    canvas.addEventListener('mousemove', ev_canvas, false);
    canvas.addEventListener('mouseup',   ev_canvas, false);
  }

  // The general-purpose event handler. This function just determines the mouse 
  // position relative to the canvas element.
  function ev_canvas (ev) {
    if (ev.layerX || ev.layerX == 0) { // Firefox
      ev._x = ev.layerX;
      ev._y = ev.layerY;
    } else if (ev.offsetX || ev.offsetX == 0) { // Opera
      ev._x = ev.offsetX;
      ev._y = ev.offsetY;
    }

    // Call the event handler of the tool.
    var func = tool[ev.type];
    if (func) {
      func(ev);
    }
  }

  // The event handler for any changes made to the tool selector.
  function ev_tool_change (ev) {
    if (tools[this.value]) {
      tool = new tools[this.value]();
    }
  }

  // This function draws the #imageTemp canvas on top of #imageView, after which 
  // #imageTemp is cleared. This function is called each time when the user 
  // completes a drawing operation.
  function img_update () {
    contexto.drawImage(canvas, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
  }

  // This object holds the implementation of each drawing tool.
  var tools = {};

  // The drawing pencil.
  tools.pencil = function () {
    var tool = this;
    this.started = false;

    // This is called when you start holding down the mouse button.
    // This starts the pencil drawing.
    this.mousedown = function (ev) {
        context.beginPath();
        context.moveTo(ev._x, ev._y);
        tool.started = true;
    };

    // This function is called every time you move the mouse. Obviously, it only 
    // draws if the tool.started state is set to true (when you are holding down 
    // the mouse button).
    this.mousemove = function (ev) {
      if (tool.started) {
        context.lineTo(ev._x, ev._y);
	//context.strokeStyle = strokestyle;
        context.stroke();
      }
    };

    // This is called when you release the mouse button.
    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  // The rectangle tool.
  tools.rect = function () {
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }

      var x = Math.min(ev._x,  tool.x0),
          y = Math.min(ev._y,  tool.y0),
          w = Math.abs(ev._x - tool.x0),
          h = Math.abs(ev._y - tool.y0);

      context.clearRect(0, 0, canvas.width, canvas.height);

      if (!w || !h) {
        return;
      }
      //context.strokeStyle = strokestyle;
      context.strokeRect(x, y, w, h);
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  // The line tool.
  tools.line = function () {
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }

      context.clearRect(0, 0, canvas.width, canvas.height);

      context.beginPath();
      context.moveTo(tool.x0, tool.y0);
      context.lineTo(ev._x,   ev._y);
      //context.strokeStyle = strokestyle;
      context.stroke();
      context.closePath();
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  // The circle tool.
  tools.circle = function () {
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }
      drawOval(ev._x, ev._y);
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  function drawOval(x, y) {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.beginPath();
    context.moveTo(tool.x0, tool.y0 + (y - tool.y0) / 2);
    context.bezierCurveTo(tool.x0, tool.y0, x, tool.y0, x, tool.y0 + (y - tool.y0) / 2);
    context.bezierCurveTo(x, y, tool.x0, y, tool.x0, tool.y0 + (y - tool.y0) / 2);
    context.closePath();
    //context.strokeStyle = strokestyle;
    context.stroke();
  }

  // The rounded-rectangle tool.
  tools.roundedrect = function (){
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }
      roundRect(context, tool.x0, tool.y0, ev._x - tool.x0, ev._y - tool.y0, 5);
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  /**
 * Draws a rounded rectangle using the current state of the canvas. 
 * @param {CanvasRenderingContext2D} ctx
 * @param {Number} x The top left x coordinate
 * @param {Number} y The top left y coordinate 
 * @param {Number} width The width of the rectangle 
 * @param {Number} height The height of the rectangle
 * @param {Number} radius The corner radius. Defaults to 5;
 * @param {Boolean} fill Whether to fill the rectangle. Defaults to false.
 * @param {Boolean} stroke Whether to stroke the rectangle. Defaults to true.
 */
  function roundRect(ctx, x, y, width, height, radius) {
    if (typeof stroke == "undefined" ) {
      stroke = true;
    }
    if (typeof radius === "undefined") {
      radius = 20;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    //context.strokeStyle = strokestyle;
    ctx.stroke();
  }

  // The concave curved line tool.
  tools.curveconcave = function (){
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
      tool.x1 = tool.x0 + 50;
      tool.y1 = tool.y0 + 50;
      tool.x2 = tool.x1 + 50;
      tool.y2 = tool.y1 + 50;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }
      tool.xf = ev._x;
      tool.yf = ev._y;
      bezierCurve(context, tool.x0, tool.y0, tool.x1, tool.y1, tool.x2, tool.y2, tool.xf, tool.yf);
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  // The convex curved line tool.
  tools.curveconvex = function (){
    var tool = this;
    this.started = false;

    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
      tool.x1 = tool.x0 - 50;
      tool.y1 = tool.y0 - 50;
      tool.x2 = tool.x1 - 50;
      tool.y2 = tool.y1 - 50;
    };

    this.mousemove = function (ev) {
      if (!tool.started) {
        return;
      }
      tool.xf = ev._x;
      tool.yf = ev._y;
      bezierCurve(context, tool.x0, tool.y0, tool.x1, tool.y1, tool.x2, tool.y2, tool.xf, tool.yf);
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
        img_update();
      }
    };
  };

  function bezierCurve(context, x0, y0, x1, y1, x2, y2, xf, yf){
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.beginPath();
    context.moveTo(x0, y0);
    context.bezierCurveTo(x1, y1, x2, y2, xf, yf);

    context.strokeStyle = 'black';
    //context.strokeStyle = strokestyle;
    context.stroke();
  }

  // The text drawing tool.
  tools.text = function (){
    var tool = this;
    this.started = false;
    this.mousedown = function (ev){
      textcontent = document.getElementById('canvastext').value;
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
      context.font = 'italic 18px Arial';
      context.fillText(textcontent, tool.x0, tool.y0);
      //context.strokeStyle = strokestyle;
      context.stroke();
    };

    this.mouseup = function (ev){
      if (tool.started){
        tool.started = false;
        img_update();
      }
    };
  };

  // Eraser tool
  tools.eraser = function (){
    var tool = this;
    this.started = false;
    strokestyle_orig = context.strokeStyle;
    this.mousedown = function (ev){
        context.beginPath();
        context.moveTo(ev._x, ev._y);
        tool.started = true;
    };

    this.mousemove = function (ev) {
      if (tool.started) {
      	context.lineWidth = 20;
        context.lineTo(ev._x, ev._y);
	context.strokeStyle = '#669999';
        context.stroke();
      }
    };

    this.mouseup = function (ev) {
      if (tool.started) {
        tool.mousemove(ev);
        tool.started = false;
	// Restore the previous settings.
	context.lineWidth = 1;
	context.strokeStyle = strokestyle_orig;
	img_update();
      }
    };
  };

  // Arrow Tool
  tools.arrow = function (){
    var tool = this;
    this.started = false;
    reversedirection = false;
    this.mousedown = function (ev) {
      tool.started = true;
      tool.x0 = ev._x;
      tool.y0 = ev._y;
      reversedirection = false;
    };

    this.mousemove = function (ev) {
      if (!tool.started){
        return;
      }
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.beginPath();
      context.fillStyle = "rgba(0, 0, 0,1)";
      context.moveTo(tool.x0, tool.y0);
      context.quadraticCurveTo(tool.x0, tool.y0, ev._x, ev._y);
      //context.strokeStyle = strokestyle;
      context.stroke();
    };

    this.mouseup = function (ev){
      if (tool.started){
	tool.mousemove(ev);
	if(tool.x0 > ev._x){
	    reversedirection = true;
        }
	var ang = findAngle(tool.x0, tool.y0, ev._x, ev._y,reversedirection);
	context.fillRect(ev._x, ev._y, 2, 2);
 	drawArrowhead(context, ev._x, ev._y, ang, 12, 12);
        tool.started = false;
        img_update();
      }
    };
  };

 
    function drawArrowhead(ctx, locx, locy, angle, sizex, sizey){
        var hx = sizex / 2;
        var hy = sizey / 2;
	ctx.translate((locx ), (locy));
        ctx.rotate(angle);
        ctx.translate(-hx, -hy);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, 1*sizey);    
        ctx.lineTo(1*sizex, 1*hy);
        ctx.closePath();
        ctx.fill();
	// Do the reverse of what we did to draw the arrowhead
	ctx.translate(hx, hy);
	ctx.rotate(-angle);
	ctx.translate((-locx ), (-locy));
    }
    
    // returns radians
    function findAngle(sx, sy, ex, ey, reversedirection) {
	if(!reversedirection){
            return Math.atan((ey - sy) / (ex - sx));
	}
	else{
	    return Math.PI + Math.atan((ey - sy) / (ex - sx));
	}
    }

  init();

}, false); }



