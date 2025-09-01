---
title: PikachuProgramming Language
date: 2025-09-01T22:00:43+00:00
author: paolo
layout: post
permalink: /2025/09/01/pikachu-programming/
categories:
  - en-US
tags:
  - comp
  - go
  - python
---

what if pikachu could write code?

I designed pikaSpeak using basic-like structure but with pikachu phrases for all the pikachu coders out there!

The basic language layout can be seen on the BNF but it's something like:

| BASIC   | pikaSpeak |
|---------|-----------|
| read    | pi?       |
| print   | pi!       |
| if      | pika?     |
| else    | pika      |
| endif   | pika!     |
| for     | pikapi    |
| while   | pikapi?   |
| to      | chu       |
| break   | chu!      |
| next    | pikapi!   |
| func    | pikapika? |
| endfunc | pikapika! |
| return  | pikachu   |
| exit    | pikachu!  |

The whole code is available at [https://github.com/paoloo/pikaSpeak](https://github.com/paoloo/pikaSpeak)

to make it run, I decided to go with a golang-based VM.

Overall, it's a complete exercise on **compillers** (front and backend) as well as **VM creation and interpretation**. 

The whole thing is in brazilian portuguese but easily translated. Enjoy!
