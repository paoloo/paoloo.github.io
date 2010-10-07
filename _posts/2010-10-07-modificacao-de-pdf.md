---
title: 'modificação de PDF em momentos de raiva: como fazer.'
date: 2010-10-07T21:55:42+00:00
author: paolo
layout: post
permalink: /2010/10/07/modificacao-de-pdf/
categories:
  - pt-BR
tags:
  - hacks
---
Depois que uma maravilhosa escaneadora automatica processa seu arquivo e voce se desloca para longe dela, voce percebe que fez a burrice de nao escanear em landscape. Até ai tudo bem, nao fosse voce tambem perceber que a escaneadora salva os arquivos com as paginas impares de ponta cabeça. Você, então, usando sua ira interior pensa em meter wipe no arquivo inutil. Comigo foi assim. Sorte que eu nao sou de momento e pensei um pouco. Alguns minutos de busca me levaram ao pdftk( <http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/> ) uma aplicação, simplesmente, mágica!

Depois de ler o manual, era hora de tentar a sorte:

Primeiro, transformar o texto em landscape:

<pre class="brush: bash; title: ; notranslate" title="">pdftk documento.pdf cat 1-endW output 1.pdf</pre>

Agora era hora de separar paginas pares de impares e rotacionar as pares num diretorio separado:

<pre class="brush: bash; title: ; notranslate" title="">mkdir tmp

pdftk 1.pdf cat 1-endodd output tmp/odd.pdf

pdftk 1.pdf cat 1-endevenD output tmp/even.pdf</pre>

Agora precisava separar as paginas em arquivos unicos:

<pre class="brush: bash; title: ; notranslate" title="">pdftk tmp/odd.pdf burst output tmp/pg%04d_A.pdf

pdftk tmp/even.pdf burst output tmp/pg%04d_B.pdf</pre>

E, finalmente, reunir os arquivos unicos num unico pdf ordenado:

<pre class="brush: bash; title: ; notranslate" title="">pdftk tmp/pg*.pdf cat output arquivo-ok.pdf</pre>

O resultado final me agradou muito. Este pdftk é uma ferramente indispensável ;D