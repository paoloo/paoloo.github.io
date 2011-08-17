---
title: Instalando o Firefox 6 no fedora 14
date: 2011-08-17T17:10:41+00:00
author: paolo
layout: post
permalink: /2011/08/17/instalando-o-firefox-6-no-fedora-14/
categories:
  - pt-BR
tags:
  - comp
  - fedora
---
Para o fedora 14, primeiro instale o repositorio do Remi Collet([http://blog.famillecollet.com/pages/Config-en](http://blog.famillecollet.com/pages/Config-en "http://blog.famillecollet.com/pages/Config-en")), um frances membro do tipo de empacotadores que empacota todo firefox novo praticamente no mesmo dia do release.

<pre class="brush: bash; title: ; notranslate" title="">rpm -Uvh http://rpms.famillecollet.com/remi-release-14.rpm
</pre>

Agora verifica-se a versão disponível do firefox:

<pre class="brush: bash; title: ; notranslate" title="">yum --enablerepo=remi list firefox
</pre>

No meu caso, eu estava usando a 3.6 e havia disponível a 6.0-1

<pre class="brush: plain; title: ; notranslate" title="">Installed Packages
firefox.i686                      3.6.18-1.fc14                         @updates
Available Packages
firefox.i686                      6.0-1.fc14.remi                       remi
</pre>

Finalmente, só instalar:

<pre class="brush: bash; title: ; notranslate" title="">yum --enablerepo=remi install firefox
</pre>

&nbsp;

<pre class="brush: plain; title: ; notranslate" title="">...
Dependencies Resolved

================================================================================
 Package             Arch          Version                  Repository     Size
================================================================================
Updating:
 firefox             i686          6.0-1.fc14.remi          remi           18 M
Installing for dependencies:
 xulrunner6          i686          6.0-1.fc14.remi          remi           11 M
...
</pre>

No final do download ele vai pedir para autorizar a key do Remi no yum, so dar um sim.

<pre class="brush: plain; title: ; notranslate" title="">warning: rpmts_HdrFromFdno: Header V3 DSA/SHA1 Signature, key ID 00f97f56: NOKEY
remi/gpgkey                                              | 2.6 kB     00:00 ...
Importing GPG key 0x00F97F56:
 Userid : Remi Collet &lt;RPMS@FamilleCollet.com&gt;
 Package: remi-release-14-6.fc14.remi.noarch (installed)
 From   : /etc/pki/rpm-gpg/RPM-GPG-KEY-remi
Is this ok [y/N]:
</pre>

Eu particularmente gostei do Firefox 6, está bem mais rapido e com menor consumo de memória. Se vai voltar a ser o que era antes do chrome, eu nao sei. Mas espero grandes coisas dele.  
E eu aconselho manter o repositório do Remi pois segundo o pessoal da mozilla, eles vao continuar fazendo update como loucos até a versão bater com a do chrome(hoje, na 14) entao tem bastante update por vir haha.