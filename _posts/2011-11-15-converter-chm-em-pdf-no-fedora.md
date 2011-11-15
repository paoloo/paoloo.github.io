---
title: converter CHM em PDF no Fedora
date: 2011-11-15T11:18:37+00:00
author: paolo
layout: post
permalink: /2011/11/15/converter-chm-em-pdf-no-fedora/
categories:
  - pt-BR
tags:
  - comp
  - fedora
---
Eu nao suporto CHM, entao procurei uma forma de PDFizar os livros em CHM que possuo. Depois de algum tempo achei o chm2pdf().  
Primeiro eu procurei resolver as dependencias dele:

<pre class="brush: bash; title: ; notranslate" title=""># yum install chmlib python-chm htmldoc
</pre>

depois baixei os fontes ( http://chm2pdf.googlecode.com/files/chm2pdf-0.9.1.tar.gz ) e mandei um:

<pre class="brush: bash; title: ; notranslate" title=""># python setup.py install
</pre>

Depois da instalação, é só rodar um

<pre class="brush: bash; title: ; notranslate" title="">chm2pdf --book arquivo.chm
</pre>

para gerar o pdf. Aproveitei e criei uma &#8216;custom action&#8217; no thunar para automatizar:

<pre class="brush: plain; title: ; notranslate" title="">Name: convert CHM to PDF
Description: convert CHM to PDF
Command: chm2pdf --book %f
File Pattern: *.chm;*.CHM
Appear if selection contains: Other files
</pre>

O treco funciona muito bem.