---
title: 'nodeMCU: Mais que uma dev Board, um vício'
date: 2015-11-19T11:29:43+00:00
author: paolo
layout: post
permalink: /2015/11/19/nodemcu-mais-que-uma-dev-board-um-vicio/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - comp
  - LUA
  - toys
  - uC
---
**NodeMCU**( <a href="http://nodemcu.com/index_en.html" target="_blank">http://nodemcu.com/index_en.html</a> ) é uma plataforma de desenvolvimento baseada no SoC ESP8266, com stack TCP/IP, eLua e vários extensões do lua embarcadas, voltadas especialmente para aplicações de IoT.  
O SoC ESP8266 usa uma CPU RISC de 32bits Tensilica Xtensa LX106, rodando a 80MH. Tem uma RAM de instruções de 64 Kb, uma RAM de dados de 96Kb e uma flash interna de 4 fucking MBs! A estrela do bolo é o IEEE 802.11 b/g/n com suporte a WEP,WPA/WPA2 disponível, além dos 16 pinos de GPIO, SPI, I2C, UART e ADC de até 10bits.

[<img class="alignnone size-medium wp-image-423" src="{{ site.baseurl }}/uploads/2015/11/nodemcu.png?w=300" alt="nodeMCU" width="300" height="255" srcset="{{ site.baseurl }}/uploads/2015/11/nodemcu.png 440w, {{ site.baseurl }}/uploads/2015/11/nodemcu-300x255.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2015/11/nodemcu.png)

No xubuntu, eu tive problemas de conectar nela com o minicom. Mas estou usando lindamento o screen:

<pre class="brush: plain; title: ; notranslate" title="">$ screen /dev/ttyUSB0 9600
</pre>

Lua/eLua é linda. coisas extremamente complexas são executadas com uma simplicidade absurda, como listar as redes 802.11 disponiveis:

<pre class="brush: plain; title: ; notranslate" title="">&gt; function lswifi()
&gt;&gt;  function listap(t)
&gt;&gt;    for k,v in pairs(t) do
&gt;&gt;      print(k.." : "..v)
&gt;&gt;    end
&gt;&gt;  end
&gt;&gt;  wifi.sta.getap(listap)
&gt;&gt;end
&gt;lswifi()
</pre>

listar os arquivos, o conhecido &#8216;ls&#8217;, é simples:

<pre class="brush: plain; title: ; notranslate" title="">&gt; for k,v in pairs(file.list()) do print(k,v) end
</pre>

logar na rede wifi, então, piece of cake:

> wifi.setmode(wifi.STATION);  
> wifi.sta.config("SSID","senha")

e pronto! so checar seu ip com:

<pre class="brush: plain; title: ; notranslate" title="">print(wifi.sta.getip())
</pre>

Aproveitei e fiz um wget rudimentar hahaha

<pre class="brush: plain; title: ; notranslate" title="">conn=net.createConnection(net.TCP, false) 
conn:on("receive", function(conn, pl) file.open("oi.lua","a"); file.write(pl); file.close() end)
conn:connect(80,"121.41.33.127")
conn:send("GET / HTTP/1.1\r\nHost: www.nodemcu.com\r\n"
    .."Connection: keep-alive\r\nAccept: */*\r\n\r\n")
</pre>

Escrevi alguns métodos do GNU coreutils, como ls, cp, mv, df&#8230; para facilitar a vida. Em breve posto no github e ponho o link aqui.

O legal é que existem uma infinidade de exemplos e aplicações para esta plaquinha. E ela ganhou um fã haha.

Enjoy!
