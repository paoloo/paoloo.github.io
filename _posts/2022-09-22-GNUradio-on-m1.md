---
title: GNUradio on m1
date: 2022-09-22T22:00:43+00:00
author: paolo
layout: post
permalink: /2022/09/22/GNUradio-on-m1/
categories:
  - en-US
tags:
  - RF
  - ham radio
  - osx
---

GNUrdio is awesome. It's the perfect starting point to anything RF-related, easy to extend and easily replicable. BUT, it sucks to install by itself!!!!!! This is true on "old school" intel-based windows/linux, but it's even crazier on osx/m1(arm64).

but but but but we, ofc, have [conda](https://anaconda.org/anaconda/conda) to help us.

to install gburadio is so ridiculously easy with conda:
```
$ conda create -n rf
$ conda activate rf
$ conda config --env --add channels conda-forge
$ conda config --env --set channel_priority strict
$ conda install gnuradio python=3.8
$ conda upgrade --all
$ conda install soapysdr-module-rtlsdr
$ conda install soapysdr-module-hackrf
```
I used python 3.8(not the most updated one, I know) because it's the best version that supports conda nowadays.

ah! and do not forget to add support to that cheap RTL-SDR!
```
$ conda install rtl-sdr
```
And that's it! with a little bit of point-and-click, you can create something like a FM radio receiver:

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2022/09/gnuradio-fmrx.png" alt="" class="wp-image-625" /><figcaption>a FM radio receiver</figcaption></figure>

That's it!
