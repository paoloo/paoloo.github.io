---
title: WakeOnLan num macOSX Lion Server
date: 2011-09-30T19:06:52+00:00
author: paolo
layout: post
permalink: /2011/09/30/wakeonlan-num-macosx-lion-server/
categories:
  - pt-BR
tags:
  - comp
  - hacks
---
A porcaria do mac OSX Lion, rodando no MacMini, usado como servidor de arquivos é uma droga e fica se desligando só por falta de atividade(por falha no OS, nao por falta de configuração) e uma das soluções era enviar frames com o wake on lan o tempo todo para lá.  
Para enviar é muito facil. No python:

<pre class="brush: python; title: ; notranslate" title="">import socket
 s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto('\xff'*6+'\xc8\x2a\x14\x58\xf9\x59'*16, ('172.17.119.3', 80))
</pre>

Depois foi pro cron e funcionou tranquilamente. Só não foi um final feliz porque outros problemas apareceram o foi feito o mais correto: Enfiar um linux no Mac Mini hahaha.