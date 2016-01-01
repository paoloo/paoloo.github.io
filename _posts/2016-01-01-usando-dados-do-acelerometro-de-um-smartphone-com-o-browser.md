---
title: Usando dados do acelerômetro de um smartphone com o browser
date: 2016-01-01T20:10:32+00:00
author: paolo
layout: post
permalink: /2016/01/01/usando-dados-do-acelerometro-de-um-smartphone-com-o-browser/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - android
  - uC
  - web
---
Enquanto migrava meus nós de uma **Rede de Sensores sem Fio** baseada em **802.15.4** para &#8220;Internet of Things&#8221; baseado em **802.11**, principalmente em aplicações voltadas a robótica e movimento, onde os dados do acelerometro eram requeridos, precisei constantemente usar o Android Studio ou o APPinventor do MIT, e isso é algo contraproducente. Procurando alternativas mais diretas, acabei conhecendo o evento &#8216;devicemotion&#8217; do javascript, e isso tornou as coisas muito mais divertidas!  
Saber se o evento é suportado(tentei em muitos devices e é em todos) é bem fácil:

<pre class="brush: jscript; title: ; notranslate" title="">if (window.DeviceMotionEvent) {
  document.getElementById("INFO").innerHTML = "Acelerometro suportado"
} else {
  document.getElementById("INFO").innerHTML = "Acelerometro não suportado"
}
</pre>

E usá-lo é ainda mais fácil:

<pre class="brush: jscript; title: ; notranslate" title="">window.addEventListener('devicemotion', dmHandler, false);
</pre>

O evento é hookado e chama uma função, dmHandler no caso, para tratá-lo. Uma exemplo de um handler seria:

<pre class="brush: jscript; title: ; notranslate" title="">function dmHandler(eventData) {
  acceleration = eventData.accelerationIncludingGravity;
  var left = 0; var right = 0;
  if (Math.abs(acceleration.y) &gt; 1) {
    var speed = acceleration.y * 123;
    left = Math.min(1023, speed + acceleration.x * 100);
    right = Math.min(1023, speed - acceleration.x * 100);
  } else if (Math.abs(acceleration.x) &gt; 1) {
    var speed = Math.min(1023, Math.abs(acceleration.x) * 123);
    if (acceleration.x &gt; 0) {
      left = speed; right = -speed; 
    } else {
      left = -speed; right = speed;
    }
  }
  var direcao = "";
  direcao = "[" + Math.round(acceleration.x) + "," + Math.round(acceleration.y) + "," + Math.round(acceleration.z) + "]&lt;BR/&gt;" + Math.round(left) + ", " + Math.round(right); 
  document.getElementById("MOSTRA").innerHTML = direcao;
}
</pre>

Depois disso, so chamar uma outra função para transferir os dados para o dispositivo:

<pre class="brush: jscript; title: ; notranslate" title="">var _ultimo = 0;
function diz(_esquerda, _direita) {
  var now = Date.now();
  if (_ultimo + 200 &lt; now) {
     _ultimo = now; 
     var _req = new XMLHttpRequest();
     _req.open('GET', '/go/' + Math.round(_esquerda) + "," + Math.round(_direita), true);
     _req.send(null);
  }
}
</pre>

E colocando tudo junto:

<pre class="brush: jscript; title: ; notranslate" title="">&lt;!DOCTYPE HTML&gt;
&lt;html&gt;&lt;head&gt;
&lt;/head&gt;&lt;body&gt;
&lt;div id="INFO"&gt;&lt;/div&gt;
&lt;br/&gt;
&lt;div id="MOSTRA"&gt;&lt;/div&gt;
&lt;br/&gt;
&lt;script type='text/javascript'&gt;
if (window.DeviceMotionEvent) {
  window.addEventListener('devicemotion', dmHandler, false);
  document.getElementById("INFO").innerHTML = "Acelerometro suportado"
} else {
  document.getElementById("INFO").innerHTML = "Acelerometro nao suportado"
}
var _ultimo = 0;
function diz(_esquerda, _direita) {
  var now = Date.now();
  if (_ultimo + 200 &lt; now) {
     _ultimo = now; 
     var _req = new XMLHttpRequest();
     _req.open('GET', '/go/' + Math.round(_esquerda) + "," + Math.round(_direita), true);
     _req.send(null);
  }
}

function dmHandler(eventData) {
  acceleration = eventData.accelerationIncludingGravity;
  var left = 0; var right = 0;
  if (Math.abs(acceleration.y) &gt; 1) {
    var speed = acceleration.y * 123;
    left = Math.min(1023, speed + acceleration.x * 100);
    right = Math.min(1023, speed - acceleration.x * 100);
  } else if (Math.abs(acceleration.x) &gt; 1) {
    var speed = Math.min(1023, Math.abs(acceleration.x) * 123);
    if (acceleration.x &gt; 0) {
      left = speed; right = -speed; 
    } else {
      left = -speed; right = speed;
    }
  }
  var direcao = "";
  direcao = "[" + Math.round(acceleration.x) + "," + Math.round(acceleration.y) + "," + Math.round(acceleration.z) + "]&lt;BR/&gt;" + Math.round(left) + ", " + Math.round(right); 
  document.getElementById("MOSTRA").innerHTML = direcao;
}
&lt;/script&gt;
&lt;/body&gt;&lt;/html&gt;
</pre>

E no meu embarcado, estou usando o bottle( <https://paoloo.wordpress.com/2015/11/19/bottle-py-a-solucao-de-um-problema-que-nao-deveria-existir/> ) para gerenciar:

<pre class="brush: python; title: ; notranslate" title=""># -*- coding: utf-8 -*-
from bottle import request, route, run, static_file

@route('/')
def get_BASEdata():
    return static_file("loader.html", root="./")

@route('/go/&lt;d&gt;')
def get_SENTdata(d):
    print d # ou faz algo mais util, como enviar os valores para o controlador dos motores
    return d

run(host='0.0.0.0', port=8080, debug=True)
</pre>

E é isso. Simples, direto e não requer nada além de um browser!