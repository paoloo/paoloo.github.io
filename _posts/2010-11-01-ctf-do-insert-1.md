---
title: 'CTF do INSERT #1'
date: 2010-11-01T01:29:01+00:00
author: paolo
layout: post
permalink: /2010/11/01/ctf-do-insert-1/
categories:
  - pt-BR
tags:
  - comp
  - hacks
---
Ocorreu nos dias 24 e 25 o Hackingnroll, evento CTF do grupo INSERT( <http://www.insert.uece.br/> ) da UECE/FFB. Fiquei interessado no evento e no grupo, pois seria uma proposta nova e interessante para o estado um grupo acadêmico sobre segurança.

O evento teve dois pontos antagonicos: por um lado foi desorganizado, ou mal gerenciado, nao sei julgar. Houveram atrasos e o formato dos desafios(uma coisa mais defcon-like) nao agradou muito. Por outro lado, a iniciativa foi incrivel. O grupo tem muito para crescer no estado(que ja tem um historico de profissionais ou hobistas de segurança renomados, ao menos no _underground_) e conseguir lotar um canal de IRC com pessoas que nao tem habito de usa-lo, em 2010, foi um feito. As possibilidades disto evoluir para um encontro periódico ou ate mesmo uma conferência, são imensas.

Pelo que vi, tenho esperança que o evento em sí evolua, bem como a comunidade de segurança no estado. Mas o post tem outro propósito. Como eles nao disponibilizaram um walkthrough, eu farei este trabalho. Infelizmente eu nao salvei todos os desafios, mas editarei a medida que for achando outros.  Começando pelo 5 níveis de **Reversing**, temos:

**Reversing 100 ~ Baixe o programa (compactado) compilado pra Linux e descubra qual a senha de desbloqueio!**

Depois de descompactar, temos um elf:

<pre class="brush: bash; title: ; notranslate" title="">$ file rev100</pre>

rev100: ELF 32-bit LSB executable, Intel 80386, version 1 (SYSV), dynamically linked (uses shared libs), for GNU/Linux 2.6.18, not stripped

<pre class="brush: bash; title: ; notranslate" title="">$ strings rev100</pre>

Revela, entre outras coisas, a senha plain, no caso: _**herbie\_pass\_strong**_

**Reversing 200 ~ A instrução em hexadecimal 0x83e58955 equivale a qual ope? Me diga Você !**

usando python e a libdisassemble da immunity ( http://www.immunitysec.com/downloads/libdisassemble2.0.tar.gz ), temos:

<pre class="brush: python; title: ; notranslate" title="">&gt;&gt;&gt; from disassemble import *
&gt;&gt;&gt; data="\x83\xe5\x89\x55"
&gt;&gt;&gt; p=Opcode(data)
&gt;&gt;&gt; p.printOpcode("AT&T")
'and           $0x89, %ebp'</pre>

Assim, a resposta é: _**and $0x89, %ebp**_

**Reversing 300 ~ Qual a operacao que eu mais realizo?** 

<pre class="brush: bash; title: ; notranslate" title="">$ objdump -d --no-show-raw-insn ./rev300 | awk '/^[ 0-9a-f]+:/{print $2}' | sort | uniq -c </pre>

A operação mais usada, com 60 ocorrencia, é: _**mov**_ seguida por **nop**(33 ocorrencias), **push** e **call**(ambas com 31 ocorrencias).

**Reversing 400 ~ A que método criptográfico se assemelha o que está presente no executável dado?**

Ao executar e entrar &#8216;aaaa&#8217; como texto e 1 como chave, temos &#8216;bbbb&#8217; como saida. Testes posteriores mostraram se tratar de uma cifra de rolagem, se assemelhando, entao com a _**cifra de cesar**_ ou _**rot13**_.  
**Reversing 500:&#8221;Qual instrucao em assembly esta relacionada com o seguinte trecho de codigo em C:**

<pre class="brush: cpp; title: ; notranslate" title="">for( ecx = 0 ; ecx &lt; 32 ; ecx++ ){
if ( (1 &lt;&lt; ecx) & eax ) {
ebx = ecx;
break;
}
}</pre>

**  
** **???  
resposta no formato:<instrucao> %<registrador 1>,%<registrador 2>  
** **por exemplo: addl %esp,%ebp**

Checando no manual da intel, temos: _**bsfl %eax, %ebx**_

Com isso, terminam a solução dos 5 níveis de reversing. Caso o resto dos desafios sejam localizados, postarei as soluções.