---
title: Wget para conexões birrentas
date: 2011-02-13T19:12:10+00:00
author: paolo
layout: post
permalink: /2011/02/13/wget-para-conexoes-birrentas/
categories:
  - pt-BR
tags:
  - comp
  - random
---
Ao precisar baixar um fonte de 20MB para fazer correções de emergencia, me vi desesperado ao usar uma conxão gprs (que deveria ser 3g) e ter o wget caindo a cada 6 segundos. Como eu nao podia ficar a todo tempo dando ctrl+c e pedindo novamente o arquivo, deixei o wget fazer isso por mim desse jeito:

<pre class="brush: bash; title: ; notranslate" title="">wget -c --tries=inf --read-timeout=5 'url'
</pre>

onde:  
**-c** continua o download do ponto onde parou.  
**&#8211;tries=inf** quantas tentativas antes de desistir do download. Embora o valor seja geralmente numerico, aceita inf para infinito.  
**&#8211;read-timeout=5** seta o timeout da leitura e escrita para o valor definido em segundos, no caso, 5. O tempo se refere ao tempo ocioso, quando nenhum dado é recebido ou enviado.  
Demorou, mas ele fez o download.  
Depois disso pus um alias no meu .bashrc

<pre class="brush: bash; title: ; notranslate" title="">function pget(){ wget -c --tries=inf --read-timeout=10 $(echo $*) ; }
</pre>

Escolhi &#8216;pget&#8217; por representar &#8216;persistent wget&#8217;.  
Bom, só caso isso seja util a alguem.