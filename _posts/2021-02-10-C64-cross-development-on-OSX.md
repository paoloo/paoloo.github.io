---
title: C64 cross development on OSX
date: 2021-02-10T22:00:43+00:00
author: paolo
layout: post
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

But if you rather have vscode, do this:

install vscode's [VS64](https://marketplace.visualstudio.com/items?itemName=rosc.vs64) with `brew install cc65 acme vice`
then edit `/opt/homebrew/Cellar/vice/3.9/share/vice/C64/gtk3_sym_uk.vkm`
if, like me, you have a british keyboard, add on line 297: `dead_doubleacute 7 3 1  # "`

that's it! Your vscode is ready to go!

type **cmd+shift+P** and select `VS64: Create ACME Project` then type

```
*=$0801
!byte $0c,$08,$b5,$07,$9e,$20,$32,$30,$36,$32,$00,$00,$00 
; BASIC stub "SYS 2062"
; -----------------------------------------------------------
; addr   value(s)         description
; ----   --------------   -----------------------------------
; 0801   0c 08            BASIC line link (ptr to next line)
; 0803   b5 07            BASIC line number (2061)
; 0805   9e               BASIC token for SYS
; 0806   20               space character
; 0807   32 30 36 32      ASCII for "2062"
; 080b   00               end of BASIC line
; 080c   00               end of BASIC program

jmp main

.hellotext
    !scr "putaria maluca",0
    !set ofs = 13

main:
       ; black screen border
       lda #$00
       sta $d020
       ; start
       ldy #0

loop:  lda .hellotext,y
       beq done
       sta $400+ofs,y
       lda #1
       sta $d800+ofs,y
       iny
       jmp loop

done:  rts
```
press **fn+F5** to compile and run automatically on vice.

AND THAT'S IT!

Enjoy and do great things
