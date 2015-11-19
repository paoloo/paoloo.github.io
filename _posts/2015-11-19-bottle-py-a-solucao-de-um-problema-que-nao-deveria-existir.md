---
title: 'Bottle.py - a solução de um problema que nao deveria existir'
date: 2015-11-19T11:32:28+00:00
author: paolo
layout: post
permalink: /2015/11/19/bottle-py-a-solucao-de-um-problema-que-nao-deveria-existir/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - comp
  - python
  - uC
  - web
---
**Bottle**( <http://bottlepy.org/docs/dev/index.html> ) é um micro web framwork em python leve e muito simples. O mais louco é que ele é distribuido em apenas um arquivo e não tem nenhuma dependencia, alem do interpretador python, o que facilita absurdamente o deploy em qualquer ambiente!!!
Ok, e dai?
Bem, vi muita gente fazendo deploy no raspberryPi de aplicações com front end web, usando apache, php, mysql, postgres, redis, ou até mesmo obscenidades como o tomcat. Por enquanto, isto não é punido com a morte, mas deve ser evitado a todo custo e se buscar leveza e simplicidade. Quando conheci o bottle, tive a certeza que isto que procurava!

Com suporte a templates, roteamento simplificado, gerenciamento de dados e um servidor built-in, não fica faltando nada para sua aplicação subir.

para instalar (deixar o .py no diretorio ou instalar via pip, com # pip install bottle) e ter várias ideias de uso, é muito bom perder um tempinho na página oficial, mas uma aplicação que me deixou emocionado foi fazer uma pseudo-API do GPIO para web, simples assim:

<pre class="brush: plain; title: ; notranslate" title="">cat &gt; webgpio.py &lt;&lt; _EOF_
from bottle import route
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

@route('/le/&lt;pino:int&gt;')
def readgpio(pino):
    GPIO.setup(pino, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    saida = GPIO.input(pino)
    return '&lt;pinos&gt;&lt;%d&&gt;%s&lt;/%d&gt;&lt;/pinos&gt;' % (pino,str(saida),pino)

@route('/escreve/&lt;pino:int&gt;/&lt;val:int&gt;')
def writegpio(pino,val):
    GPIO.setup(pino, GPIO.OUT)
    if val==0 or val ==1:
        GPIO.output(pino, (GPIO.LOW , GPIO.HIGH)[val])
        return 'escrito %d no pino %d' % (val, pino)
    else:
        return 'valores validos para escrita: 0 e 1'
_EOF_
</pre>

Rodando&#8230;

<pre class="brush: plain; title: ; notranslate" title="">$ python webgpio.py 
Bottle v0.13-dev server starting up (using WSGIRefServer())...
Listening on http://localhost:8080/
Hit Ctrl-C to quit.

127.0.0.1 - - [19/Nov/2015 02:20:48] "GET /le/13 HTTP/1.1" 200 26
127.0.0.1 - - [19/Nov/2015 02:21:04] "GET /escreve/15/0 HTTP/1.1" 200 20
127.0.0.1 - - [19/Nov/2015 02:21:14] "GET /escreve/15/1 HTTP/1.1" 200 20
</pre>

E fazendo os requests&#8230;

<pre class="brush: plain; title: ; notranslate" title="">$ curl http://localhost:8080/le/13
&lt;pinos&gt;&lt;13&gt;12.5&lt;/13&gt;&lt;/pinos&gt;
$ curl http://localhost:8080/escreve/15/1
escrito 1 no pino 15
$ curl http://localhost:8080/escreve/15/2
valores validos para escrita: 0 e 1
</pre>

Obviamente este código não é seguro nem otimizado, é apena um PoC. Mas ainda assim, este treco é lindo, leve e tem suporte a muita coisa. Se a interface de template dele não agradar, ele é facilmente integravel com o **jinja2**( <http://jinja.pocoo.org/docs/dev/> ) e, principalmente para linux embarcado é o framework web definitivo(ok, isso é minha opinião pessoal, mas é o que realmente parece haha).
