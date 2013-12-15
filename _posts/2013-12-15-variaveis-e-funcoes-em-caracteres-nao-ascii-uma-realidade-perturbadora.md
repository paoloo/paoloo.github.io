---
title: 'variaveis e funçoes em caracteres nao-ascii: uma realidade perturbadora'
date: 2013-12-15T23:32:40+00:00
author: paolo
layout: post
permalink: /2013/12/15/variaveis-e-funcoes-em-caracteres-nao-ascii-uma-realidade-perturbadora/
categories:
  - pt-BR
tags:
  - comp
  - hacks
  - random
---
Quanto tempo levará para codigos como o descrito aqui (que funciona, infelizmente) se tornarem comuns? Eu sei, em alguns casos isso é util (EXs: **var π = Math.PI** ou **var λ = function(){};**) e que neste caso do meu exemplo, são apenas componentes dos alfabetos japoneses. Porém, alem de vários alfabetos, tambem são permitidos coisas absurdas como ಠ益ಠ ou 个卐Δℕ, e isto é um convite ao caos!!!!!!!!

<pre class="brush: xml; title: ; notranslate" title="">&lt;html&gt;
&lt;head&gt;
&lt;meta http-equiv="Content-Type" content="text/html; charset=utf-8" /&gt;
&lt;script&gt;
var ヽン = function(ヽロノ){ alert(ヽロノ); }
var ヽo_oノ = function(){ ツ = "ヽo_oノ ", ー=0; while(ー&lt;9){ツ+=ツ; ー++;} return ツ; }
&lt;/script&gt;
&lt;/head&gt;
&lt;body&gt;
&lt;input type="button" onClick="javascript:ヽン(ヽo_oノ())"&gt;
&lt;/body&gt;
&lt;/html&gt;
</pre>

É ou não é bizarro?

Ah, uma forma rápida de checar se a variável é permitida(alem de escrever em um texto e abrir no navegador hahahaha), é através do site <http://mothereff.in/js-variables>.