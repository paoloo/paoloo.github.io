---
title: First Radio Experiments on OSX
date: 2022-10-02T22:00:43+00:00
author: paolo
layout: post
permalink: /2022/10/02/first-radio-experiments-on-osx/
categories:
  - en-US
tags:
  - RF
  - ham radio
  - osx
---

After installing GNUradio, there are some other tools to properly start experimenting on RF. One of the more versatiles ones is: [fldigi](https://sourceforge.net/projects/fldigi/)!

I installed it with [homebrew](https://brew.sh) and it's pretty straightforward: `brew install fldigi`

We also need a hardware to connect a standard transceiver to the computer. Usually an USB sound card+USB-to-serial is enough but we have better options like [digirig](https://digirig.net)!

I did try to attach a baofeng uv5r to fldigi using digirig. The configuration is pretty simple: Select digirig usb sound card for rx and tx and, on Rig Control/Hardware PTT, set "use a separated serial", select the device and use RTS as the trigger.

<figure class="wp-block-image"><img src="{{ site.baseurl }}/uploads/2022/10/baofeng_digirig.png" alt="" class="wp-image-625" /><figcaption>uv5r+fldigi+digirig</figcaption></figure>

It works like magic!

Next step is to talk to radio via python
