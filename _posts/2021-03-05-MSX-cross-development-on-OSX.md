---
title: MSX cross development on OSX
date: 2021-03-05T22:00:43+00:00
author: paolo
layout: post
permalink: /2021/03/05/MSX-cross-development-on-OSX/
categories:
  - en-US
tags:
  - retrocomputing
  - MSX
  - OSX
---

Just like a did for [C64](blog/2021/02/10/C64-cross-development-on-OSX/), I created a simple development environment based on [avelino's](http://msx.avelinoherrera.com/index_en.html) files. The result is a little more complex than the C64 version but for C programming(and ASM as well).
For that, I decided to use [SDCC](http://sdcc.sourceforge.net/) + [hex2bin](http://hex2bin.sourceforge.net/) to create the binaries. Everything is managed by a makefile and this is primarily focused on MSXDOS application development. The code is available [here](https://github.com/paoloo/msxdos-app).

But I ended up creating another repository, a general one, that can create ROMs, BINs and MSX-DOS applications. This is a heavily modified version of Danilo's template used on his great MSX development workshop (videos (in pt-br) [here](https://www.youtube.com/channel/UC-QPKENS07P_5q-7a7ps2HA/videos) and original template, for visual studio [here](https://github.com/paoloo/sdcc-msx-template). ). My repository is [here](https://github.com/paoloo/sdcc-msx-template) and there are some explanations on how to use it on the README.md
