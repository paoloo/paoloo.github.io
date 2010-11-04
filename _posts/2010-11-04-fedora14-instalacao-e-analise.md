---
title: 'fedora14: instalação e análise'
date: 2010-11-04T00:46:08+00:00
author: paolo
layout: post
permalink: /2010/11/04/fedora14-instalacao-e-analise/
categories:
  - pt-BR
tags:
  - comp
  - fedora
---
Venho esperando o fedora14 a bastante tempo, não migrei para o 13 por muitos fatores mas comecei a testar o 14 desde o inicio e sempre estive bem satisfeito. A instalação foi rapida e limpa, como nos ultimos releases, e reconheceu praticamente todo o meu hardware (um Asus eeepc 1001HA) out of the box. Entretanto manteve o probleminha com o hook fn+f2, usado para habilitar o wifi(veja a solucao [aqui](http://paoloo.wordpress.com/2010/11/04/fedora-e-a-saga-do-wifi-perdido/) ).  
Outro problema, tambem herdado do fedora12: o vlc nao ativa um lock no screensaver possibilitando que este se ative durante a execução de um filme, o que é bastante irritante. A solução simples é adicionar o script &#8220;vlc&#8221; a seguir, em /usr/local/bin/

<pre class="brush: bash; title: ; notranslate" title="">#!/bin/sh
gnome-screensaver-command -i -n vlc -r &quot;playing video&quot; &amp;
pid=$!
stop_inhibitor(){
	kill $pid
}
trap stop_inhibitor SIGINT SIGTERM
/usr/bin/vlc &quot;$@&quot;
stop_inhibitor
</pre>

Desta forma, ao ser inciado, este script tem precedencia e impede o screensaver de se ativar.  
Um outro detalhe importante é o touchpad, cujo hardware suporta multi-touch, porém a opção no gerenciador, nao. Depois de saber que [este commit no kernel](http://git.kernel.org/?p=linux/kernel/git/torvalds/linux-2.6.git;a=commitdiff;h=2a8e77102e02dd236ff276a2151073ed551d04f2 "commit no kernel") e [este no xf86-input-synaptics](http://cgit.freedesktop.org/xorg/driver/xf86-input-synaptics/commit/?id=ffa6dc2809734a6aaa690e9133d6761480603a68 "commit no synaptic") permitam que o multi-touch seja usado, o único problema restante é a impossibilidade de selecionar a opção no gerenciador, que pode ser resolvida assim:

<pre class="brush: bash; title: ; notranslate" title="">gconftool-2 --set /desktop/gnome/peripherals/touchpad/scroll_method --type int &quot;2&quot;</pre>

(o valor original é 1). Pronto, despois disso o multi-touch funcionou como magica ;D  
Entao comecei as instalações. Primeiro, os repositorios extras:

<pre class="brush: bash; title: ; notranslate" title="">rpm -ivh http://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-stable.noarch.rpm http://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-stable.noarch.rpm</pre>

depois adicionar o repositorio do google-chrome:

<pre class="brush: bash; title: ; notranslate" title=""># cat &lt;&lt; EOF &gt;&gt; /etc/yum.repos.d/google.repo
[google]
name=Google - i386
baseurl=http://dl.google.com/linux/rpm/stable/i386
enabled=1
gpgcheck=1
gpgkey=https://dl-ssl.google.com/linux/linux_signing_key.pub
EOF
# yum install google-chrome-beta</pre>

e o repositorio do skype:

<pre class="brush: bash; title: ; notranslate" title=""># cat &lt;&lt; EOF &gt;&gt; /etc/yum.repos.d/skype.repo
[skype]
name=Skype Repository
baseurl=http://download.skype.com/linux/repos/fedora/updates/i586/
gpgkey=http://www.skype.com/products/skype/linux/rpm-public-key.asc
enabled=1
gpgcheck=0
EOF
# yum install skype
</pre>

Depois disso, deixei o Rhytmbox abrir uma mp3 e baixar os codecs. Então, instalei o basico do basico:

<pre class="brush: bash; title: ; notranslate" title="">yum install unrar p7zip vlc proxychains tor privoxy vim ffmpeg leafpad</pre>

Dai veio o nautilus, primeiro o open-terminal-here(que deveria ser parte integrada dele)

<pre class="brush: bash; title: ; notranslate" title="">yum install nautilus-open-terminal </pre>

Só que agora, o nautilus vem sem a opção de texto na location bar, para adicionar:

<pre class="brush: bash; title: ; notranslate" title="">gconftool-2 --type=Boolean --set /apps/nautilus/preferences/always_use_location_entry true</pre>

Continuei a instalar itens que deveriam vir como padrão: editor de menu( alacarte ) e as ferramentas do SELinux:

<pre class="brush: bash; title: ; notranslate" title="">yum install alacarte setools-console policycoreutils-gui </pre>

Depois disso, foi so pegar o backup de volta, instalar o truecrypt, por as coisas no lugar e curtir o fedorazão 14 o/.

Reitero que estou muito feliz com essa versão do fedora, entretanto, sinto falta de bastante coisa, como o talika(extensão do gnome que permite exibir as janelas abertas como um unico icone) que trava o gnome-bar se for incluido na barra, ou um bug no layout do teclado que o faz mudar sozinho(este **ainda** nao consertei ;D). De forma que uma analise mais correta só poderá ser feita em algumas semanas, depois do updates e patches e ver os rumos que tudo vai tomar.

**EDIT: (10 de novembro)** Depois de seis dias de uso intenso eu estou apto a dar minhas impressões.  
**Primeiro**, o gráfico. As mudanças foram ótimas, o tema e os icones estão mais bem acabados, o sistema esta mais visualmente bonito como um todo. É uma mudança incomum no fedora que geralmente deixa esses detalhes graficos de lado. E a libjpg-turbo&#8230; nossa! que diferença ela faz! a renderização de imagens dobrou a velocidade. Muito bom. Ah, e joguinhos que nao funcioavem no fedora 12 agora rodam lindamente&#8230; coisa linda o/  
**Segundo:** meu probleminha com o teclado se resolveu sozinho em algum update. deve ter sido algum conflito, não importa, não existe mais ;D  
**Terceiro:** Os crashes do kernel que ocorriam no fedora 12 quando eu ficava alternando rapidamente entre as varias conexoes e vpns, nao acontecem mais. A estabilidade no gerenciamento de conexões foi a primeira coisa que eu percebi, inclusive.  
**Quarto e ultimo:** O lado ruim. Primeiro o não funcionamento do talika, que na minha opinião deveria ser uma opção oficial do gnome-panels. Depois o fato de muitos pacotes nao acharem suas dependencias, mesmo elas estando instaladas. Eu nao sei exatamente porque isso ocorre, e geralmeute eu resolvo isso com uma gambiarra feia(fazendo links simbolicos em toda parte ate o software achar), mas isso, que acontece principalmente com pacotes antigos, pode ser uma incompatibilidade que deverá se resolver a medida que as coisas forem repacotadas para o fedora 14.  
Finalmente, minha impressão: **O fedora melhorou incrivelmente entre as versões 12 e 14.** Mesmo nao tendo inserido o novo gnome, muita coisa mudou e para melhor. Ainda nao testei o ambiente de virtualização mas em breve o farei e postarei os resultados.

o/