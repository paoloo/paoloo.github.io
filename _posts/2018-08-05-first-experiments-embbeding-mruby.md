---
title: First experiments embedding mruby
date: 2018-08-05T09:52:32+00:00
author: paolo
layout: post
permalink: /2018/08/05/first-experiments-embbeding-mruby/
categories:
  - en-US
tags:
  - embedded
  - mruby
  - ruby
---
The philosophy of mruby is to be a lightweight implementation of the Ruby ISO standard with <a href="https://github.com/mruby/mruby/blob/master/doc/limitations.md" rel="noopener" target="_blank">some limitations</a>. Different from the usual Ruby runtime, specially MRI, mruby, using RiteVM, is designed to be a modular and embedded version of ruby. It&#8217;s pretty small and fast, actually, and easily extended with C. A good OO auternative to Lua for embbedded, although lua is way faster today.

code integrations, is easy as hell

clone mruby repo

<pre class="brush: bash; title: ; notranslate" title="">$ cd ~/Workspace/embbeded
$ git clone https://github.com/mruby/mruby.git
</pre>

Then install it as explained <a href="https://github.com/mruby/mruby/blob/master/doc/guides/compile.md" rel="noopener" target="_blank">here</a>

Now, let&#8217;s test with a simple inline code (**01.c**):

<pre class="brush: cpp; title: ; notranslate" title="">#include &lt;mruby.h&gt;
#include &lt;mruby/compile.h&gt;

int
main(void)
{
  mrb_state *mrb = mrb_open();
  if (!mrb) { /* handle error */ }
  // mrb_load_nstring() for strings without null terminator or with known length
  mrb_load_string(mrb, "puts 'hello world'");
  mrb_close(mrb);
  return 0;
}
</pre>

compile it with:

<pre class="brush: bash; title: ; notranslate" title="">$ gcc -std=c99 -Imruby/include 01.c -o aaa mruby/build/host/lib/libmruby.a -lm
</pre>

as expected, the string &#8220;Hello world&#8221; will be printed. Now, to embbed a small ruby file, I tested this small C code(**02.c**):

<pre class="brush: cpp; title: ; notranslate" title="">#include &lt;stdio.h&gt;
#include &lt;mruby.h&gt;
#include &lt;mruby/dump.h&gt;

static mrb_value mrb_greet(mrb_state *mrb, mrb_value self) {
  printf("Hey ho mofo!\n");
  return mrb_nil_value();
}

mrb_value mrb_boo(mrb_state* mrb, mrb_value self){
	mrb_int i = 0; // retrieve one arg of type int (see mruby.h)
	mrb_get_args(mrb, "i", &i);
	printf("iiiiiha %d hae hae\n", (int)i);
	return mrb_nil_value();
}

int main(void){
  mrb_state *mrb = mrb_open();
  if (!mrb) { /* handle error */ }
  mrb_define_method(mrb, mrb-&gt;object_class, "greet!", mrb_greet, MRB_ARGS_NONE());
  mrb_define_method(mrb, mrb-&gt;object_class, "boo!", mrb_boo, MRB_ARGS_REQ(1));
  FILE *fp = fopen("testa.mrb", "r");
  mrb_load_irep_file(mrb, fp);
  mrb_close(mrb);
  return 0;
}
</pre>

There are two importante things here. First, I had to add **<mruby/dump.h>** for `mrb_load_irep_file` and remove `<mruby/compile.h>` to decrease generated binary file. Second, we have to export any method that we define in C with `mrb_define_method`.

Now for the **testa.rb** we have

<pre class="brush: ruby; title: ; notranslate" title="">puts 'helloooo worldi'
greet!
puts 'here we go'
boo! 12
puts 'end'
</pre>

After that, generate it&#8217;s bytecode with:

<pre class="brush: bash; title: ; notranslate" title="">$ cd ~/Workspace/embbeded
$ mruby/bin/mrbc testa.rb
</pre>

which will generate \`testa.mrb\`.

<pre class="brush: plain; title: ; notranslate" title="">$ cd ~/Workspace/embbeded
$ gcc -std=c99 -Imruby/include 02.c -o aaa mruby/build/host/lib/libmruby.a -lm
$ ./aaa
helloooo worldi
Hey ho mofo!
here we go
iiiiiha 12 hae hae
end
</pre>

To show that this works.

Also, as we are junt reading from a file, we could store it within an array. That would work as well.  
just include `<mruby/irep.h>` then create an `anyarray[] = { 0x45, 0x54..., 0x08 };` and, finally, call with `mrb_load_irep(mrb, anyarray);`

mruby is easy to integrate with anything and is getting faster everyday. So play with it a little. Enjoy.