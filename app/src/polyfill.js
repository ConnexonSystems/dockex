// The MIT License (MIT)
//
// Copyright (c) 2018 creativeLabs Łukasz Holeczek.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

/*
* required polyfills
*/
import "core-js";
import 'core-js/features/set/map';

/** IE9, IE10 and IE11 requires all of the following polyfills. **/
// import 'core-js/es6/symbol'
// import 'core-js/es6/object'
// import 'core-js/es6/function'
// import 'core-js/es6/parse-int'
// import 'core-js/es6/parse-float'
// import 'core-js/es6/number'
// import 'core-js/es6/math'
// import 'core-js/es6/string'
// import 'core-js/es6/date'
// import 'core-js/es6/array'
// import 'core-js/es6/regexp'
// import 'core-js/es6/map'
// import 'core-js/es6/weak-map'
// import 'core-js/es6/set'
// import 'core-js/es7/object'

/** IE10 and IE11 requires the following for the Reflect API. */
// import 'core-js/es6/reflect'

/** Evergreen browsers require these. **/
// Used for reflect-metadata in JIT. If you use AOT (and only Angular decorators), you can remove.
// import 'core-js/es7/reflect'

// CustomEvent() constructor functionality in IE9, IE10, IE11
(function () {

  if ( typeof window.CustomEvent === "function" ) return false

  function CustomEvent ( event, params ) {
    params = params || { bubbles: false, cancelable: false, detail: undefined }
    var evt = document.createEvent( 'CustomEvent' )
    evt.initCustomEvent( event, params.bubbles, params.cancelable, params.detail )
    return evt
  }

  CustomEvent.prototype = window.Event.prototype

  window.CustomEvent = CustomEvent
})()
