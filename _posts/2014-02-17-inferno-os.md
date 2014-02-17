---
title: Inferno OS
date: 2014-02-17T12:42:12+00:00
author: paolo
layout: post
permalink: /2014/02/17/inferno-os/
categories:
  - pt-BR
tags:
  - comp
  - OS
---
Inferno é um sistema operacional compacto que foi criado em 1995 por membros do Bell Labs, com o proposito de construir sistemas distruibuidos. Foi baseado nas experiencias feitas com o plan 9 e pode rodar tanto nativamente (em quase toda arquitetura existente, literalmente haha) como na forma de aplicação simbionte sore o sistema operacional em uso(ou o internet explorer hahaha).  
Usa os nomes de aplicaçoes principais e do próprio sistema advindos da parte &#8220;inferno&#8221; de &#8220;A divina Comédia&#8221; do Dante Alighieri.  
Ele se baseia em uma maquina virtual, chamada de Dis, que faz JIT compilation(just-in-time compilling) sobre os codigos escritos em Limbo, uma mistureba orientada a objetos de C com pascal, e o protocolo Styx, clone do 9P. Como no Plan 9, todos os recursos são arquivos(memoria, teclado, mouse, monitor, bancos de dados, voce, etc), usa o conceito de namespace, prove nativamente suporte a encriptação IDEA, DES de 56 bits e RC4 de 40, 50, 128 e 256 bits bem como MD4, MD5 e SHA como algoritmos de hash&#8230; Usa o mesmo estilo de permissão do unix, e os comandos do shell são tão ou mais poderosos que o bash, porém a implementação da interação com o usuário do terminal é meio zoada(só apertar a tecla &#8220;para cima&#8221; para entender o que quer dizer).

_**Instalação**_  
Baixei de <http://www.vitanuova.com/dist/old/3e/3e.tgz> e depois atualizei a versão usando:

<pre class="brush: bash; title: ; notranslate" title="">hg pull
hg update
</pre>

Editei no mkconfig o ROOT para o diretorio /home/paolo/inferno-os, SYHOST=Linux e OBJTYPE=386  
Depois meti um ./makemk.sh para buildar o mk.  
setei o PATH adicionando o meu $ROOT/$SYSHOST/$OBJTYPE/bin para poder rodar o mk(que deve estar no path:  
export PATH=$PATH:/home/paolo/Linux/386/bin  
dei um **mk nuke** para limpar os objetos pre-existentes e mandei buildar tudo com **mk install**.

Não funcionou, parou em um certo ponto com o erro:

_sh: line 1: 7960 Floating point exception(core dumped)_

Depois de pesquisar um pouco e tentar muita coisa, descobri que o problema era a forma como o gcc estava lidando com a prevenção da divisão por zero, ele &#8220;otimizava&#8221; o asm original em Linux/386/include/fpuctl.h para para evitar a divisão por zero e zoava tudo. A solução era nao deixar ele otimizar e sim usar o asm puro, usando a diretiva &#8220;volatile&#8221; e adicionar uma saida (: &#8220;=a&#8221; (fcr)) a função, que nao retornava nada originalmente.

Agora sim, buildou que é uma maravilha! Só tentar um **$emu**:  
; wm/wm  
e temos uma versão funcional(e extremamente limitada e capada) do inferno OS  
[<img class="alignnone size-medium wp-image-386" src="{{ site.baseurl }}/uploads/2014/04/inferno-running.png?w=300" alt="inferno-running" width="300" height="230" srcset="{{ site.baseurl }}/uploads/2014/04/inferno-running.png 803w, {{ site.baseurl }}/uploads/2014/04/inferno-running-300x231.png 300w, {{ site.baseurl }}/uploads/2014/04/inferno-running-768x590.png 768w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/04/inferno-running.png)  
Agora a brincadeira começa ;D

_**Pequenos ajustes e configurações  
**_ Tive um problema em abrir algumas coisas, e pelos logs, percebi que nao haviam mais os diretorios fonts/lucida e fonts/lucidasans, presentes originalmente no 3e.tgz. Ao repor do tgz original, tudo funcionou como devia.  
Um outro erro constante era sobre o fato de nao encontrar meu home, ja que ele herda o nome de usuario do linux, copiei o diretório /usr/inferno para /usr/paolo e este problema tambem foi sanado.  
Uma coisa bem importante é setar os binários no seu PATH a nível de sistema, para isso, pus no meu ~/.profile:

PATH=&#8221;$PATH:$HOME/inferno-os/Linux/386/bin&#8221;

E ao se chamar o emu, ele simplesmente responde com o prompt ; porém, é fácil gerar um lançador fazendo no ~/.bashrc:  
alias inferno=&#8217;echo wm/wm | emu -g800x600&#8242;

Já para fazer um lançador do seu ambiente gráfico, é preferível fazer um bash script e chama-lo, fiz isso e adicionei este icone da vitanuova e voilá!  
[<img class="alignnone size-full wp-image-384" src="{{ site.baseurl }}/uploads/2014/04/vitanuova.png" alt="vitanuova" width="34" height="33" />]({{ site.baseurl }}/uploads/2014/04/vitanuova.png)  
[<img class="alignnone size-full wp-image-387" src="{{ site.baseurl }}/uploads/2014/04/menu-inferno.png" alt="menu-inferno" width="130" height="24" />]({{ site.baseurl }}/uploads/2014/04/menu-inferno.png)

_**  Limbo**_  
A linguagem limbo é bem completa e complexa para ser definida aqui, então deixo o link de um livro, Inferno Programming with Limbo, escrito por Phillip Stanley-Marbell da Carnegie Mellon University e publicado pela Wiley em 2003. O livro é gratis, mas existe uma versão em papel disponível na amazon: <http://www.amazon.com/gp/product/0470843527?ie=UTF8&tag=catv-20&linkCode=as2&camp=1789&creative=9325&creativeASIN=0470843527>. Ah!, o link do pdf gratis do livro: [http://doc.cat-v.org/inferno/books/inferno\_programming\_with\_limbo/Inferno\_Programming\_With\_Limbo.pdf](http://doc.cat-v.org/inferno/books/inferno_programming_with_limbo/Inferno_Programming_With_Limbo.pdf) e o treco tem 22MB.

Pensem no Inferno OS como um Java que, alem da simples linguagem, tambem tem todo um SO rodando sobre, com uma abordagem diferenciada dos sistemas normalmente usados. Alem do fato de ser interessante desenvolver projetos encapsulados pelo Inferno OS, a forma como o sistema usa a rede é interessante para muitas aplicaçoes, inclusive a Lucent usa Inferno OS embarcado em varios produtos, desde roteador a set-top-box.
