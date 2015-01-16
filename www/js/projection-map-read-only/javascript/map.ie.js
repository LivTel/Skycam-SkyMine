//
// Projection Map Library.
//
// @Copyleft: 2011 University of Hawaii Institute for Astronomy
// @Project:  This project originated as a component of the Pan-STARRS project.
// @Authors:  (Thomas) Xin Chen, Larry Denneau, Conrad Holmberg
// @History:
// @License: The MIT License (MIT)
// Copyright (c) <2011> <PanSTARRS>
// Permission is hereby granted, free of charge, to any person obtaining a copy of 
// this software and associated documentation files (the "Software"), to deal in the 
// Software without restriction, including without limitation the rights to use, copy, 
// modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
// and to permit persons to whom the Software is furnished to do so, subject to the 
// following conditions: The above copyright notice and this permission notice shall be 
// included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED 
// "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO 
// THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
// IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR 
// OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT 
// OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//
//


//////////////////////////////////////////////
// Global variables and functions.
//////////////////////////////////////////////

function btnSpin_OnClick(btnSpin) {
  projMap.btnSpin_OnClick(btnSpin);
}


function useDefault() {
  projMap.btnReset_OnClick();
}


if (typeof (ProjectionMap) == "undefined") {

    //////////////////////////////////////////////
    // Class ProjectionMap.
    //////////////////////////////////////////////

    //
    // E.g., call with:
    // var proj = new HammerProjection();
    // //var proj = new SinusoidalProjection();
    // //var proj = new MollweideProjection();
    // //var proj = new FlatProjection();
    // var projMap = new ProjectionMap(proj);
    //
    //function ProjectionMap(projection) {
    var ProjectionMap = function(projection) {
        this.className = 'ProjectionMap';
        this.width = 900;
        this.height = 600;

        this.DTR = Math.PI / 180.0;
        this.RTD = 180.0 / Math.PI;

        this.vDebug = true;
        this.proj = projection;

        this.pos_x0 = 0; // (pos_x0, pos_y0) - position of the graph in canvas.
        this.pos_y0 = 0;

        this.mouse_x0 = 0; // (mouse_x0, mouse_y0) - cursor starting position each time mouse is down.
        this.mouse_y0 = 0;

        this.zoomDefault = 10; // Initial zoom value. Does not change.
        this.zoom0 = this.zoomDefault; // This will change according to zoom slider.

        this.ctrlDown = false;
        this.vSelect = false;
        this.vDrag = false;

        this.sliderZoomID = 'slider-2';
        this.sliderZoomInputID = 'slider-input-2';
        this.sliderZoomLabelID = 'vZoom';

        this.sliderRotationID = "slider-1";
        this.sliderRotationInputID = "slider-input-1";
        this.sliderRotationLabelID = "vRotation";

        this.vSpin = null;
        this.spin_left = false;

        this.select_start = null;
        this.select_end = null;

        this.vFrameListVal = '';

        this.selectCanvasInitiated = false;

        this.slider1 = null;
        this.slider2 = null;

        // Initialize Html Elements.
        this.vSelectCanvas = document.getElementById('selectCanvas');
        this.vMapCanvas = document.getElementById('map');
        this.vMsg = document.getElementById('tmp');
        this.vFrameList = document.getElementById("FrameList");
        this.vFrameCount = document.getElementById("FrameCount");
        this.vMapToolbar = document.getElementById("MapToolbar");
        this.vLoc = document.getElementById("example");

        this.keydown_select = false;
        this.keydown_deselect = false;

        this.init();
    }


    //////////////////////////////////////////////
    // Initialization. Start.


    ProjectionMap.prototype.init = function() {
        this.initCanvas();
        this.initSlider_Rotation(this);
        this.initSlider_Zoom(this);

        // Can't use "this" in event handlers, since it refers to "window"!
        //window.addEventListener('keydown', this.doKeyDown, true);
        //window.addEventListener('keyup', this.doKeyUp, true);
        //window.addEventListener('resize', this.updateSelectCanvasPosition, true);
        var p = this;
        document.attachEvent('onkeydown', function(e) { p.doKeyDown(e, p); });
        document.attachEvent('onkeyup', function(e) { p.doKeyUp(e, p); });
        document.attachEvent('onresize', function(e) { p.updateSelectCanvasPosition(e, p); });

        this.drawHammer(fields, 0, 0, 0, 10);
    }


    //
    // find absolute position of an element on screen.
    // http://www.quirksmode.org/js/findpos.html
    //
    ProjectionMap.prototype.findPos = function(obj) {
        var curleft = curtop = 0;
        if (obj.offsetParent) {
            do {
                curleft += obj.offsetLeft;
                curtop += obj.offsetTop;
            } while (obj = obj.offsetParent);
        }
        return [curleft, curtop];
    }


    //
    // e - event, p - ProjectionMap object.
    //
    ProjectionMap.prototype.updateSelectCanvasPosition = function(e, p) {
        if (!p || !p.vMapCanvas || !p.vSelectCanvas) { return; }

        var a = p.findPos(p.vMapCanvas);
        p.vSelectCanvas.style.left = a[0] + 'px';
        p.vSelectCanvas.style.top = a[1] + 'px';
        p.vSelectCanvas.width = p.vMapCanvas.width;
        p.vSelectCanvas.height = p.vMapCanvas.height;
    }


    ProjectionMap.prototype.initSlider_Rotation = function(me) {
        var slider = document.getElementById(me.sliderRotationID);
        var input = document.getElementById(me.sliderRotationInputID);
        me.slider1 = new Slider(slider, input);
        me.slider1.setMaximum(360);
        me.slider1.setValue(0);

        me.slider1.onchange = function() {
            var rotate0 = me.slider1.getValue();
            document.getElementById(me.sliderRotationLabelID).innerHTML = rotate0;
            me.drawHammer(fields, me.pos_x0, me.pos_y0, rotate0, me.zoom0);
        };
    }


    ProjectionMap.prototype.initSlider_Zoom = function(me) {
        var slider = document.getElementById(me.sliderZoomID);
        var input = document.getElementById(me.sliderZoomInputID);
        me.slider2 = new Slider(slider, input);
        me.slider2.setMaximum(150);
        me.slider2.setMinimum(5);
        me.slider2.setValue(me.zoomDefault);
        me.zoomOffset = 1;

        me.slider2.onchange = function() {
            me.zoom0 = me.slider2.getValue();
            me.zoomOffset = me.zoom0 / me.zoomDefault;
            document.getElementById(me.sliderZoomLabelID).innerHTML = me.zoom0;
            me.drawHammer(fields, me.pos_x0, me.pos_y0, me.slider1.getValue(), me.zoom0);
        };
    }


    ProjectionMap.prototype.initCanvas = function() {
        if (!this.vMapCanvas) { return; }

        this.vMapCanvas.width = this.width;
        this.vMapCanvas.height = this.height;
        this.initMapEventListener(this);

        if (!this.vSelectCanvas) { return; }

        this.vSelectCanvas.style.border = 'solid 1px #00ff00';
        this.vSelectCanvas.style['background'] = '#000000';
        this.vSelectCanvas.style.display = 'none';
        this.initSelectEventListener(this);

        if (this.vMapToolbar) { this.vMapToolbar.width = this.width; }

        if (!this.selectCanvasInitiated) {
            this.updateSelectCanvasPosition(null, this);
            this.selectCanvasInitiated = true;
        }
    }


    ProjectionMap.prototype.initMapEventListener = function(me) {

        me.vMapCanvas.attachEvent('onmousedown', function(e) {
            if (e.button != 1) { return; } // do nothing if not left mouse button.
            var loc = me.getLoc(e, me); // + " (mouse Down)";
            me.showLoc(loc, me);
            me.mouse_x0 = me.pageX(e) - me.vMapCanvas.offsetLeft;
            me.mouse_y0 = me.pageY(e) - me.vMapCanvas.offsetTop;
            me.vDrag = true;
        });

        me.vMapCanvas.attachEvent('onmousemove', function(e) {
            var loc = me.getLoc(e, me);
            me.showLoc(loc, me);

            // Move this to onmouseup, draw only once to speed it up.
            //if (me.vDrag) {
            //    var delta_x = (me.pageX(e) - me.vMapCanvas.offsetLeft) - me.mouse_x0;
            //    var delta_y = (me.pageY(e) - me.vMapCanvas.offsetTop) - me.mouse_y0;
            //    me.drawHammer(fields, me.pos_x0 + delta_x, me.pos_y0 + delta_y,
            //             me.slider1.getValue(), me.slider2.getValue());
            //}
        });

        me.vMapCanvas.attachEvent('onmouseup', function(e) {
            var loc = me.getLoc(e, me); // + "(mouse Up)";
            me.showLoc(loc, me);
            if (me.vDrag) {
                var delta_x =
                    ((me.pageX(e) - me.vMapCanvas.offsetLeft) - me.mouse_x0) / me.zoomOffset;
                var delta_y =
                    ((me.pageY(e) - me.vMapCanvas.offsetTop) - me.mouse_y0) / me.zoomOffset;
                me.drawHammer(fields, me.pos_x0 + delta_x, me.pos_y0 + delta_y,
                              me.slider1.getValue(), me.slider2.getValue());

                me.pos_x0 += delta_x; //(me.pageX(e) - me.vMapCanvas.offsetLeft) - me.mouse_x0;
                me.pos_y0 += delta_y; //(me.pageY(e) - me.vMapCanvas.offsetTop) - me.mouse_y0;
                me.vDrag = false;
            }
        });

        //me.vMapCanvas.attachEvent('onmouseout', function(e) {
        me.vMapCanvas.attachEvent('onmouseleave', function(e) {
            me.showLoc("", me);
            me.vDrag = false;
        });
    }


    ProjectionMap.prototype.initSelectEventListener = function(me) {

        me.vSelectCanvas.attachEvent('onmousedown', function(e) {
            if (e.which == 3) { return; } // do nothing for right mouse button.
            var loc = me.getLoc(e, me); // + "(mouse Down)";
            me.showLoc(loc, me);

            me.mouse_x0 = me.pageX(e) - me.vSelectCanvas.offsetLeft;
            me.mouse_y0 = me.pageY(e) - me.vSelectCanvas.offsetTop;
            if (!me.vSelect) {
                me.vMsg.innerHTML = '';
                me.select_start = me.doSelect();  // CTRL is down, do select by pressing mouse.
            }
            me.vSelect = true;
        });


        me.vSelectCanvas.attachEvent('onmousemove', function(e) {
            var loc = me.getLoc(e, me); 
            me.showLoc(loc, me);

            if (me.vSelect) {
                var mouse_x1 = me.pageX(e) - me.vSelectCanvas.offsetLeft;
                var mouse_y1 = me.pageY(e) - me.vSelectCanvas.offsetTop;
                me.drawSelectRect(me.mouse_x0, me.mouse_y0, mouse_x1, mouse_y1);
            }
        });


        me.vSelectCanvas.attachEvent('onmouseup', function(e) {
            var loc = me.getLoc(e, me); // + "(mouse up)");
            me.showLoc(loc, me);

            if (me.vSelect) {
                me.clearSelectRect();
                me.vSelect = false;

                me.mouse_x0 = me.pageX(e) - me.vSelectCanvas.offsetLeft;
                me.mouse_y0 = me.pageY(e) - me.vSelectCanvas.offsetTop;
                me.select_end = me.doSelect();

                me.getSelectedData(me.select_start, me.select_end);
            }
        });

        me.vSelectCanvas.attachEvent('onmouseout', function(e) {
            me.showLoc("", me);
            me.vSelect = false;
        });
    }



    ProjectionMap.prototype.doKeyDown = function(evt, p) {
        if (!evt || !p) { return; }
            var key_code = evt.keyCode;
            // 83 - s, 68 - d.
            if (key_code == 83 || key_code == 68) {
            if (key_code == 83) { p.keydown_select = true; }
            if (key_code == 68) { p.keydown_deselect = true; }
            p.vSelectCanvas.style.display = 'block';
        }
        else if (key_code == 17) { // 17 - ctrl
            p.ctrlDown = true;
        }
        else if (key_code == 67 && !p.ctrlDown) { // 67 - c.
            p.clearSelectedData();
        }
    }


    ProjectionMap.prototype.doKeyUp = function(evt, p) {
        if (!evt || !p) { return; }
        var key_code = evt.keyCode;
        if (key_code == 83 || key_code == 68) {
            if (key_code == 83) { p.keydown_select = false; }
            if (key_code == 68) { p.keydown_deselect = false; }
            p.vSelectCanvas.style.display = 'none';
        }
        else if (key_code == 17) {
            p.ctrlDown = false;
        }
    }


    // Initialization. End.
    //////////////////////////////////////////////


    //////////////////////////////////////////////
    // Action functions.
    //////////////////////////////////////////////

    //          
    // Called when Reset button is clicked.
    //          
    ProjectionMap.prototype.btnReset_OnClick = function() {
        this.pos_x0 = 0;
        this.pos_y0 = 0;
        this.zoom0 = 10;
        rotation = 0;
        this.slider1.setValue(rotation);
        this.slider2.setValue(this.zoom0);

        this.setMsg("", this);
        this.drawHammer(fields, this.pos_x0, this.pos_y0, rotation, this.zoom0);
    }


    //
    // Called when spin button is clicked.
    //
    ProjectionMap.prototype.btnSpin_OnClick = function(btnSpin) {
        if (btnSpin.title == 'Spin') {
            btnSpin.title = 'Pause';
            btnSpin.src = 'javascript/slider/pause.png';

            var interval, len = fields.length;
            if (len <= 1000) { interval = 200; }
            else if (len <= 2000) { interval = 300; }
            else if (len <= 5000) { interval = 1000; }
            else if (len <= 10000) { interval = 1500; }
            else { interval = 3000; }

            var p = this;
            this.vSpin = setInterval(function() { p.doSpin(p); }, interval);

        } else if (btnSpin.title == 'Pause') {
            btnSpin.title = 'Spin';
            btnSpin.src = 'javascript/slider/play.gif';
            clearInterval(this.vSpin);
        }
    }


    //////////////////////////////////////////////
    // Draw projection map. Start.

    ProjectionMap.prototype.initMinMax = function() {
        this.min_x = Number.POSITIVE_INFINITY,
    this.max_x = Number.NEGATIVE_INFINITY,
    this.min_y = Number.POSITIVE_INFINITY,
    this.max_y = Number.NEGATIVE_INFINITY;
    }


    ProjectionMap.prototype.updateMinMax = function(p) {
        this.min_x = Math.min(this.min_x, p.x);
        this.max_x = Math.max(this.max_x, p.x);
        this.min_y = Math.min(this.min_y, p.y);
        this.max_y = Math.max(this.max_y, p.y);
    }


    ProjectionMap.prototype.updateMapParams = function(pos_x, pos_y, zoom) {
        var w = this.width - 100, h = this.height - 100;
        w *= (zoom / 10.0);
        h *= (zoom / 10.0);

        this.xof = this.width / 2 - w / 2 + pos_x;
        this.yof = this.height / 2 - h / 2 + pos_y;
        this.s = Math.min(w / (this.max_x - this.min_x), h / (this.max_y - this.min_y)); // the scale
        this.xx = (w - (this.max_x - this.min_x) * this.s) / 2 + this.xof + 2;
        this.yy = (h - (this.max_y - this.min_y) * this.s) / 2 + this.yof + 2;
    }


    ProjectionMap.prototype.world2Canvas = function(lamda, phi) { // world->coord->canvas.
        var p = this.proj.project(lamda, phi, { x: 0, y: 0 }); // this.proj
        if (p == null) { return null; }
        return this.coord2Canvas(p);
    }


    ProjectionMap.prototype.coord2Canvas = function(p) { // coordinate system (x,y) to canvas(x,y).
        if (p == null) { return null; }
        p.x = (p.x - this.min_x) * this.s + this.xx;
        p.y = (p.y - this.min_y) * this.s + this.yy;
        return p;
    }


    ProjectionMap.prototype.canvas2Coord = function(p) {
        if (p == null) { return null; }
        p.x = this.min_x + (p.x - this.xx) / this.s;
        p.y = this.min_y + (p.y - this.yy) / this.s;
        return p;
    }


    ProjectionMap.prototype.outOfRange = function(p) {
        return p.x < this.min_x || p.x > this.max_x || p.y < this.min_y || p.y > this.max_y;
    }


    ProjectionMap.prototype.log = function(msg) {
        var p = document.createElement('div');
        p.innerHTML = msg;
        document.body.appendChild(p);
    }


    ProjectionMap.prototype.deg2rad = function(deg) {
        return deg * this.DTR;
    }


    ProjectionMap.prototype.rad2deg = function(rad) {
        return rad * this.RTD;
    }


    // calculate this for rotation.
    ProjectionMap.prototype.getLamda = function(x, delta) {
        var lam = x - 180 - delta;
        if (lam < -180) lam += 360; // wrap around.
        return lam;
    }


    //
    // @Parameters:
    //  - (pos_x, pos_y) for shift.
    //  - delta_ra for rotation.
    //  - zoom for zooming.
    //
    ProjectionMap.prototype.drawHammer = function(fields, pos_x, pos_y, delta_ra, zoom) {
        // Check the element is in the DOM and the browser supports canvas
        if (!this.vMapCanvas || !this.vMapCanvas.getContext) { return; }
        var start_time = new Date().valueOf();

        var lines = [];
        var labels = [];
        this.preprocess(lines, labels, delta_ra);

        var context = this.vMapCanvas.getContext('2d');
        context.lineWidth = 1;

        pos_x *= this.zoomOffset;
        pos_y *= this.zoomOffset;

        this.updateMapParams(pos_x, pos_y, zoom);

        // clear canvas before drawing.
        this.clearCanvas(context);
        this.drawGrid(lines, context);
        this.drawCurve(lines[lines.length - 2], context); // Galactic line.
        this.drawCurve(lines[lines.length - 1], context); // Ecliptic line.
        this.drawLabel(labels, context);

        var WDEG = 1.0; // size of square patches.
        var lamda1, lamda2, phi1, phi2, p1, p2, p3, p4, filter;
        var ddec = WDEG;
        var dra = WDEG;
        var x_cutoff = this.width, y_cutoff = this.height;
        // no need to handle wrap around for pole projections.
        var handleWrap = !(this.proj.ClassName == 'NorthPoleProjection' ||
                        this.proj.ClassName == 'SouthPoleProjection');

        // Field locations. 
        for (foo = 0; foo < fields.length; foo++) {
            f = fields[foo];
            fra = parseFloat(f['ra_deg']);
            fdec = parseFloat(f['dec_deg']);
            //dra = WDEG / Math.cos(this.deg2rad(fdec));

            lamda1 = this.deg2rad(this.getLamda(fra + dra, delta_ra));
            lamda2 = this.deg2rad(this.getLamda(fra - dra, delta_ra));
            phi1 = this.deg2rad(fdec + ddec);
            phi2 = this.deg2rad(fdec - ddec);

            // Corners. 
            if ((p1 = this.world2Canvas(lamda1, phi1)) == null) { continue; }
            if ((p2 = this.world2Canvas(lamda2, phi1)) == null) { continue; }
            if ((p3 = this.world2Canvas(lamda2, phi2)) == null) { continue; }
            if ((p4 = this.world2Canvas(lamda1, phi2)) == null) { continue; }

            if (handleWrap && p2.x < p1.x) {
                p2.x = p1.x + WDEG;
                p3.x = p4.x + WDEG;
            }

            // clipping: point 1 - upper left corner, point 3 - bottom right corner.
            if (p3.x < 0 || p1.x > x_cutoff || p3.y < 0 || p1.y > y_cutoff) { continue; }

            // Draw the shape for the field.
            filter = f['filter'];
            if (filter == null) filter = '';
            context.strokeStyle = scolors[filter];
            if (f['selected'] == 1) { context.strokeStyle = '#FFFFFF'; }
            context.fillStyle = fcolors[filter];
            context.beginPath();
            context.moveTo(p1.x, p1.y);
            context.lineTo(p2.x, p2.y);
            context.lineTo(p3.x, p3.y);
            context.lineTo(p4.x, p4.y);
            context.lineTo(p1.x, p1.y);
            context.fill();
            context.stroke();
        }

        //var duration = (new Date().valueOf() - start_time)/1000;
        //this.log('Data projection took '+duration+' secs');
    }


    //
    // get lines and labels.
    //
    ProjectionMap.prototype.preprocess = function(lines, labels, delta_ra) {
        var tmp, val, color;
        var delta_ra0 = delta_ra;
        this.initMinMax();

        for (cx = 0; cx < griddata.length; cx++) {
            tmp = griddata[cx].split('\t');
            val = tmp[0];
            color = tmp[1];

            if (val == "line") {
                // recover delta_ra0 for last 2 rows: galactic/ecliptic lines.
                if (cx == griddata.length - 2) { delta_ra0 = delta_ra; }

                var lpt = tmp[2].split(';');
                var line = new Array();
                var last = null;
                for (px = 0; px < lpt.length; px++) {
                    var pt = lpt[px].split(',');
                    if (last != null && Math.abs(last[0] - pt[0]) > 180) {
                        lines.push({ 'color': color, 'line': line });
                        line = new Array();
                    }

                    var p = this.proj.project(this.deg2rad(this.getLamda(pt[0], delta_ra0)),
                                          this.deg2rad(pt[1]), { x: 0, y: 0 });
                    if (p == null) { continue; }
                    this.updateMinMax(p);
                    line.push(p);
                    last = pt;
                }
                lines.push({ 'color': color, 'line': line });
            }
            else if (val == "label") {
                var pt = tmp[2].split(',');

                var p = this.proj.project(this.deg2rad(this.getLamda(pt[0], delta_ra0)),
                                      this.deg2rad(pt[1]), { x: 0, y: 0 });
                if (p == null) { continue; }
                this.updateMinMax(p);
                labels.push({ 'color': color, 'loc': p, 'label': tmp[3] });

                if (pt[0] == 360) { delta_ra0 = 0; } // the last data row for longitude.
            }
        }
    }


    ProjectionMap.prototype.clearCanvas = function(context) {
        context.fillStyle = '#000000';
        context.fillRect(0, 0, this.width, this.height);
    }


    ProjectionMap.prototype.drawLabel = function(labels, context) {
        context.font = "11px sans-serif";
        context.fillStyle = "#FFFFFF";
        context.textAlign = "left";
        context.textBaseline = "top";

        for (sx = 0; sx < labels.length; sx++) {
            label = labels[sx];
            var color = label.color;
            var p = this.coord2Canvas(label.loc);
            context.fillText(label.label, p.x, p.y);
        }
    }


    ProjectionMap.prototype.drawGrid = function(lines, context) {
        var line, sx, px, p;

        for (sx = 0; sx < lines.length - 2; sx++) {
            line = lines[sx].line;
            if (line.length == 0) continue;

            context.strokeStyle = lines[sx].color; ;
            context.lineWidth = 1;
            context.beginPath();

            p = this.coord2Canvas(line[0]);
            context.moveTo(p.x, p.y);
            for (px = 1; px < line.length; px++) {
                p = this.coord2Canvas(line[px]);
                context.lineTo(p.x, p.y);
            }

            context.stroke();
        }
    }


    ProjectionMap.prototype.drawCurve = function(lines, context) {
        var line = lines.line;
        if (line.length == 0) { return; }

        context.strokeStyle = lines.color;
        context.lineWidth = 1;
        context.beginPath();
        var x0 = 0, y0 = 0, px, k, p;
        var GAP_CUTOFF = 200;

        p = this.coord2Canvas(line[0]);
        context.moveTo(p.x, p.y);
        for (px = 1; px < line.length; px++) {
            p = this.coord2Canvas(line[px]);
            k = (x0 > p.x) ? x0 - p.x : p.x - x0;
            if (k > GAP_CUTOFF) { context.moveTo(p.x, p.y); } // Don't draw wrapping line.
            else { context.lineTo(p.x, p.y); }
            x0 = p.x, y0 = p.y;
        }

        context.stroke();
    }

    // Draw projection map. End.
    //////////////////////////////////////////////


    //////////////////////////////////////////////
    // Do selection. Start.

    ProjectionMap.prototype.clearSelectRect = function() {
        if (!this.vSelectCanvas) { return; }

        var context = this.vSelectCanvas.getContext('2d');
        if (!context) { return; }

        context.clearRect(0, 0, this.vSelectCanvas.width, this.vSelectCanvas.height);
    }


    //
    // return value: array [error_code, ra,dec, x,y, mouse_x0,mouse_y0].
    //   error code: 0 if succeed, 1/2/3 if fail (out of range).
    //   (x, y) - (x, y) in map coordiate system
    //
    ProjectionMap.prototype.doSelect = function() {
        // { x : this.mouse_x0, y : this.mouse_y0 } - a point object {x,y}.
        var p = this.canvas2Coord({ x: this.mouse_x0, y: this.mouse_y0 });

        var ipt = this.proj.inverse_project(p.x, p.y, { ra: 0.0, dec: 0.0 });

        // check out of range error.
        if (ipt == null) { return [1, 0, 0, p.x, p.y, this.mouse_x0, this.mouse_y0]; }
        if (this.outOfRange(p)) {
            return [2, ipt.ra, ipt.dec, p.x, p.y, this.mouse_x0, this.mouse_y0]; // out of range.
        }

        // out of range type 3: out of range in corner.
        if (this.proj.ClassName == "NorthPoleProjection") {
            if (ipt.dec < 0) { return [3, ipt.ra, ipt.dec, p.x, p.y, this.mouse_x0, this.mouse_y0]; }
        } else if (this.proj.ClassName == "SouthPoleProjection") {
            if (ipt.dec > 0) { return [3, ipt.ra, ipt.dec, p.x, p.y, this.mouse_x0, this.mouse_y0]; }
        } else {
            if (p.x * ipt.ra > 0) { return [3, ipt.ra, ipt.dec, p.x, p.y, this.mouse_x0, this.mouse_y0]; }
        }

        // reverse of getLamda(). 
        ipt.ra = this.rad2deg(ipt.ra) + this.slider1.getValue() + 180;
        ipt.ra %= 360;
        if (ipt.ra > 180) ipt.ra -= 360;

        ipt.dec = this.rad2deg(ipt.dec);

        return [0, ipt.ra, ipt.dec, p.x, p.y, this.mouse_x0, this.mouse_y0];
    }


    ProjectionMap.prototype.drawSelectRect = function(x0, y0, x1, y1) {
        if (!this.vSelectCanvas) { return; }

        var context = this.vSelectCanvas.getContext('2d');
        if (!context) { return; }

        context.clearRect(0, 0, this.vSelectCanvas.width, this.vSelectCanvas.height);

        context.strokeStyle = '#FFFFFF';
        context.beginPath();
        context.moveTo(x0, y0);
        context.lineTo(x1, y0);
        context.lineTo(x1, y1);
        context.lineTo(x0, y1);
        context.lineTo(x0, y0);
        context.stroke();
    }


    //
    // p0 - start point, p1 - end point.
    // contents of p: [ra, dec, x, y].
    //
    ProjectionMap.prototype.getSelectedData = function(p0, p1) {
        if (p0 == null || p1 == null) { return; }

        if (this.vDebug) {
            this.setMsg("", this);
            if (p0[0] != 0) { this.appendMsg("start point out of range (code:" + p0[0] + ")", this); }
            if (p1[0] != 0) { this.appendMsg("  end point out of range (code:" + p1[0] + ")", this); }

            this.appendMsg(
      '<br>Start: [ra,dec:' + p0[1] + ',' + p0[2] +
      '; map(x,y):' + p0[3] + ',' + p0[4] + '; mouse(x,y):' + p0[5] + ',' + p0[6] + ']' +
      '<br>End: [ra,dec:' + p1[1] + ',' + p1[2] +
      '; map(x,y):' + p1[3] + ',' + p1[4] + '; mouse(x,y):' + p1[5] + ',' + p1[6] + ']<br>', this);
        }

        if (p0[0] == 1 || p1[0] == 1) { return; } // do nothing for error code 1.

        if (this.vFrameList) { this.clearFrameList(); }

        var count;
        if (p0[1] == p1[1] && p0[2] == p1[2]) { count = this.getSelectedData_Point(p0[1], p0[2]); }
        else { count = this.getSelectedData_Area(p0, p1); }

        if (this.vFrameCount) { this.vFrameCount.innerHTML = count; }
        if (this.vFrameList) { this.vFrameList.innerHTML = this.vFrameListVal; }

        this.drawHammer(fields, this.pos_x0, this.pos_y0, this.slider1.getValue(), this.slider2.getValue());
    }


    ProjectionMap.prototype.getSelectedData_Point = function(x, y) {
        var i, len = fields.length, f, fra0, fra, fdec, in_range;
        var WDEG = 1.0, ddec = WDEG, dra = WDEG;
        var count = 0;

        for (i = 0; i < len; i++) {
            f = fields[i];
            fra = fra0 = parseFloat(f['ra_deg']);
            if (fra > 180) fra -= 360;
            //dra = WDEG / Math.cos(this.deg2rad(fdec));
            fdec = parseFloat(f['dec_deg']);
            in_range = (Math.abs(x - fra) < dra) && (Math.abs(y - fdec) < ddec);

            count += this.handleRange(in_range, f, fra0, fdec);
        }
        return count;
    }


    ProjectionMap.prototype.getSelectedData_Area = function(p0, p1) {
        var min_x = Math.min(p0[1], p1[1]);
        var max_x = Math.max(p0[1], p1[1]);
        var min_y = Math.min(p0[2], p1[2]);
        var max_y = Math.max(p0[2], p1[2]);

        // p0 and p1 are on the two sides of the line "-180|180", so: (x1 - x0) * (ra1 - ra0) > 0.
        var cross_180_line = (min_x < 0 && max_x > 0) && ((p1[1] - p0[1]) * (p1[3] - p0[3]) > 0);

        var i, len = fields.length, f, fra0, fra, fdec, in_range, count = 0;
        for (i = 0; i < len; i++) {
            f = fields[i];
            fra = fra0 = parseFloat(f['ra_deg']);
            if (fra > 180) fra -= 360;
            fdec = parseFloat(f['dec_deg']);

            if (cross_180_line) {
                in_range = (fra <= min_x && fra >= -180 && fdec >= min_y && fdec <= max_y) ||
                 (fra >= max_x && fra <= 180 && fdec >= min_y && fdec <= max_y);
            } else {
                in_range = (fra >= min_x && fra <= max_x && fdec >= min_y && fdec <= max_y);
            }

            count += this.handleRange(in_range, f, fra0, fdec);
        }

        return count;
    }


    ProjectionMap.prototype.clearSelectedData = function() {
        var i, len = fields.length;
        for (i = 0; i < len; i++) {
            fields[i]['selected'] = 0;
        }

        if (this.vFrameList) { this.clearFrameList(); }
        this.drawHammer(fields, this.pos_x0, this.pos_y0, this.slider1.getValue(), this.slider2.getValue());
    }


    //
    // If ctrl is down, select; if shift is down, de-select.
    //
    ProjectionMap.prototype.handleRange = function(in_range, f, fra0, fdec) {
        var count = 0;
        if (in_range) {
            if (this.keydown_select) {
                f['selected'] = 1;
                this.addFrameList(fra0 + ', ' + fdec);
                count = 1;
            } else if (this.keydown_deselect) {
                f['selected'] = 0;
            }
        } else {
            if (f['selected'] == 1) { // already selected.
                this.addFrameList(fra0 + ', ' + fdec);
                count = 1;
            }
        }
        return count;
    }


    ProjectionMap.prototype.clearFrameList = function() {
        this.vFrameList.innerHTML = '';
        this.vFrameListVal = '';
        this.vFrameCount.innerHTML = '';
    }


    ProjectionMap.prototype.addFrameList = function(txt) {
        this.vFrameListVal += txt + '\n';
    }


    // Do selection. End.
    //////////////////////////////////////////////


    //////////////////////////////////////////////
    // Helper functions. Start.

    //
    // firefox uses pageX.
    // IE and Opera browsers use different parameters.
    // See: http://javascript.about.com/library/blmousepos.htm
    //
    ProjectionMap.prototype.pageX = function(e) {
        if (e.pageX) return e.pageX;
        else if (e.clientX)
            return e.clientX + (document.documentElement.scrollLeft ?
                document.documentElement.scrollLeft : document.body.scrollLeft);
        else return null;
    }
    
    
    ProjectionMap.prototype.pageY = function(e) {
        if (e.pageY) return e.pageY;
        else if (e.clientY)
            return e.clientY + (document.documentElement.scrollTop ?
                document.documentElement.scrollTop : document.body.scrollTop);
        else return null;
    }
    
    
    ProjectionMap.prototype.getLoc = function(e, me) {
        if (!me.vMapCanvas) { return ""; }
        return " [x,y]:[" + (me.pageX(e) - me.vMapCanvas.offsetLeft) + "," +
                      (me.pageY(e) - me.vMapCanvas.offsetTop) + "]";
    }
    

    ProjectionMap.prototype.showLoc = function(s, me) {
        if (me.vLoc) { me.vLoc.innerHTML = s; }
    }
    
    
    ProjectionMap.prototype.setMsg = function(s, me) {
        if (me.vMsg) { me.vMsg.innerHTML = s; }
    }


    ProjectionMap.prototype.appendMsg = function(s, me) {
        if (me.vMsg) { me.vMsg.innerHTML += s; }
    }
    

    ProjectionMap.prototype.doSpin = function(p) {
        var i = p.slider1.getValue();
        if (p.spin_left) {
            p.slider1.setValue(--i);
            if (i == 0) { p.spin_left = false; }
        } else {
            p.slider1.setValue(++i);
            if (i == 360) { p.spin_left = true; }
        }
    }


    // Helper functions. End.
    //////////////////////////////////////////////

} // end of "if (typeof ProjectionMap == "undefined")"


//////////////////////////////////////////////
// Global data.
//////////////////////////////////////////////

var fcolors = {
    'g': '#008000',
    'r': '#800000',
    'i': '#804000',
    'z': '#004080',
    'y': '#808000',
    'w': '#606060',
    '' : '#999999'
};


var scolors = {
    'g': '#00B000',
    'r': '#B00000',
    'i': '#B08000',
    'z': '#0080B0',
    'y': '#B0B000',
    'w': '#E0E0E0',
    '' : '#999999'
};


// Hammer-Aitoff grid.
griddata = [
"line	#808080	0,-90;0,-85;0,-80;0,-75;0,-70;0,-65;0,-60;0,-55;0,-50;0,-45;0,-40;0,-35;0,-30;0,-25;0,-20;0,-15;0,-10;0,-5;0,0;0,5;0,10;0,15;0,20;0,25;0,30;0,35;0,40;0,45;0,50;0,55;0,60;0,65;0,70;0,75;0,80;0,85;0,90",
"label	#808080	0,0	0h",
"line	#252525	15,-90;15,-85;15,-80;15,-75;15,-70;15,-65;15,-60;15,-55;15,-50;15,-45;15,-40;15,-35;15,-30;15,-25;15,-20;15,-15;15,-10;15,-5;15,0;15,5;15,10;15,15;15,20;15,25;15,30;15,35;15,40;15,45;15,50;15,55;15,60;15,65;15,70;15,75;15,80;15,85;15,90",
"label	#252525	15,0	1h",
"line	#808080	30,-90;30,-85;30,-80;30,-75;30,-70;30,-65;30,-60;30,-55;30,-50;30,-45;30,-40;30,-35;30,-30;30,-25;30,-20;30,-15;30,-10;30,-5;30,0;30,5;30,10;30,15;30,20;30,25;30,30;30,35;30,40;30,45;30,50;30,55;30,60;30,65;30,70;30,75;30,80;30,85;30,90",
"label	#808080	30,0	2h",
"line	#252525	45,-90;45,-85;45,-80;45,-75;45,-70;45,-65;45,-60;45,-55;45,-50;45,-45;45,-40;45,-35;45,-30;45,-25;45,-20;45,-15;45,-10;45,-5;45,0;45,5;45,10;45,15;45,20;45,25;45,30;45,35;45,40;45,45;45,50;45,55;45,60;45,65;45,70;45,75;45,80;45,85;45,90",
"label	#252525	45,0	3h",
"line	#808080	60,-90;60,-85;60,-80;60,-75;60,-70;60,-65;60,-60;60,-55;60,-50;60,-45;60,-40;60,-35;60,-30;60,-25;60,-20;60,-15;60,-10;60,-5;60,0;60,5;60,10;60,15;60,20;60,25;60,30;60,35;60,40;60,45;60,50;60,55;60,60;60,65;60,70;60,75;60,80;60,85;60,90",
"label	#808080	60,0	4h",
"line	#252525	75,-90;75,-85;75,-80;75,-75;75,-70;75,-65;75,-60;75,-55;75,-50;75,-45;75,-40;75,-35;75,-30;75,-25;75,-20;75,-15;75,-10;75,-5;75,0;75,5;75,10;75,15;75,20;75,25;75,30;75,35;75,40;75,45;75,50;75,55;75,60;75,65;75,70;75,75;75,80;75,85;75,90",
"label	#252525	75,0	5h",
"line	#808080	90,-90;90,-85;90,-80;90,-75;90,-70;90,-65;90,-60;90,-55;90,-50;90,-45;90,-40;90,-35;90,-30;90,-25;90,-20;90,-15;90,-10;90,-5;90,0;90,5;90,10;90,15;90,20;90,25;90,30;90,35;90,40;90,45;90,50;90,55;90,60;90,65;90,70;90,75;90,80;90,85;90,90",
"label	#808080	90,0	6h",
"line	#252525	105,-90;105,-85;105,-80;105,-75;105,-70;105,-65;105,-60;105,-55;105,-50;105,-45;105,-40;105,-35;105,-30;105,-25;105,-20;105,-15;105,-10;105,-5;105,0;105,5;105,10;105,15;105,20;105,25;105,30;105,35;105,40;105,45;105,50;105,55;105,60;105,65;105,70;105,75;105,80;105,85;105,90",
"label	#252525	105,0	7h",
"line	#808080	120,-90;120,-85;120,-80;120,-75;120,-70;120,-65;120,-60;120,-55;120,-50;120,-45;120,-40;120,-35;120,-30;120,-25;120,-20;120,-15;120,-10;120,-5;120,0;120,5;120,10;120,15;120,20;120,25;120,30;120,35;120,40;120,45;120,50;120,55;120,60;120,65;120,70;120,75;120,80;120,85;120,90",
"label	#808080	120,0	8h",
"line	#252525	135,-90;135,-85;135,-80;135,-75;135,-70;135,-65;135,-60;135,-55;135,-50;135,-45;135,-40;135,-35;135,-30;135,-25;135,-20;135,-15;135,-10;135,-5;135,0;135,5;135,10;135,15;135,20;135,25;135,30;135,35;135,40;135,45;135,50;135,55;135,60;135,65;135,70;135,75;135,80;135,85;135,90",
"label	#252525	135,0	9h",
"line	#808080	150,-90;150,-85;150,-80;150,-75;150,-70;150,-65;150,-60;150,-55;150,-50;150,-45;150,-40;150,-35;150,-30;150,-25;150,-20;150,-15;150,-10;150,-5;150,0;150,5;150,10;150,15;150,20;150,25;150,30;150,35;150,40;150,45;150,50;150,55;150,60;150,65;150,70;150,75;150,80;150,85;150,90",
"label	#808080	150,0	10h",
"line	#252525	165,-90;165,-85;165,-80;165,-75;165,-70;165,-65;165,-60;165,-55;165,-50;165,-45;165,-40;165,-35;165,-30;165,-25;165,-20;165,-15;165,-10;165,-5;165,0;165,5;165,10;165,15;165,20;165,25;165,30;165,35;165,40;165,45;165,50;165,55;165,60;165,65;165,70;165,75;165,80;165,85;165,90",
"label	#252525	165,0	11h",
"line	#808080	180,-90;180,-85;180,-80;180,-75;180,-70;180,-65;180,-60;180,-55;180,-50;180,-45;180,-40;180,-35;180,-30;180,-25;180,-20;180,-15;180,-10;180,-5;180,0;180,5;180,10;180,15;180,20;180,25;180,30;180,35;180,40;180,45;180,50;180,55;180,60;180,65;180,70;180,75;180,80;180,85;180,90",
"label	#808080	180,0	12h",
"line	#252525	195,-90;195,-85;195,-80;195,-75;195,-70;195,-65;195,-60;195,-55;195,-50;195,-45;195,-40;195,-35;195,-30;195,-25;195,-20;195,-15;195,-10;195,-5;195,0;195,5;195,10;195,15;195,20;195,25;195,30;195,35;195,40;195,45;195,50;195,55;195,60;195,65;195,70;195,75;195,80;195,85;195,90",
"label	#252525	195,0	13h",
"line	#808080	210,-90;210,-85;210,-80;210,-75;210,-70;210,-65;210,-60;210,-55;210,-50;210,-45;210,-40;210,-35;210,-30;210,-25;210,-20;210,-15;210,-10;210,-5;210,0;210,5;210,10;210,15;210,20;210,25;210,30;210,35;210,40;210,45;210,50;210,55;210,60;210,65;210,70;210,75;210,80;210,85;210,90",
"label	#808080	210,0	14h",
"line	#252525	225,-90;225,-85;225,-80;225,-75;225,-70;225,-65;225,-60;225,-55;225,-50;225,-45;225,-40;225,-35;225,-30;225,-25;225,-20;225,-15;225,-10;225,-5;225,0;225,5;225,10;225,15;225,20;225,25;225,30;225,35;225,40;225,45;225,50;225,55;225,60;225,65;225,70;225,75;225,80;225,85;225,90",
"label	#252525	225,0	15h",
"line	#808080	240,-90;240,-85;240,-80;240,-75;240,-70;240,-65;240,-60;240,-55;240,-50;240,-45;240,-40;240,-35;240,-30;240,-25;240,-20;240,-15;240,-10;240,-5;240,0;240,5;240,10;240,15;240,20;240,25;240,30;240,35;240,40;240,45;240,50;240,55;240,60;240,65;240,70;240,75;240,80;240,85;240,90",
"label	#808080	240,0	16h",
"line	#252525	255,-90;255,-85;255,-80;255,-75;255,-70;255,-65;255,-60;255,-55;255,-50;255,-45;255,-40;255,-35;255,-30;255,-25;255,-20;255,-15;255,-10;255,-5;255,0;255,5;255,10;255,15;255,20;255,25;255,30;255,35;255,40;255,45;255,50;255,55;255,60;255,65;255,70;255,75;255,80;255,85;255,90",
"label	#252525	255,0	17h",
"line	#808080	270,-90;270,-85;270,-80;270,-75;270,-70;270,-65;270,-60;270,-55;270,-50;270,-45;270,-40;270,-35;270,-30;270,-25;270,-20;270,-15;270,-10;270,-5;270,0;270,5;270,10;270,15;270,20;270,25;270,30;270,35;270,40;270,45;270,50;270,55;270,60;270,65;270,70;270,75;270,80;270,85;270,90",
"label	#808080	270,0	18h",
"line	#252525	285,-90;285,-85;285,-80;285,-75;285,-70;285,-65;285,-60;285,-55;285,-50;285,-45;285,-40;285,-35;285,-30;285,-25;285,-20;285,-15;285,-10;285,-5;285,0;285,5;285,10;285,15;285,20;285,25;285,30;285,35;285,40;285,45;285,50;285,55;285,60;285,65;285,70;285,75;285,80;285,85;285,90",
"label	#252525	285,0	19h",
"line	#808080	300,-90;300,-85;300,-80;300,-75;300,-70;300,-65;300,-60;300,-55;300,-50;300,-45;300,-40;300,-35;300,-30;300,-25;300,-20;300,-15;300,-10;300,-5;300,0;300,5;300,10;300,15;300,20;300,25;300,30;300,35;300,40;300,45;300,50;300,55;300,60;300,65;300,70;300,75;300,80;300,85;300,90",
"label	#808080	300,0	20h",
"line	#252525	315,-90;315,-85;315,-80;315,-75;315,-70;315,-65;315,-60;315,-55;315,-50;315,-45;315,-40;315,-35;315,-30;315,-25;315,-20;315,-15;315,-10;315,-5;315,0;315,5;315,10;315,15;315,20;315,25;315,30;315,35;315,40;315,45;315,50;315,55;315,60;315,65;315,70;315,75;315,80;315,85;315,90",
"label	#252525	315,0	21h",
"line	#808080	330,-90;330,-85;330,-80;330,-75;330,-70;330,-65;330,-60;330,-55;330,-50;330,-45;330,-40;330,-35;330,-30;330,-25;330,-20;330,-15;330,-10;330,-5;330,0;330,5;330,10;330,15;330,20;330,25;330,30;330,35;330,40;330,45;330,50;330,55;330,60;330,65;330,70;330,75;330,80;330,85;330,90",
"label	#808080	330,0	22h",
"line	#252525	345,-90;345,-85;345,-80;345,-75;345,-70;345,-65;345,-60;345,-55;345,-50;345,-45;345,-40;345,-35;345,-30;345,-25;345,-20;345,-15;345,-10;345,-5;345,0;345,5;345,10;345,15;345,20;345,25;345,30;345,35;345,40;345,45;345,50;345,55;345,60;345,65;345,70;345,75;345,80;345,85;345,90",
"label	#252525	345,0	23h",
"line	#808080	360,-90;360,-85;360,-80;360,-75;360,-70;360,-65;360,-60;360,-55;360,-50;360,-45;360,-40;360,-35;360,-30;360,-25;360,-20;360,-15;360,-10;360,-5;360,0;360,5;360,10;360,15;360,20;360,25;360,30;360,35;360,40;360,45;360,50;360,55;360,60;360,65;360,70;360,75;360,80;360,85;360,90",
"label	#808080	360,0	0h",
"line	#252525	0,-90;15,-90;30,-90;45,-90;60,-90;75,-90;90,-90;105,-90;120,-90;135,-90;150,-90;165,-90;180,-90;195,-90;210,-90;225,-90;240,-90;255,-90;270,-90;285,-90;300,-90;315,-90;330,-90;345,-90;360,-90",
"label	#252525	0,-90	-90",
"line	#252525	0,-80;15,-80;30,-80;45,-80;60,-80;75,-80;90,-80;105,-80;120,-80;135,-80;150,-80;165,-80;180,-80;195,-80;210,-80;225,-80;240,-80;255,-80;270,-80;285,-80;300,-80;315,-80;330,-80;345,-80;360,-80",
"label	#252525	0,-80	-80",
"line	#252525	0,-70;15,-70;30,-70;45,-70;60,-70;75,-70;90,-70;105,-70;120,-70;135,-70;150,-70;165,-70;180,-70;195,-70;210,-70;225,-70;240,-70;255,-70;270,-70;285,-70;300,-70;315,-70;330,-70;345,-70;360,-70",
"label	#252525	0,-70	-70",
"line	#252525	0,-60;15,-60;30,-60;45,-60;60,-60;75,-60;90,-60;105,-60;120,-60;135,-60;150,-60;165,-60;180,-60;195,-60;210,-60;225,-60;240,-60;255,-60;270,-60;285,-60;300,-60;315,-60;330,-60;345,-60;360,-60",
"label	#252525	0,-60	-60",
"line	#252525	0,-50;15,-50;30,-50;45,-50;60,-50;75,-50;90,-50;105,-50;120,-50;135,-50;150,-50;165,-50;180,-50;195,-50;210,-50;225,-50;240,-50;255,-50;270,-50;285,-50;300,-50;315,-50;330,-50;345,-50;360,-50",
"label	#252525	0,-50	-50",
"line	#252525	0,-40;15,-40;30,-40;45,-40;60,-40;75,-40;90,-40;105,-40;120,-40;135,-40;150,-40;165,-40;180,-40;195,-40;210,-40;225,-40;240,-40;255,-40;270,-40;285,-40;300,-40;315,-40;330,-40;345,-40;360,-40",
"label	#252525	0,-40	-40",
"line	#FFFFFF	0,-30;15,-30;30,-30;45,-30;60,-30;75,-30;90,-30;105,-30;120,-30;135,-30;150,-30;165,-30;180,-30;195,-30;210,-30;225,-30;240,-30;255,-30;270,-30;285,-30;300,-30;315,-30;330,-30;345,-30;360,-30",
"label	#FFFFFF	0,-30	-30",
"line	#252525	0,-20;15,-20;30,-20;45,-20;60,-20;75,-20;90,-20;105,-20;120,-20;135,-20;150,-20;165,-20;180,-20;195,-20;210,-20;225,-20;240,-20;255,-20;270,-20;285,-20;300,-20;315,-20;330,-20;345,-20;360,-20",
"label	#252525	0,-20	-20",
"line	#252525	0,-10;15,-10;30,-10;45,-10;60,-10;75,-10;90,-10;105,-10;120,-10;135,-10;150,-10;165,-10;180,-10;195,-10;210,-10;225,-10;240,-10;255,-10;270,-10;285,-10;300,-10;315,-10;330,-10;345,-10;360,-10",
"label	#252525	0,-10	-10",
"line	#FFFFFF	0,0;15,0;30,0;45,0;60,0;75,0;90,0;105,0;120,0;135,0;150,0;165,0;180,0;195,0;210,0;225,0;240,0;255,0;270,0;285,0;300,0;315,0;330,0;345,0;360,0",
"line	#252525	0,10;15,10;30,10;45,10;60,10;75,10;90,10;105,10;120,10;135,10;150,10;165,10;180,10;195,10;210,10;225,10;240,10;255,10;270,10;285,10;300,10;315,10;330,10;345,10;360,10",
"label	#252525	0,10	+10",
"line	#252525	0,20;15,20;30,20;45,20;60,20;75,20;90,20;105,20;120,20;135,20;150,20;165,20;180,20;195,20;210,20;225,20;240,20;255,20;270,20;285,20;300,20;315,20;330,20;345,20;360,20",
"label	#252525	0,20	+20",
"line	#252525	0,30;15,30;30,30;45,30;60,30;75,30;90,30;105,30;120,30;135,30;150,30;165,30;180,30;195,30;210,30;225,30;240,30;255,30;270,30;285,30;300,30;315,30;330,30;345,30;360,30",
"label	#252525	0,30	+30",
"line	#252525	0,40;15,40;30,40;45,40;60,40;75,40;90,40;105,40;120,40;135,40;150,40;165,40;180,40;195,40;210,40;225,40;240,40;255,40;270,40;285,40;300,40;315,40;330,40;345,40;360,40",
"label	#252525	0,40	+40",
"line	#252525	0,50;15,50;30,50;45,50;60,50;75,50;90,50;105,50;120,50;135,50;150,50;165,50;180,50;195,50;210,50;225,50;240,50;255,50;270,50;285,50;300,50;315,50;330,50;345,50;360,50",
"label	#252525	0,50	+50",
"line	#252525	0,60;15,60;30,60;45,60;60,60;75,60;90,60;105,60;120,60;135,60;150,60;165,60;180,60;195,60;210,60;225,60;240,60;255,60;270,60;285,60;300,60;315,60;330,60;345,60;360,60",
"label	#252525	0,60	+60",
"line	#252525	0,70;15,70;30,70;45,70;60,70;75,70;90,70;105,70;120,70;135,70;150,70;165,70;180,70;195,70;210,70;225,70;240,70;255,70;270,70;285,70;300,70;315,70;330,70;345,70;360,70",
"label	#252525	0,70	+70",
"line	#252525	0,80;15,80;30,80;45,80;60,80;75,80;90,80;105,80;120,80;135,80;150,80;165,80;180,80;195,80;210,80;225,80;240,80;255,80;270,80;285,80;300,80;315,80;330,80;345,80;360,80",
"label	#252525	0,80	+80",
"line	#252525	0,90;15,90;30,90;45,90;60,90;75,90;90,90;105,90;120,90;135,90;150,90;165,90;180,90;195,90;210,90;225,90;240,90;255,90;270,90;285,90;300,90;315,90;330,90;345,90;360,90",
"label	#252525	0,90	+90",
"line	#00FFFF	6.45,62.73;15.20,62.85;23.87,62.44;32.15,61.51;39.84,60.10;46.81,58.30;53.05,56.15;58.59,53.72;63.50,51.07;67.85,48.23;71.74,45.25;75.24,42.14;78.40,38.94;81.28,35.67;83.94,32.33;86.40,28.94;88.71,25.50;90.89,22.03;92.97,18.54;94.96,15.02;96.88,11.49;98.76,7.94;100.61,4.39;102.43,0.83;104.26,-2.73;106.10,-6.29;107.96,-9.84;109.86,-13.38;111.82,-16.90;113.85,-20.41;115.98,-23.89;118.22,-27.34;120.61,-30.75;123.17,-34.12;125.94,-37.43;128.97,-40.66;132.30,-43.81;136.00,-46.86;140.13,-49.77;144.77,-52.51;150.00,-55.05;155.91,-57.34;162.54,-59.31;169.90,-60.91;177.93,-62.07;186.45,-62.73;195.20,-62.85;203.87,-62.44;212.15,-61.51;219.84,-60.10;226.81,-58.30;233.05,-56.15;238.59,-53.72;243.50,-51.07;247.85,-48.23;251.74,-45.25;255.24,-42.14;258.40,-38.94;261.28,-35.67;263.94,-32.33;266.40,-28.94;268.71,-25.50;270.89,-22.03;272.97,-18.54;274.96,-15.02;276.88,-11.49;278.76,-7.94;280.61,-4.39;282.43,-0.83;284.26,2.73;286.10,6.29;287.96,9.84;289.86,13.38;291.82,16.90;293.85,20.41;295.98,23.89;298.22,27.34;300.61,30.75;303.17,34.12;305.94,37.43;308.97,40.66;312.30,43.81;316.00,46.86;320.13,49.77;324.77,52.51;330.00,55.05;335.91,57.34;342.54,59.31;349.90,60.91;357.93,62.07",
"line	#800000	0.00,-0.04;4.49,1.94;9.09,3.92;13.71,5.87;18.36,7.78;23.06,9.64;27.80,11.43;32.61,13.15;37.48,14.78;42.42,16.30;47.44,17.71;52.54,18.99;57.70,20.13;62.94,21.11;68.24,21.93;73.60,22.58;79.00,23.05;84.43,23.34;89.88,23.44;95.33,23.35;100.76,23.07;106.16,22.61;111.52,21.96;116.82,21.15;122.06,20.17;127.24,19.04;132.33,17.77;137.35,16.37;142.30,14.85;147.17,13.23;151.98,11.51;156.73,9.72;161.43,7.86;166.08,5.95;170.71,4.00;175.31,2.03;179.90,0.04;184.49,-1.94;189.09,-3.92;193.71,-5.87;198.36,-7.78;203.06,-9.64;207.80,-11.43;212.61,-13.15;217.48,-14.78;222.42,-16.30;227.44,-17.71;232.54,-18.99;237.70,-20.13;242.94,-21.11;248.24,-21.93;253.60,-22.58;259.00,-23.05;264.43,-23.34;269.88,-23.44;275.33,-23.35;280.76,-23.07;286.16,-22.61;291.52,-21.96;296.82,-21.15;302.06,-20.17;307.24,-19.04;312.33,-17.77;317.35,-16.37;322.30,-14.85;327.17,-13.23;331.98,-11.51;336.73,-9.72;341.43,-7.86;346.08,-5.95;350.71,-4.00;355.31,-2.03;359.90,-0.04"
];



