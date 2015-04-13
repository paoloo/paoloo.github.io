---
title: Acessando PCI Express com python
date: 2015-04-13T17:03:54+00:00
author: paolo
layout: post
permalink: /2015/04/13/acessando-pci-express-com-python-2/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - hacks
  - python
  - random
---
Usando **lspci** para retornar o valor do dispositivo:  
**01:00.0** Non-VGA unclassified device: Altera Corporation Device 0de4 (rev 01)  
Encontra-o em /sys/devices/  
/sys/devices/pci0000:00/0000:00:01.0/0000:**01:00.0**  
Habilita-o com:

<pre class="brush: bash; title: ; notranslate" title="">echo -n 1 &gt; /sys/devices/pci0000:00/0000:00:01.0/0000:01:00.0/enable </pre>

Depois, só rodar o script(salvar como **placapci.py**):

<pre class="brush: python; title: ; notranslate" title="">import mmap, sys
with open('/sys/devices/pci0000:00/0000:00:01.0/0000:01:00.0/resource0', 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 32)
    mm[:1] = chr(int(sys.argv[1], 16))
</pre>

no caso, ativar os leds de uma altera lindona:  
**python placapci.py 0xAA**  
[<img class="alignnone size-medium wp-image-398" src="{{ site.baseurl }}/uploads/2015/04/01.jpg?w=222" alt="01" width="222" height="300" srcset="{{ site.baseurl }}/uploads/2015/04/01.jpg 2368w, {{ site.baseurl }}/uploads/2015/04/01-222x300.jpg 222w, {{ site.baseurl }}/uploads/2015/04/01-768x1038.jpg 768w, {{ site.baseurl }}/uploads/2015/04/01-758x1024.jpg 758w" sizes="(max-width: 222px) 100vw, 222px" />]({{ site.baseurl }}/uploads/2015/04/01.jpg)  
**python placapci.py 0x55**  
[<img class="alignnone size-medium wp-image-399" src="{{ site.baseurl }}/uploads/2015/04/02.jpg?w=222" alt="02" width="222" height="300" srcset="{{ site.baseurl }}/uploads/2015/04/02.jpg 2368w, {{ site.baseurl }}/uploads/2015/04/02-222x300.jpg 222w, {{ site.baseurl }}/uploads/2015/04/02-768x1038.jpg 768w, {{ site.baseurl }}/uploads/2015/04/02-758x1024.jpg 758w" sizes="(max-width: 222px) 100vw, 222px" />]({{ site.baseurl }}/uploads/2015/04/02.jpg)

É isso aí.
