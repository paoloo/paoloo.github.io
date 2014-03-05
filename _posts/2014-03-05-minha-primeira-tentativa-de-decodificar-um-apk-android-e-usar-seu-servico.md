---
title: Minha primeira tentativa de decodificar um apk android e usar seu serviço
date: 2014-03-05T03:00:09+00:00
author: paolo
layout: post
permalink: /2014/03/05/minha-primeira-tentativa-de-decodificar-um-apk-android-e-usar-seu-servico/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - android
  - hacks
  - python
---
_**UPDATE 15/maio/2014** no final do arquivo!  
**UPDATE 20/novembro/2015** no final do arquivo!  
_ 

Escolhi como meu primeiro alvo a aplicaçao:  
<https://play.google.com/store/apps/details?id=br.gov.sinesp.cidadao.android>  
que checa os dados das placas dos carros e diz qual carro é. Algo bem inocente ;D  
Depois de baixar o br.gov.sinesp.cidadao.android.apk e checar sua estrutura interna, pude ver que apenas classes.dex, resources.arsc e AndroidManifest.xml eram interessantes.  
Primeiro procurei uma ferramente para transformar o dex em jar. Pela ordem das pesquisas no google, tentei inicialmente o apktool( <http://android-apktool.googlecode.com/files/apktool1.5.2.tar.bz2> ), mas nao funcionou, deu trocentos erros. Passei para o dex2jar( <http://dex2jar.googlecode.com/files/dex2jar-0.0.9.15.zip> )&#8230; esse funcionou como mágica e gerou o classes_dex2jar.jar, que abri com o jd-gui ( <http://jd.benow.ca/jd-gui/downloads/jd-gui-0.3.5.linux.i686.tar.gz> ). Comecei a explorar.  
Iniciando em **br.gov.sinesp.cidadao**, vi que **android.*** nao tinha nada interessante. Mas tanto **util.Hash** quanto **cordova.plugin.InfoAplicacaoPlugin** pareciam promissores.  
Comecei, lógico, pelo Hash.

<pre class="brush: java; title: ; notranslate" title="">public class Hash
{
public static String generateHash(String paramString1, String paramString2)
{
SecretKeySpec localSecretKeySpec = new SecretKeySpec(paramString1.getBytes(), "HmacSHA1");
try
{
Mac localMac = Mac.getInstance("HmacSHA1");
localMac.init(localSecretKeySpec);
byte[] arrayOfByte = localMac.doFinal(paramString2.getBytes());
new Hex();
String str = new String(Hex.encode(arrayOfByte), "UTF-8");
return str;
}
...
</pre>

Um método bem simples que usa **HMAC**(Hash-based Message Authentication Code) para gerar o hash encodado em hexa vindo de dois parametros (paramString1 e paramString2). Implementar HMAC em python e hex encodar a saida é trivial:

<pre class="brush: python; title: ; notranslate" title="">from hashlib import sha1
from hmac import new as hmac
generateHash = lambda(placa): hmac(paramString1, paramString2, sha1).digest().encode('hex')
</pre>

Agora é achar o diacho destes paramString1 e paramString2.  
Através da documentação do PhoneGap( [http://docs.phonegap.com/en/2.0.0/guide\_plugin-development\_android_index.md.html](http://docs.phonegap.com/en/2.0.0/guide_plugin-development_android_index.md.html) ), cheguei a classe Plugin, que deve ser chamado no javascript da view da aplicação. O formato do chamado ao plugin é:

<pre class="brush: jscript; title: ; notranslate" title="">exec(&lt;successFunction&gt;, &lt;failFunction&gt;, &lt;service&gt;, &lt;action&gt;, [&lt;args&gt;]);
</pre>

Ou seja, a função chamada caso o request seja um sucesso, caso ele falhe, o serviço, ação e os parametros. Não encontrei no código original os parametros tais quais estão definidos, porem na classe InfoAplicacaoPlugin que extende CordovaPlugin e que está em /br/gov/sinesp/cidadao/cordova/plugin/, encontrei as definiçoes dos plugins, especialmente:

<pre class="brush: java; title: ; notranslate" title="">public final String ACTION_GET_APP_INFO = "getAppInfo";
public final String ACTION_GET_TOKEN = "getToken";
...
private String chave = "sheacsrhet";
</pre>

E no método execute encontrei:

<pre class="brush: java; title: ; notranslate" title="">if ("getToken".equals(paramString))
{
String str1 = paramJSONArray.getString(0);
localJSONObject.put("token", Hash.generateHash(this.chave, str1));
}
paramCallbackContext.success(localJSONObject);
</pre>

Huhuhu&#8230; já tenho a chave, so preciso descobrir o que raios é **paramJSONArray.getString(0)**.  
Dando mais uma passeada pelo javascript, encontrei em /assets/www/js/plugin/InfoApp.js o seguinte:  
InfoApp.prototype.getToken = function(funcaoRetornoSucesso, funcaoRetornoErro, dados)  
Ou seja, uma redefinição do exec original onde apenas 3 parametros eram necessarios! Procurando um pouco mais, achei em /assets/www/js/sinesp-cidadao.js o seguinte:

<pre class="brush: jscript; title: ; notranslate" title="">window.plugins.infoApp.getToken(
function(retorno){
sucessoGetToken(retorno);
var ws = new WebService(URL_SERVICO);
var parametrosHeader = getParametrosHeader();
var parametrosBody = getParametrosBody();
ws.call(METODO_SERVICO, parametrosHeader, parametrosBody, retornoServico, retornoServicoErro);
},
erroGetToken,
[placa]
);
</pre>

Então, pude saber que paramJSONArray.getString(0) era a própria placa. Ufa.  
Agora fica fácil reescrever a função de HASH em python:

<pre class="brush: python; title: ; notranslate" title="">from hashlib import sha1
from hmac import new as hmac
generateHash = lambda(placa): hmac("sheacsrhet",placa,sha1).digest().encode('hex')
</pre>

Sniffei a saida do app e meu código. O hash bateu ;D  
Porém, tambem tem como parametro IP e localizacao geografica(lat e long). Não sei se o sistema pode restringir a checagem por local/IP, então, porque nao randomizar tambem? ;D  
Latitute e longitude é facil fazer um esquema para randomizar o valor dentro de um raio de cobertura, evitando de por um local inexistente ou, sei lá, no Japão.

<pre class="brush: python; title: ; notranslate" title="">rLat = lambda(raio): '%.7f' % (( raio/111000.0 * math.sqrt(random.random()) ) * math.cos(2 * 3.141592654 * random.random()) + (-3.7506985))

rLong = lambda(raio): '%.7f' % (( raio/111000.0 * math.sqrt(random.random()) ) * math.sin(2 * 3.141592654 * random.random()) + (-38.5290245))
</pre>

Usei a latitude e longitude de Fortaleza/Ceará como referencia.  
O próximo passo é montar tudo:

<pre class="brush: python; title: ; notranslate" title="">#coding: utf-8
import socket
import random, math
from hashlib import sha1
from hmac import new as hmac

generateHash = lambda(placa): hmac("sheacsrhet",placa,sha1).digest().encode('hex')

rLong = lambda(raio): '%.7f' % (( raio/111000.0 * math.sqrt(random.random()) ) * math.sin(2 * 3.141592654 * random.random()) + (-38.5290245))

rLat = lambda(raio): '%.7f' % (( raio/111000.0 * math.sqrt(random.random()) ) * math.cos(2 * 3.141592654 * random.random()) + (-3.7506985))

pacote = lambda(placa): 'POST /sinesp-cidadao/ConsultaPlaca HTTP/1.1\nHost: sinespcidadao.sinesp.gov.br\nContent-Length: %d\nOrigin: file://\nSOAPAction: \nContent-Type: application/x-www-form-urlencoded; charset=UTF-8\nAccept: text/plain, */*; q=0.01\nx-wap-profile: http://wap.samsungmobile.com/uaprof/GT-S7562.xml\nUser-Agent: Mozilla/5.0 (Linux; U; Android 4.1.4; pt-br; GT-S1162L Build/IMM76I) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30\nAccept-Encoding: gzip,deflate\nAccept-Language: pt-BR, en-US\nAccept-Charset: utf-8, iso-8859-1, utf-16, gb2312, gbk, *;q=0.7\n\n%s' % ( len(payload(placa)), payload(placa) )

payload = lambda(placa): '&lt;?xml version="1.0" encoding="utf-8" standalone="yes" ?&gt;&lt;soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" &gt;&lt;soap:Header&gt;&lt;dispositivo&gt;GT-S1312L&lt;/dispositivo&gt;&lt;nomeSO&gt;Android&lt;/nomeSO&gt;&lt;versaoAplicativo&gt;1.1.1&lt;/versaoAplicativo&gt;&lt;versaoSO&gt;4.1.4&lt;/versaoSO&gt;&lt;aplicativo&gt;aplicativo&lt;/aplicativo&gt;&lt;ip&gt;177.206.169.90&lt;/ip&gt;&lt;token&gt;%s&lt;/token&gt;&lt;latitude&gt;%s&lt;/latitude&gt;&lt;longitude&gt;%s&lt;/longitude&gt;&lt;/soap:Header&gt;&lt;soap:Body&gt;&lt;webs:getStatus xmlns:webs="http://soap.ws.placa.service.sinesp.serpro.gov.br/"&gt;&lt;placa&gt;%s&lt;/placa&gt;&lt;/webs:getStatus&gt;&lt;/soap:Body&gt;&lt;/soap:Envelope&gt;\n/sinesp-cidadao/ConsultaPlaca HTTP/1.1\r&lt;br&gt;\r\n' % (generateHash(placa),rLat(20000),rLong(20000), placa)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("sinespcidadao.sinesp.gov.br", 80))
s.send(pacote('XXX0000'))
print s.recv(1024)
s.close()
</pre>

Pronto. Funciona ;D Para efeito de beleza, pode-se usar alguma lib de parsing de XML ou mete um belo e bruto regex da escuridão para parsear tudo com a sutileza de um macaco-ogro do pântano.

**[UPDATE 15/maio/2014]** Conforme foi percebido pelo Lúcio Corrêa( [@luciofcorrea](https://twitter.com/luciofcorrea) ), o sistema mudou e a sinesp tentou obfuscar o resultado. Mas não foi muito difícil gerar novamente o HASH e obter os novos parametros.  
Primeiro, em **/br/gov/sinesp/cidadao/android/f/k.class** foi mantida a chave antiga, para enganar uma busca por strings, porem em **/br/gov/sinesp/cidadao/android/f/j.class** a localSecretKeySpec mudou, ao invés de usar o valor em k.java, ele seta a senha estáticamente:

<pre class="brush: java; title: ; notranslate" title="">SecretKeySpec localSecretKeySpec = new SecretKeySpec("shienshenlhq".getBytes(), "HmacSHA1");</pre>

Desta forma, a nova chave é **&#8220;shienshenlhq&#8221;**.  
Em **/br/gov/sinesp/cidadao/android/f/a.class** temos

<pre class="brush: java; title: ; notranslate" title="">public static final String a = "http://sinespcidadao.sinesp.gov.br/sinesp-cidadao/ConsultaPlacaNovo27032014";</pre>

ou seja, muda a string a se fazer o POST.  
Já em **/br/gov/sinesp/cidadao/android/e/c.class**, encontramos o novo campo a ser incluído: _versaoAplicativo_, com conteudo fixo &#8220;1.1.1&#8221; e o parametro _aplicativo_ agora tem o valor fixo &#8220;aplicativo&#8221;.  
Com tudo isto incluído, o script voltou a funcionar. e está postado no meu github: <https://github.com/paoloo/servicos/blob/master/placa.py>

**[UPDATE 20/NOVEMBRO/2015]** Como da ultima vez, a string de request estava obfuscada, mas foi encontrada pelo grande <span class="user">Junior Kaibro</span>, que a postou no comentario. O novo POST é feito para **/sinesp-cidadao/ConsultaPlacaNovo** e só, nada mais mudou. Atualizei no github. Depois de tanto tempo é legal ver o pessoal mantendo a ferramenta viva. E se colocarem captcha, relaxem, eu quebro ;D