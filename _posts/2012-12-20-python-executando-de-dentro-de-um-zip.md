---
title: python executando de dentro de um zip
date: 2012-12-20T01:13:36+00:00
author: paolo
layout: post
permalink: /2012/12/20/python-executando-de-dentro-de-um-zip/
categories:
  - pt-BR
tags:
  - python
---
Felicidade descobrir que python executava dentro de arquivo zip, como um tar no java. Ficou mais fácil fazer deploy de aplicações! O único ponto a considerar é que deve haver um arquivo \_\_main\_\_.py na raiz do zip que carrega o resto do projeto.  
teste:

<pre class="brush: bash; title: ; notranslate" title="">echo "print 'YEY'" &gt; __main__.py && zip -9 teste.zip __main__.py && python test.zip
</pre>

E para deixar o teste.zip executavel diretamente

<pre class="brush: bash; title: ; notranslate" title="">(echo '#!/usr/bin/env python'; cat teste.zip) &gt; teste && chmod +x test && ./teste
</pre>

YEY