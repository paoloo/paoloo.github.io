---
title: fedora e a saga do wifi perdido
date: 2010-11-04T00:32:19+00:00
author: paolo
layout: post
permalink: /2010/11/04/fedora-e-a-saga-do-wifi-perdido/
categories:
  - pt-BR
tags:
  - comp
  - fedora
  - hacks
---
Já faz quase um ano que migrei para o fedora e, até agora, tenho bem pouca coisa a reclamar, mas uma que me deu bastante dor de cabeça no passado foi o &#8216;esquecimento&#8217; de como funcionava minha wifi.  
Eu uso um eeepc 1001HA, um hardware bem &#8216;conhecido&#8217;  e nao havia razao para isto acontecer. O fato é que ao iniciar meu uso no fedora12, tudo funcionava lindamente, mas um belo dia, um update de kernel pos tudo a perder: ele simplesmente ignorava a existência do meu wifi. Depois de muito bater a cabeça, cheguei a uma solução. Gambiarra, seria um termo melhor.  
Primeiro, desabilitei a trava de hardware do wifi na BIOS. Depois disso, ao bootar, o wifi ficava sempre ativo. Ou seja, o driver estava funcionando, apenas o hook não. O próximo passo logico seria criar o hook. Depois de muita raiva, eis o hook:

<pre class="brush: bash; title: ; notranslate" title="">rfkill list | awk 'BEGIN{left=0}/Wireless LAN/{left=3}{if(left){if(match($0,/Soft blocked: (yes|no)/,a)){if(a[1]==&quot;yes&quot;)system(&quot;rfkill unblock wifi&quot;);else system(&quot;rfkill block wifi&quot;);};left--;}}'</pre>

Agora tinha o problema de iniciar isso junto com o sistema. O passo obvio seria torna-lo um serviço do fedora. Primeiro criei o script:

<pre class="brush: bash; title: ; notranslate" title="">#!/bin/bash
## wifi        Gambi para resolver bug tosco na ativacao do wifi no eeepc
#
# Author: Paolo Oliveira
#
# chkconfig: 2345 20 80
#
# BEGIN INIT INFO
# Provides: wifi
# Required-Start: $local_fs $remote_fs $network $named
# Required-Stop: $local_fs $remote_fs $network
# Should-Start: distcache
# Short-Description: start and stop wifi software lock
# Description: Solve ridiculous bug on newer linux on wifi activation
#  (a very very creepy bug).
### END INIT INFO
# Source function library..
/etc/rc.d/init.d/functions
start() {
echo -n $&quot;Starting Wlan: &quot;
rfkill block wifi
RETVAL=$?
}
stop() {
	echo -n $&quot;Stopping Wlan: &quot;
	rfkill unblock wifi
RETVAL=$?
}
status() {
rfkill list | awk 'BEGIN{left=0}/Wireless LAN/{left=3}{if(left){if(match($0,/Soft blocked: (yes|no)/,a)){if(a[1]==&quot;yes&quot;)print &quot;WIFI: [OFF]&quot;;else print &quot;WIFI: [ON]&quot;;};left--;}}'
RETVAL=$?
}
reload() {
echo -n $&quot;Reloading not available: &quot;
RETVAL=$?
}
# See how we were called.
case &quot;$1&quot; in  start)
	start
	;;
stop)
	stop
	;;
status)
status
	;;
restart)
	stop
	start
	;;
condrestart|try-restart)
	reload
	;;
force-reload|reload)
reload
	;;
graceful|help|configtest|fullstatus)
	echo &quot;boo&quot;
	RETVAL=$?
	;;
*)
	echo $&quot;Usage: $prog {start|stop|restart|help}&quot;
	RETVAL=3
esac
exit $RETVAL</pre>

E, para finalizar, mandei o chkconfig cuidar do boot:  
**chkconfig &#8211;add wifi && chkconfig &#8211;level 2345 wifi on**  
e adicionei nas &#8216;hotkeys&#8217; do fedora, tecla do windows+f2 para acessar o hook(habilitando e desabilitando o wifi on-the-fly).  
Final feliz ;D

**EDIT: (8 de Novembro)** Ao bootar depois de um update do conectionMenager, o &#8220;truque&#8221; da tecla de windows+f2 nao funcionou. Checkei desesperado com o rfkill que informou que tanto a trava de hardware quanto a de software estavam off. Então, depois de olhar dmesg, fazer despacho para matarem alguem aleatorio na red hat, percebi que o update simplesmente desabilitou a opção wireless no gerenciador(LOL) e a solução foi clicar com o botão direito sobre a conexao(na barra do gnome) e selecionar &#8220;enable wireless&#8221;. Simples e WTF. Mas fica a informação haha