---
title: Python + SSL para aplicações simples
date: 2016-01-19T01:44:46+00:00
author: paolo
layout: post
permalink: /2016/01/19/python-ssl-para-aplicacoes-simples/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - bash
  - comp
  - python
---
Precisei relembrar uma forma de gerar uma conexão SSL(não apenas a camada de aplicação) para um projeto. O python faz isso de forma muito fluida e simples. Não requer prática, tampouco habilidade haha.

Para gerar o certificado, primeiro geramos uma chave com o openssl. Depois a usamos para gerar um certificado. Uma forma direta e automatica(e insegura, ja que não ha dados no certificado gerado) de fazer isso é:

<pre class="brush: bash; title: ; notranslate" title="">openssl genrsa -out key.pem
yes '' | openssl req -new -x509 -key key.pem -out crt.pem -days 36500 || exit 1
cat key.pem crt.pem &gt; cert.pem
rm key.pem crt.pem
</pre>

Lembrando que estou ignorando as entradas para gerar o cert. Este tipo de coisa é mais usado para automatizar e gerar um cert novo a cada sessão. Depois disto é necessario pegar o fingerprint da chave, assim:

<pre class="brush: bash; title: ; notranslate" title="">openssl x509 -in cert.pem -md5 -fingerprint -noout | sed 's/^[^=]\+=//;s/://g' | tr 'A-Z' 'a-z'
</pre>

Agora o servidor, extremamente simples, para apenas uma conexão e printar o dado enviado:

<pre class="brush: python; title: ; notranslate" title="">import socket, ssl
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', 8081))
sock.listen(1)
newsock, fromaddr = sock.accept()
conn = ssl.wrap_socket(newsock, server_side=True, certfile='cert.pem', keyfile='cert.pem')
conn.setblocking(0)
while True:
    try:
        buf = conn.read(512)
        if buf == '':
            break
        else:
            print buf
    except:
        pass
</pre>

O cliente é tão simples quanto o servidor. Só lembrar de pegar o fingerprint gerado e usar no client. Ele verifica e só loga no servidor se bater o fingerprint.

<pre class="brush: python; title: ; notranslate" title="">import socket, ssl, hashlib, time
CERT="fingerprint que voce pegou"
sock = socket.socket()
sock.settimeout(2)
sock.connect(('localhost', 8081))
conn = ssl.wrap_socket(sock)
if hashlib.md5(conn.getpeercert(True)).hexdigest() != CERT:
    conn.close()
    print 'CERT diferente do esperado, tentando me hackearrrrrrr'
else:
    print '200 OK'
    time.sleep(2)
    conn.write('CHUPA ESSA MANGA, WIRESHARK!1!!')
    print 'enviado'
    conn.close()
</pre>

E é só isso, bem simples. É uma forma de encriptação e autenticação bem razoavel e resolve para a maioria das aplicações práticas contemporaneas.

link dos sources em : https://github.com/paoloo/simple-ssl