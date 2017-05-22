---
title: My first steps into Ruby and OpenCV(on OSX)
date: 2017-05-22T14:38:34+00:00
author: paolo
layout: post
permalink: /2017/05/22/my-first-steps-into-ruby-and-opencvon-osx/
geo_public:
  - "0"
categories:
  - en-US
tags:
  - comp
  - opencv
  - osx
  - ruby
---
I was writing some robotic code that will run on a mac mini, so I tryied on my macbook for the first time, ruby binding to opencv. It was a weird experience lol.

First, to install _OpenCV_, brew do the job:

<pre class="brush: bash; title: ; notranslate" title="">$ brew tap homebrew/science
$ brew install opencv
</pre>

after a while we see that instalation goes flawlessly:  
**/usr/local/Cellar/opencv/2.4.13.2: 278 files, 35.6MB**  
and we have current version: **2.4.13.2**. That said, now install ruby gem:

<pre class="brush: bash; title: ; notranslate" title="">$ gem install ruby-opencv -- --with-opencv-lib=/usr/local/Cellar/opencv/2.4.13.2/lib \
                             --with-opencv-include=/usr/local/Cellar/opencv/2.4.13.2/include/opencv \
                             --with-opencv-include=/usr/local/Cellar/opencv/2.4.13.2/include/opencv2

Fetching: ruby-opencv-0.0.18.gem (100%)
Building native extensions with: '--with-opencv-lib=/usr/local/Cellar/opencv/2.4.13.2/lib --with-opencv-include=/usr/local/Cellar/opencv/2.4.13.2/include/opencv --with-opencv-include=/usr/local/Cellar/opencv/2.4.13.2/include/opencv2'
This could take a while...
Successfully installed ruby-opencv-0.0.18
Parsing documentation for ruby-opencv-0.0.18
Installing ri documentation for ruby-opencv-0.0.18
Done installing documentation for ruby-opencv after 7 seconds
1 gem installed
</pre>

after that, time to code.

My first try, obviously, is to use HAAR cascade classifier to look for faces.

<pre class="brush: ruby; title: ; notranslate" title="">require "rubygems"
require "opencv"
include OpenCV

window = GUI::Window.new(&quot;grab da face!&quot;)
camera = CvCapture.open
detector = CvHaarClassifierCascade::load('./haarcascade_frontalface_alt.xml')
loop {
  image = camera.query
  detector.detect_objects(image).each { |rect|
    image.rectangle! rect.top_left, rect.bottom_right, :color =&gt; CvColor::Blue
  }
  window.show image
  break if GUI::wait_key(100)
}
</pre>

It didn&#8217;t worked as ruby-opencv currently supports only older type format of trained data xml. To solve that, I grabed older version of **haarcascade\_frontalface\_alt.xml** from https://raw.githubusercontent.com/Itseez/opencv/2.4.10.4/data/haarcascades/haarcascade\_frontalface\_alt.xml and it worked as expected.  
Sometimes, OSX Facetime camera stop working, but is easy to fix, just run

<pre class="brush: bash; title: ; notranslate" title="">sudo killall VDCAssistant
</pre>

wait a little and voilá.

In the end, was a different experience, it worked but was way too slow. I&#8217;ll try to tweak a little but python version are way faster and I believe I&#8217;ll keep using it.