---
title: Fedora 16 XFCE Spin
date: 2011-11-10T22:38:43+00:00
author: paolo
layout: post
permalink: /2011/11/10/fedora-16-xfce-spin/
categories:
  - pt-BR
tags:
  - comp
  - fedora
---
Depois de quase desistir do Fedora em face do desrespeito representado pelo gnome 3, fiz uma outra tentativa, com o spin xfce. O nível de satisfação nao é o mesmo do gnome2 mas está muito além da sensação de usar o gnome 3.  
Mas uma vez usei o Asus EEEPC 1001HA e e fedora, como sempre, teve uma instalação muito tranquila. Tudo foi instalado out-of-box, com excessão do som, que requereu trocar a placa de som para a &#8216;internal audio analog stereo (pulseAudio mixer)&#8217; nas propriedades do som. E me surpreendi com a wifi, desta vez o fedora reconheceu bonitinho, sem nenhuma configuração adicional, bem como reconheceu todos as combinações do Fn e o vlc inibe o screensaver de ser ativado(coisa que no gnome2 requeria script adicional).  
O multitouch ja funciona out-of-box mas para habilitar o click em um toque no touchpad é necessário editar o arquivo _/usr/share/X11/xorg.conf.d/50-synaptics.conf_ (como root, óbvio), procurar pela Seção &#8220;_InputClass_&#8221; contendo o parametro:

<pre class="brush: plain; title: ; notranslate" title="">Identifier &quot;touchpad catchall&quot;
</pre>

e adicionar:

<pre class="brush: plain; title: ; notranslate" title="">Option &quot;TapButton1&quot; &quot;1&quot;
</pre>

antes do &#8220;_EndSection_&#8220;. Reiniciar e pronto.  
Outra dificuldade foi edição de menu. O editor mais funcional que encontrei foi o lxmed(http://lxmed.sourceforge.net/) porém veio com dois defeitos: um erro de digitacao e o problema de nao haver gksu no fedora. A solucao foi editar o arquivo /usr/bin/lxmed e corrigir a linha 16(adicionando apenas um $, fazendo DISTRO=$REDHAT), instalar o beesu(_yum install beesu_) e substituir o gksu por beesu no codigo. Entretanto, para editar os diretorios(adicionar,remover&#8230;), é necessário usar o arquivo xml  
/etc/xdg/menus/xfce-applications.menu e adicionar conferme os que já estão lá.  
Outra coisa estranha é que, embora ele reconheça outros monitores e datashow, ele não os habilita por default. É necessario ir nas propriedades do display e habilitar na mão. Pelo menos da primeira vez.  
Fora isso, o uso do XFCE não é do mesmo nível do gnome, faltam muitos ajustes finos. Mas o downgrade para o XFCE é ainda infinitamente mais decente que o suposto upgrade para o gnome3. O gerenciamento de energia tambem não é muito bom, mas espero grandes coisas do XFCE.  
Depois disso, ocorreu a instalação normal de sempre. Primeiro os repositórios extras:

<pre class="brush: bash; title: ; notranslate" title="">rpm -ivh http://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-stable.noarch.rpm http://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-stable.noarch.rpm
</pre>

depois adicionar o repositorio do google-chrome:

<pre class="brush: bash; title: ; notranslate" title=""># cat &lt;&lt; EOF &gt;&gt; /etc/yum.repos.d/google.repo
[google]
name=Google - i386
baseurl=http://dl.google.com/linux/rpm/stable/i386
enabled=1
gpgcheck=1
gpgkey=https://dl-ssl.google.com/linux/linux_signing_key.pub
EOF
# yum install google-chrome-beta
</pre>

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

e o basicão:

<pre class="brush: bash; title: ; notranslate" title="">yum install unrar p7zip vlc proxychains tor privoxy vim ffmpeg
</pre>

Agora estou testando o Fedora 16 XFCE Spin e vamos ver no que dá.

[Sourcecode]