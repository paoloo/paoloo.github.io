---
title: Arvore de diretório da Caixa Economica Federal
date: 2010-11-10T16:01:44+00:00
author: paolo
layout: post
permalink: /2010/11/10/arvore-de-diretorio-da-caixa-economica-federal/
categories:
  - pt-BR
tags:
  - hacks
  - not-really-useful
---
Uma falha nas configuracoes no webserver da Caixa Economica Federal permitiu acessar a arvore de diretorios de todo o server por alguns dias. Até o google fez um [cache](http://webcache.googleusercontent.com/search?q=cache:MnY7HKZOUPQJ:www.caixa.gov.br/evid_NT050_Inst_web_216208.txt+site:caixa.gov.br+filetype:txt&cd=1&hl=pt-BR&ct=clnk&gl=br "google cache do arquivo da CEF"). O arquivo, que foi gerado durante a atualização de algum componente do webserver( Microsoft-IIS/6.0, tinha que ser! **LoL** ), estava world readable e foi indexado pelo google( tinha que ser! **LoL [2]** ).  
Embora isso não seja uma falha grave, é interessante ver o &#8220;_nível&#8221;_ dos admins de um web banking haha&#8230; ( Depois o pessoal fica reclamando quando existe ataque ).  
O arquivo original, http://www.caixa.gov.br/evid\_NT050\_Inst\_web\_216208.txt não se encontra mais no ar, obviamente. O encontrei através de uma singela [busca](http://www.google.com.br/search?q=site:caixa.gov.br+filetype:txt) e vou disponibilizar [aqui]({{ site.baseurl }}/uploads/2010/11/cef_estrutura.doc)( O arquivo diz .doc mas é um .txt, apenas que o wordpress nao deixa upar texto puro. ).

Au revoir.
