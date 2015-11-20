---
title: Serviço de checagem de CPF em bash script+python
date: 2015-11-20T20:03:15+00:00
author: paolo
layout: post
permalink: /2015/11/20/servico-de-checagem-de-cpf-em-bash-scriptpython/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - bash
  - hacks
  - python
---
Analisando um app de iPhone(depois mostro o passo a passo e as ferramentas), me vi precisando escrever um teste rápido no bash com o curl, que é uma ferramente absolutamente excepcional, mas me ví com problemas deevido a geração do HMAC e fazer parsing do resultado(sed+awk+cut é meio doloroso ne).  
Acabei fazendo algo meio hibrido assim:

<pre class="brush: plain; title: ; notranslate" title="">#!/bin/bash
cpfHASH=`echo "$1 $2" | python -c "from hashlib import sha1; from hmac import new as hmac; import sys; v=sys.stdin.read().strip().split(' '); print hmac('Sup3RbP4ssCr1t0grPhABr4sil','%s%s' % (v[0],v[1]),sha1).digest().encode('hex')"`

saidA=`curl https://movel01.receita.fazenda.gov.br/servicos-rfb/v2/IRPF/cpf -s -k -H "token: $cpfHASH" -H "plataforma: iPhone OS" -H "dispositivo: iPhone" -H "aplicativo: Pessoa Física" -H "versao: 8.3" -H "versao_app: 4.1" -d "cpf=$1&dataNascimento=$2" 2&gt;&1`

python -c "null=None; a=$saidA; print ''.join(['%s = %s\n' % (c,a) for c in a])"
</pre>

Ficou meio porco usar o python para gerar o hash e para fazer o parsing, mas resolveu o meu problema. A execução é simples, o chato é que requer, além do CPF, a data de nascimento. Mas futuramente integrarei uma ferramenta para conseguir esta informação ;D

<pre class="brush: plain; title: ; notranslate" title="">$ ./cpf.sh 13326724691 14121947
horaConsulta = 20:49:31
exception = None
codigoRetorno = 00
mensagemRetorno = OK
dataIsncricao = anterior a 10/11/1990
digitoVerificador = 00
nome = DILMA VANA ROUSSEFF
dataEmissao = 20/11/2015
horaEmissao = 08:49:32
mensagemObito = None
anoObito = 0000
codigoControle = CCA9.63A0.C92D.1C0D
codSituacaoCadastral = 0
dataConsulta = 20/11/2015
descSituacaoCadastral = REGULAR
dataNascimento = 14/12/1947
</pre>

O código se encontra em https://github.com/paoloo/servicos/blob/master/cpf.sh

o/