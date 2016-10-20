---
title: Accessing Go compiled applications through FFI
date: 2016-10-20T23:52:43+00:00
author: paolo
layout: post
permalink: /2016/10/20/accessing-go-compiled-applications-through-ffi/
geo_public:
  - "0"
categories:
  - en-US
tags:
  - comp
  - Go
---
I finally started to create some useful Go code and, just like some previous posts(in pt-BR, ) where I integrated python, lua and C, I would love to use them with old python code instead of C/C++. For that, I had to generate a shared library. The process is easy as expected, requiring only the import of library &#8220;C&#8221; and a comment before function definition, exporting the function name, as following examples.

<pre class="brush: plain; title: ; notranslate" title="">package main

import "C"

//export ModXY
func ModXY(x int) int {
        return x * 2
}

func main() {}
</pre>

Now, let&#8217;s compile it to generate a shared lib:

<pre class="brush: plain; title: ; notranslate" title="">$ go build -o libmod.so -buildmode=c-shared
</pre>

This results on two files, libmod.so and libmod.h where the first one is a shared library itself and the second one is the headers to include Go types into a C application. More on this soon. First let&#8217;s check libmod.so

<pre class="brush: plain; title: ; notranslate" title="">$ file libmod.so
libmod.so: Mach-O 64-bit dynamically linked shared library x86_64
</pre>

Nice, as expected on OSX. Now let&#8217;s try to import it with python ctypes!

<pre class="brush: plain; title: ; notranslate" title="">Python 2.7.12 (default, Sep 28 2016, 18:41:32)
[GCC 4.2.1 Compatible Apple LLVM 8.0.0 (clang-800.0.38)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
&gt;&gt;&gt; import ctypes
&gt;&gt;&gt; lib = ctypes.CDLL('libmod.so')
&gt;&gt;&gt; lib.ModXY(13,2)
1
</pre>

It worked like a charm! It is, actually, pretty easy to deal with. Now let&#8217;s find out the raison d&#8217;etre of this .h file. If, for some crazy reason, you need to embbed Go code inside a C file, simply include the .h and use the functions normally, as the following example:

<pre class="brush: cpp; title: ; notranslate" title="">#include &lt;stdio.h&gt;
#include "libmod.h"

int main(void){
  printf("the rest of division of 13 per 2 is %d", (int)ModXY(13,2));
  return 0;
}
</pre>

then, compile it with:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -o purexecutable testlib.c libmod.so 
</pre>

and

<pre class="brush: plain; title: ; notranslate" title="">$ file purexecutable
purexecutable: Mach-O 64-bit executable x86_64
$ ./purexecutable
the rest of division of 13 per 2 is 1
</pre>

Yey! Again, simple and efficient. The design documentation of this feature may be found here( http://golang.org/s/execmodes ). That&#8217;s all