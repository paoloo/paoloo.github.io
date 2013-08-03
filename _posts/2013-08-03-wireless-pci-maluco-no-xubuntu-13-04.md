---
title: wireless pci maluco no xubuntu 13.04
date: 2013-08-03T13:22:31+00:00
author: paolo
layout: post
permalink: /2013/08/03/wireless-pci-maluco-no-xubuntu-13-04/
categories:
  - pt-BR
tags:
  - comp
  - ubuntu
---
Quando fiz o update de kernel no xubuntu 13.04, depois do reboot,  
meu ndiswripper(é, ainda uso placa incompatível+ndsiwrapper&#8230; eu sei&#8230;) pirou, o modprobe nao me deixava levantar o modulo dando um erro bizarro:

<pre class="brush: bash; title: ; notranslate" title=""># modprobe ndiswrapper
</pre>

**ERROR: could not insert &#8216;ndiswrapper&#8217;: Exec format error**  
olhando o dmesg:  
**[  841.073631] ndiswrapper: disagrees about version of symbol module_layout**  
a solucao foi simples, enfiei um radio usb antigo e lerdo feito o inferno, porém compatível,  
meti um

<pre class="brush: bash; title: ; notranslate" title=""># apt-get remove ndiswrapper ndiswrapper-dkms ndiswrapper-common
</pre>

e depois um

<pre class="brush: bash; title: ; notranslate" title=""># apt-get install ndiswrapper-dkms ndiswrapper-modules-1.9 ndiswrapper-utils-1.9
</pre>

e tudo funcionou lindamente

<pre class="brush: bash; title: ; notranslate" title=""># ndiswrapper -l
</pre>

mrv8335 : driver installed  
device (11AB:1FAA) present

<pre class="brush: bash; title: ; notranslate" title=""># modprobe ndiswrapper
</pre>

uhuuu!