---
id: 629
title: C64 cross development on OSX
date: 2021-02-10T22:00:43+00:00
author: paolo
layout: post
guid: http://paolo.zone/blog/?p=629
permalink: /2021/02/10/C64-cross-development-on-OSX/
categories:
  - en-US
tags:
  - retrocomputing
  - C64
  - OSX
---

OSX has become a really good platform for development, after all there is a (deformed) BSD under the hood and Apple usually play all the correct cards when design interfaces. (Usually but sometimes the result sucks haha)
Anyway, with iTerm2+bash there is no limitation to your criativity.

To create a clean, simple and fast Commodore 64 cross compiling environment on OSX, I decided to use [Turbo Macro Pro](http://turbo.style64.org), this amazing assembler that can also be used on the machine itself. As a code verifier, I used the [petxd](https://style64.org/petxd), a xxd-like hex dumper that outputs using a Unicode/PETSCII representation, and, finnaly, the best C64 emulator: [VICE](https://vice-emu.sourceforge.io).

This is available on github [here](https://github.com/paoloo/C64asmOnOSX) ( I accept PRs )

Everything is integrated with the Makefile so that build and test is easy and fast. There are the minumun amount of files to make things simple to understant.
```
.
├── Makefile
├── README.md
├── bin
│   ├── petxd
│   └── tmpx
├── lib
├── release
└── src
    └── main.asm

4 directories, 5 files
```
An usage example:
```
$ make
TMPx v1.1.0 [r1141; 2015-08-13 11:11:32]; (c) Style 2008-2015

	Assembled: $1000 - $101f / Writing 34/$0022 bytes incl load address
1000: 20 12 10 60 50 55 54 41 
1008: 52 49 41 20 4d 41 4c 55 
1010: 43 41 a2 00 bd 04 10 20 
1018: d2 ff e8 e0 0e d0 f5 60 
Done
```

Enjoy and do great things
