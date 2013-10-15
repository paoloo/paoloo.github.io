---
title: Problema ao usar o meu SDR USB no linux
date: 2013-10-15T17:02:13+00:00
author: paolo
layout: post
permalink: /2013/10/15/problema-ao-usar-o-meu-sdr-usb-no-linux/
categories:
  - pt-BR
tags:
  - comp
  - SDR
  - ubuntu
---
Em uma fresh install no xubuntu, ao tentar o **rtl_test** tive uma péssima surpresa:

**$ rtl_test -t**  
Found 1 device(s):  
0:  Realtek, RTL2838UHIDIR, SN: 00000001

Using device 0: Generic RTL2832U OEM

Kernel driver is active, or device is claimed by second instance of librtlsdr.  
In the first case, please either detach or blacklist the kernel module  
(dvb\_usb\_rtl28xxu), or enable automatic detaching at compile time.

usb\_claim\_interface error -6  
Failed to open rtlsdr device #0.

Ou seja: o linux nao conseguia abrir o meu dispositivo por ele ja está em uso! Mas como, onde e por que? Depois de dar uma checadas, percebi que o problema era o linux que percebeu o dongle e ja carregou os drivers DVB, ou seja, transformou em um receptor de TV e como o driver ja estava usando o dispositivo, ele ficou ocupado para qualquer outro modo.  
A solução inicial foi meio obvia, removi o dvb\_usb\_rtl28xxu mencionado no arquivo de erro:  
**  # modprobe -r dvb\_usb\_rtl28xxu**  
Funcionou, rodou lindamente. Depois tornei a solução permanente adicionando:  
**blacklist dvb\_usb\_rtl28xxu**  
em qualquer arquivo .conf já existem em **/etc/modprobe.d** (ou cria um meusdr.conf para ficar organizado).

Fim do problema.