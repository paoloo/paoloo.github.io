---
title: Analisando pcap com Scapy
date: 2010-11-17T23:13:49+00:00
author: paolo
layout: post
permalink: /2010/11/17/analisando-pcap-com-scapy/
categories:
  - pt-BR
tags:
  - hacks
  - python
---
Depois de ficar de saco cheio de abrir o wireshark ou ettercap para ver .pcaps, eu lembrei que o scapy faz o mesmo, porem de forma muito mais leve. Para quem nao conhece [scapy](http://www.secdev.org/projects/scapy/), é um canivete suiço de tcp/ip em forma de modulo python. Possui uma quantidade imensa de features(como sniffer, flooder, analise de pacotes&#8230;) e ainda é extensível. Na minha opinião é a ferramente principal de análise e interação de redes. É muito facil usá-lo para analisar pcap. Nos exemplos a seguir, usarei o pcap de um sniff em uma vm windows xp sp3 depois de infectada por um malware.

**$ python**

<pre class="brush: python; title: ; notranslate" title="">Python 2.7 (r27:82500, Sep 16 2010, 18:03:06)
[GCC 4.5.1 20100907 (Red Hat 4.5.1-3)] on linux2
Type &quot;help&quot;, &quot;copyright&quot;, &quot;credits&quot; or &quot;license&quot; for more information.
&gt;&gt;&gt; from scapy.all import *
&gt;&gt;&gt; b=rdpcap('./traffic1.pcap') # carregar o arquivo na variavel b
&gt;&gt;&gt; b
&lt;traffic1.pcap: TCP:9 UDP:0 ICMP:0 Other:0&gt; # 9 frames TCP
&gt;&gt;&gt; b.nsummary()  # mostra uma visao geral dos frames
0000 Ether / IP / TCP 192.168.0.2:mtqp &gt; 89.209.91.49:http S
0001 Ether / IP / TCP 89.209.91.49:http &gt; 192.168.0.2:mtqp SA
0002 Ether / IP / TCP 192.168.0.2:mtqp &gt; 89.209.91.49:http A / Padding
0003 Ether / IP / TCP 192.168.0.2:mtqp &gt; 89.209.91.49:http PA / Raw
0004 Ether / IP / TCP 89.209.91.49:http &gt; 192.168.0.2:mtqp PA / Raw
0005 Ether / IP / TCP 89.209.91.49:http &gt; 192.168.0.2:mtqp FA / Padding
0006 Ether / IP / TCP 192.168.0.2:mtqp &gt; 89.209.91.49:http A / Padding
0007 Ether / IP / TCP 192.168.0.2:mtqp &gt; 89.209.91.49:http FA / Padding
0008 Ether / IP / TCP 89.209.91.49:http &gt; 192.168.0.2:mtqp A / Padding

# para analisar qualquer frame é só definir na variável

&gt;&gt;&gt; b[4]
&lt;Ether  dst=52:54:00:12:34:56 src=92:27:fc:57:72:bb type=0x800 |&lt;IP  version=4L ihl=5L tos=0x0 len=444 id=35057 flags=DF frag=0L ttl=103 proto=tcp chksum=0x139e src=89.209.91.49 dst=192.168.0.2 options='' |&lt;TCP  sport=http dport=mtqp seq=2622890338L ack=3064987870L dataofs=5L reserved=0L flags=PA window=64702 chksum=0xe61e urgptr=0 options=[] |&lt;Raw  load='HTTP/1.1 404 Not Found\r\nDate: Thu, 08 Nov 2007 06:09:09 GMT\r\nServer: Apache/2.2.15 (Win32) PHP/5.2.13\r\nContent-Length: 214\r\nConnection: close\r\nContent-Type: text/html; charset=iso-8859-1\r\n\r\n&lt;!DOCTYPE HTML PUBLIC &quot;-//IETF//DTD HTML 2.0//EN&quot;&gt;\n&lt;html&gt;&lt;head&gt;\n&lt;title&gt;404 Not Found&lt;/title&gt;\n&lt;/head&gt;&lt;body&gt;\n&lt;h1&gt;Not Found&lt;/h1&gt;\n&lt;p&gt;The requested URL /e/websitechk.php was not found on this server.&lt;/p&gt;\n&lt;/body&gt;&lt;/html&gt;\n' |&gt;&gt;&gt;&gt;

# para uma análise melhor, usar o método show()

&gt;&gt;&gt; b[4].show()
###[ Ethernet ]###
dst= 52:54:00:12:34:56
src= 92:27:fc:57:72:bb
type= 0x800
###[ IP ]###
version= 4L
ihl= 5L
tos= 0x0
len= 444
id= 35057
flags= DF
frag= 0L
ttl= 103
proto= tcp
chksum= 0x139e
src= 89.209.91.49
dst= 192.168.0.2
options= ''
###[ TCP ]###
sport= http
dport= mtqp
seq= 2622890338L
ack= 3064987870L
dataofs= 5L
reserved= 0L
flags= PA
window= 64702
chksum= 0xe61e
urgptr= 0
options= []
###[ Raw ]###
load= 'HTTP/1.1 404 Not Found\r\nDate: Thu, 08 Nov 2007 06:09:09 GMT\r\nServer: Apache/2.2.15 (Win32) PHP/5.2.13\r\nContent-Length: 214\r\nConnection: close\r\nContent-Type: text/html; charset=iso-8859-1\r\n\r\n&lt;!DOCTYPE HTML PUBLIC &quot;-//IETF//DTD HTML 2.0//EN&quot;&gt;\n&lt;html&gt;&lt;head&gt;\n&lt;title&gt;404 Not Found&lt;/title&gt;\n&lt;/head&gt;&lt;body&gt;\n&lt;h1&gt;Not Found&lt;/h1&gt;\n&lt;p&gt;The requested URL /e/websitechk.php was not found on this server.&lt;/p&gt;\n&lt;/body&gt;&lt;/html&gt;\n'

# para exibir todo o conteudo, equivalente ao 'follow tcp stream' no wireshark:

&gt;&gt;&gt; print '\n'.join([('%s -&gt; %s\n%s'%(b[i].payload.src,b[i].payload.dst,b[i].load)) for i in range(len(b)) if hasattr(b[i], 'load')])
192.168.0.2 -&gt; 89.209.91.49
POST http://89.209.91.49/e/websitechk.php HTTP/1.1
Host: 89.209.91.49
Connection: close
Content-Type: multipart/form-data; boundary=55377776816118
Content-Length: 659
...

</pre>

Enfim, é isso. O Scapy é uma ferramenta excelente e merece ser bem explorada.