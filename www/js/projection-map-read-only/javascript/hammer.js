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


if (typeof HammerProjection == "undefined") {
    var HammerProjection = function() { }

    //
    // Hammer projection: http://en.wikipedia.org/wiki/Hammer_projection
    // Javascript functions: http://www.math.rutgers.edu/~erowland/playground.html
    //
    HammerProjection.prototype.inverse_project = function(x, y, out) {
      x = -x;
      y = -y;
      var z2 = 1 - (x * x + 4 * y * y) / 16;
      if (z2 < 0) return null;
      var z = Math.sqrt(z2);
      out.ra = 2 * Math.atan(0.5 * z * x / (2 * z2 - 1));
      out.dec = Math.asin(z * y);
      return out;
    }

    HammerProjection.prototype.project = function(lplam, lpphi, out) {
      var cos_phi = Math.cos(lpphi);
      var lplam2 = lplam / 2;

      var t = 1 + cos_phi * Math.cos(lplam2);

      // Avoid divide by 0 error (singularity case). E.g., when (lam = 2PI, phi = 0).
      // Since 2PI =~ 0, can get that x = y = 0 in this case.
      if (t == 0) { out.x = out.y = 0; return out; }

      var d = - Math.SQRT2 / Math.sqrt(t);
      out.x = 2 * d * cos_phi * Math.sin(lplam2);
      out.y = d * Math.sin(lpphi);
      return out;
    }
}


if(typeof SinusoidalProjection=="undefined") {
    var SinusoidalProjection = function() { }

    //
    // http://en.wikipedia.org/wiki/Sinusoidal_projection
    // http://mathworld.wolfram.com/SinusoidalProjection.html
    // Let central meridian lam0 = 0.
    //
    SinusoidalProjection.prototype.inverse_project = function(x, y, out) {
      x = -x;
      y = -y;

      var d = Math.cos(y);
      if (d == 0) { out.ra = 0; } // y = +- PI/2, it converges to 1 point.
      else { out.ra = x / d; }

      out.dec = y;
      return out;
    }

    SinusoidalProjection.prototype.project = function(lplam, lpphi, out) {
      out.x = - lplam * Math.cos(lpphi); // let lam0 = 0.
      out.y = - lpphi;
      return out;
    }
}


if(typeof MollweideProjection=="undefined") {
    var MollweideProjection = function() { }

    //
    // http://mathworld.wolfram.com/MollweideProjection.html
    // Let lam0 = 0.
    //
    MollweideProjection.prototype.inverse_project = function(x, y, out) {
      x = -x;
      y = -y;

      var theta = Math.asin(y / Math.SQRT2);
      if (Math.cos(theta) == 0) { // theta = +- PI/2. (x,y) is north/south pole.
          out.ra = 0;
          out.dec = (y > 0) ? Math.PI/2 : - Math.PI/2;
          return out;
      }
      out.ra = 0 + 0.5 * Math.PI * x / (Math.SQRT2 * Math.cos(theta));
      out.dec = Math.asin( (2 * theta + Math.sin(2 * theta)) / Math.PI ); 

      return out;
    } 
    

    MollweideProjection.prototype.project = function(lplam, lpphi, out) {
      var theta1, theta, theta2;

      if (2 * Math.abs(lpphi) == Math.PI) { 
        out.x = 0;
        out.y = (lpphi > 0) ? - Math.SQRT2 : Math.SQRT2;
        return out;
      }

      // else, get theta by newton's method.
      theta1 = lpphi;
      do {
        theta = theta1;
        theta2 = 2 * theta;
        theta1 = theta - (theta2 + Math.sin(theta2) - Math.PI * Math.sin(lpphi))/(2 + 2 * Math.cos(theta2));
      } while  ( Math.abs(theta1 - theta) > 0.001 );

      out.x = - 2 * Math.SQRT2 * (lplam - 0) * Math.cos(theta) / Math.PI;
      out.y = - Math.SQRT2 * Math.sin(theta);

      return out;
    }
}     


if(typeof FlatProjection=="undefined") {
    var FlatProjection = function() { }

    FlatProjection.prototype.inverse_project = function(x, y, out) {
      out.ra = -x;
      out.dec = -y;
      return out;
    }
    
    FlatProjection.prototype.project = function(lplam, lpphi, out) {
      out.x = - lplam;
      out.y = - lpphi;
      return out;
    }
}


if(typeof NorthPoleProjection=="undefined") {
    var NorthPoleProjection = function() {
      this.ClassName = 'NorthPoleProjection';
    }

    //
    // Azimuthal Equidistant Projection:
    // http://mathworld.wolfram.com/AzimuthalEquidistantProjection.html
    // North Pole: lam0 = 0, phi1 = - Math.PI/2
    //
    NorthPoleProjection.prototype.inverse_project = function(x, y, out) {
      var c = Math.sqrt(x * x + y * y);
      out.dec =  Math.asin(Math.cos(c));
      if (y == 0) { out.ra = (x > 0) ? - Math.PI/2 : Math.PI/2; }
      else { out.ra = - Math.atan(x / y); }

      if (y < 0) { out.ra -= Math.PI; }

      return out;
    }

    NorthPoleProjection.prototype.project = function(lplam, lpphi, out) {
      if (lpphi < 0) { return null; } // for north sphere, phi in [0, 90].

      lplam = - lplam;
      lpphi = - lpphi;

      var c = Math.acos(- Math.sin(lpphi));
      var k;
      if (Math.sin(c) == 0) { k = 1; }
      else { k = c / Math.sin(c); }
      out.x = k * Math.cos(lpphi) * Math.sin(lplam);
      out.y = k * (Math.cos(lpphi) * Math.cos(lplam));

      return out;
    }
}


if(typeof SouthPoleProjection=="undefined") {
    var SouthPoleProjection = function() {
      this.ClassName = 'SouthPoleProjection';
    }

    //
    // Azimuthal Equidistant Projection:
    // http://mathworld.wolfram.com/AzimuthalEquidistantProjection.html
    // South Pole: lam0 = 0, phi1 = Math.PI/2
    //
    SouthPoleProjection.prototype.inverse_project = function(x, y, out) {
      var c = Math.sqrt(x * x + y * y);

      out.dec = Math.asin(- Math.cos(c));
      if (y == 0) { out.ra = (x > 0) ? Math.PI/2 : - Math.PI/2; }
      else { out.ra =  Math.atan(x / y); }

      if (y > 0) { out.ra -= Math.PI; }

      return out;
    }

    SouthPoleProjection.prototype.project = function(lplam, lpphi, out) {
      if (lpphi > 0) { return null; } // for south sphere, phi in [-90, 0].

      lplam = - lplam;
      lpphi = - lpphi;

      var c = Math.acos(Math.sin(lpphi));
      var k;
      if (Math.sin(c) == 0) { k = 1; }
      else { k = c / Math.sin(c); }
      out.x = k * Math.cos(lpphi) * Math.sin(lplam);
      out.y = k * (- Math.cos(lpphi) * Math.cos(lplam));

      return out;
    }
}


if(typeof AzimuthalEquiDistanceProjection=="undefined") {
    var AzimuthalEquiDistanceProjection = function() {
      this.PI_Half = Math.PI / 2;
      this.lam0 = 0; //- Math.PI / 2;
      this.phi1 = - this.PI_Half;
    }

    //
    // Azimuthal Equidistant Projection:
    // http://mathworld.wolfram.com/AzimuthalEquidistantProjection.html
    // Note this implementation is not done yet. There may exist bugs. 5/10/2011.
    //
    AzimuthalEquiDistanceProjection.prototype.inverse_project = function(x, y, out) {
      var c = Math.sqrt(x * x + y * y);
      if (c == 0) { out.x = out.y = 0.0; return out; }

      out.dec = Math.asin(Math.cos(c) * Math.sin(this.phi1) + y * Math.sin(c) * Math.cos(this.phi1) / c);

      if (this.phi1 == this.PI_Half) { out.ra = this.lam0 + Math.atan(- x / y); }
      else if (this.phi1 == - this.PI_Half) { out.ra = this.lam0 + Math.atan(x / y); }
      else { out.ra = this.lam0 + Math.atan(x * Math.sin(c) / 
                      (c * Math.cos(this.phi1) * Math.cos(c) - y * Math.sin(this.phi1) * Math.sin(c))); }

      out.ra -= out.ra;
      out.dec -= out.dec;

      return out;
    }
    
    AzimuthalEquiDistanceProjection.prototype.project = function(lplam, lpphi, out) {
      lplam = - lplam;
      lpphi = - lpphi;

      //if (Math.abs(lplam - lam0) > this.PI_Half) { return null; } 
      if (Math.abs(lpphi - this.phi1) > this.PI_Half) { return null; }
      var c = Math.acos(Math.sin(this.phi1) * Math.sin(lpphi) + 
                        Math.cos(this.phi1) * Math.cos(lpphi) * Math.cos(lplam - this.lam0));
      var k;
      if (Math.sin(c) == 0) { k = 1; } 
      else { k = c / Math.sin(c); }
      out.x = k * Math.cos(lpphi) * Math.sin(lplam - this.lam0);
      out.y = k * (Math.cos(this.phi1) * Math.sin(lpphi) - 
                   Math.sin(this.phi1) * Math.cos(lpphi) * Math.cos(lplam - this.lam0));

      return out;
    }
}


