---
title: '"Ouvindo aviões" com meu SDR USB'
date: 2013-05-15T02:58:19+00:00
author: paolo
layout: post
permalink: /2013/05/15/ouvindo-avioes-com-meu-sdr-usb/
categories:
  - pt-BR
tags:
  - SDR
---
Usando meu novo sdr usb, fiz um teste que queria fazer a muito tempo: escutar transponder de aeronaves.
Antes de mais nada, precisava de algum software para gerenciar os dados. GNURadio seria a escolha obvia, mas estou sem banda e baixar quase 1GB de não faz sentido. Optei pelo rtl-sdr.
O rtl-sdr é uma versão capada e bem simplificada das ferramentas do GNURadio feita pelo pessoal da osmocom. Não é um sibstituto, mas um quebra-galho bem legal.
Então o primeiro passo é baixar e compilar o rtl-sdr:

<pre class="brush: bash; title: ; notranslate" title="">git clone git://git.osmocom.org/rtl-sdr.git
cd  rtl-sdr
mkdir  build
cd  build
cmake  ../ -DINSTALL_UDEV_RULES=ON
make
sudo  make  install
sudo  ldconfig
</pre>

Se tudo estiver OK, so rodar:

<pre class="brush: bash; title: ; notranslate" title="">rtl_test  -t
</pre>

com o dispositivo plugado na USB.
Agora é hora de baixar e compilar o dump1090:

<pre class="brush: bash; title: ; notranslate" title="">git  clone  git://github.com/MalcolmRobb/dump1090.git
cd  dump1090
make
</pre>

Tudo compilando é so meter um:

<pre class="brush: bash; title: ; notranslate" title="">./dump1090 --interactive
</pre>

para ver isso:
[<img class="alignnone size-medium wp-image-287" alt="aeroporto 1" src="{{ site.baseurl }}/uploads/2013/06/aeroporto-1.png?w=300" width="300" height="73" srcset="{{ site.baseurl }}/uploads/2013/06/aeroporto-1.png 739w, {{ site.baseurl }}/uploads/2013/06/aeroporto-1-300x73.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2013/06/aeroporto-1.png)
lindo ne? Este screenshot foi tirado sentado no embarque do Aeroporto Internacional Ant. Carlos Jobim, o Galeão, no Rio. Note os aviões pousados (Altitude:ground).

BONUS: Dentro do avião eu rodei rtl_fm, um utilitário do rtl-sdr da osmocom( [mini-manual](http://kmkeen.com/rtl-demod-guide/ "http://kmkeen.com/rtl-demod-guide/") ) para ouvir o canal de comunicação do avião:

<pre class="brush: bash; title: ; notranslate" title="">rtl_fm -M -f 118M:137M:25k -s 12k -g 49.2 -l 2 | play -r 12k -t raw -e signed-integer -b 16 -c 1 -V1 -

</pre>

E o resultado:

[<img class="alignnone size-medium wp-image-288" alt="inside the plane" src="{{ site.baseurl }}/uploads/2013/06/inside-the-plane.png?w=300" width="300" height="132" srcset="{{ site.baseurl }}/uploads/2013/06/inside-the-plane.png 737w, {{ site.baseurl }}/uploads/2013/06/inside-the-plane-300x133.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2013/06/inside-the-plane.png)

Bem legal.
