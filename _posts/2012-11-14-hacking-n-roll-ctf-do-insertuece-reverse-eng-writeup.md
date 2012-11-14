---
title: "Hacking N' Roll - CTF do INSERT/UECE - Reverse Eng. Writeup"
date: 2012-11-14T15:09:25+00:00
author: paolo
layout: post
permalink: /2012/11/14/hacking-n-roll-ctf-do-insertuece-reverse-eng-writeup/
categories:
  - pt-BR
tags:
  - hacks
---
Este é o writeup dos 5 níveis dos desafios de engenharia reversa do II Hacking N&#8217; Roll, CTF organizado pelo grupo INSERT da UECE.

**REV100**

Olhando as strings na seção .rodata do binário, que vai de 0x538 até 0xcc8 como mostra o objdump:

<pre class="brush: plain; title: ; notranslate" title="">$ objdump -j .rodata -x rev100
(...)
Sections:
Idx Name Size VMA LMA File off Algn
 14 .rodata 00000590 08048738 08048738 00000738 2**2
 CONTENTS, ALLOC, LOAD, READONLY, DATA
(...) </pre>

Encontramos uma string interessante(leia: resposta) no editor hexadecimal, como mostra o screenshot a seguir:

[<img class="alignnone size-medium wp-image-220" title="rev100" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev100.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev100.png 562w, {{ site.baseurl }}/uploads/2012/11/rev100-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev100.png)

**REV200**

Verificamos que o código em Assembly mostrado não fazia muito sentido, pois acessava a memória de maneira estranha e não parecia corresponder a nenhum algoritmo conhecido.

<pre class="brush: plain; title: ; notranslate" title="">08048054 &lt;_start&gt;:
 8048054: eb 00 jmp 8048056 &lt;get_call&gt;

08048056 &lt;get_call&gt;:
 8048056: 09 79 20 or %edi,0x20(%ecx)
 8048059: 30 20 xor %ah,(%eax)
 804805b: 75 20 jne 804807d &lt;get_call+0x27&gt;
 804805d: 7c 32 jl 8048091 &lt;get_call+0x3b&gt;
 804805f: 20 20 and %ah,(%eax)
 8048061: 20 6b 20 and %ch,0x20(%ebx)
 8048064: 33 20 xor (%eax),%esp
 8048066: 79 20 jns 8048088 &lt;get_call+0x32&gt;
 8048068: 20 20 and %ah,(%eax)
 804806a: 69 35 20 3a 09 49 27 imul $0x525f6d27,0x49093a20,%esi
 8048071: 6d 5f 52
 8048074: 33 40 6c xor 0x6c(%eax),%eax
 8048077: 6c insb (%dx),%es:(%edi)
 8048078: 59 pop %ecx
 8048079: 5f pop %edi
 804807a: 34 6e xor $0x6e,%al
 804807c: 5f pop %edi
 804807d: 61 popa
 804807e: 73 63 jae 80480e3 &lt;get_call+0x8d&gt;
 8048080: 49 dec %ecx
 8048081: 49 dec %ecx
 8048082: 0a .byte 0xa
</pre>

Percebe-se a grande quantidade de 0x20(espaço). Utilizando o seguinte código de uma linha em Python:

<pre class="brush: plain; title: ; notranslate" title="">''.join([a[1].strip() for a in [s.split('\t') for s in open('rev200').xreadlines()] if len(a)==3]).replace(' ','').decode('hex')</pre>

Verificamos como era o binário original antes de ser disassemblado, representado pela seguinte string:

&#8220;\xeb\x00\ty 0 u |2 k 3 y i5 :\tI&#8217;3@llY\_4n\_ascII\n&#8221;

Onde aparece a palavra-chave para o problema ( I&#8217;3@llY\_4n\_ascII ).

**REV300**

Dentro da função inside2, encontramos uma chamada às funções reveal e scramble, o que indica que a função constrói a chave e depois embaralha com a função scramble.

[<img class="alignnone size-medium wp-image-221" title="rev300a" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev300a.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev300a.png 562w, {{ site.baseurl }}/uploads/2012/11/rev300a-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev300a.png)

Então entramos na função scramble e colocamos uma instrução &#8216;ret&#8217; logo no início da mesma, para que ela não seja executada quando for chamada

[<img class="alignnone size-medium wp-image-222" title="rev300b" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev300b.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev300b.png 562w, {{ site.baseurl }}/uploads/2012/11/rev300b-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev300b.png).

Salvamos o programa com a modificação acima e executamos, passando as telas, até que ele mostra a chave.

[<img class="alignnone size-medium wp-image-223" title="rev300c" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev300c.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev300c.png 562w, {{ site.baseurl }}/uploads/2012/11/rev300c-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev300c.png)

**REV400**

Verificando os símbolos existentes no binário, encontramos uma função com nome sugestivo &#8211; reveal.

[<img class="alignnone size-medium wp-image-224" title="rev400a" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev400a.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev400a.png 562w, {{ site.baseurl }}/uploads/2012/11/rev400a-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev400a.png)

Essa função reveal é chamada em apenas um local. Seguindo o xref, achamos a função flag. A função flag, por sua vez, não é utilizada em nenhum local do programa.

[<img class="alignnone size-medium wp-image-225" title="rev400b" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev400b.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev400b.png 562w, {{ site.baseurl }}/uploads/2012/11/rev400b-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev400b.png)

Abrimos o gdb, colocamos um breakpoint em main, executamos o programa, e chamamos a função flag usando o comando call do gdb, e verificamos que ela mostra a string desejada.

[<img class="alignnone size-medium wp-image-226" title="rev400c" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev400c.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev400c.png 562w, {{ site.baseurl }}/uploads/2012/11/rev400c-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev400c.png)

REV500

Percebemos que várias funções do programa gravavam dados numa região de memória associada ao símbolo &#8216;hidden&#8217;.

[<img class="alignnone size-medium wp-image-227" title="rev500a" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev500a.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev500a.png 562w, {{ site.baseurl }}/uploads/2012/11/rev500a-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev500a.png)

Consta no binário que o comprimento do símbolo é de 98 bytes.

[<img class="alignnone size-medium wp-image-228" title="rev500b" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev500b.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev500b.png 562w, {{ site.baseurl }}/uploads/2012/11/rev500b-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev500b.png)

Verificamos um ponto na função &#8216;main&#8217; que estaria depois da chamada de todas as funções.

[<img class="alignnone size-medium wp-image-229" title="rev500c" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev500c.png?w=300" height="180" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev500c.png 562w, {{ site.baseurl }}/uploads/2012/11/rev500c-300x180.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev500c.png)

Executamos o gdb e colocamos um breakpoint nesse ponto. Mandamos executar o programa. Ao chegar no breakpoint, dumpamos a região de memória do símbolo &#8216;hidden&#8217;. Visualizamos uma string cerca de 39 bytes à frente do início do símbolo, e demos um comando print para visualizar melhor. Nessa string aparece a chave.

[<img class="alignnone size-medium wp-image-230" title="rev500d" alt="" src="{{ site.baseurl }}/uploads/2012/11/rev500d.png?w=300" height="286" width="300" srcset="{{ site.baseurl }}/uploads/2012/11/rev500d.png 752w, {{ site.baseurl }}/uploads/2012/11/rev500d-300x287.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2012/11/rev500d.png)

Infelizmente, nós do grupo CACTUS do IFCE não levamos esta por diversas razões e aproveitamos para congratular os vencedores e organizadores.
