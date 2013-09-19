---
title: criar uma search engine
date: 2013-09-19T08:40:44+00:00
author: paolo
layout: post
permalink: /2013/09/19/criar-uma-search-engine/
categories:
  - pt-BR
tags:
  - comp
  - random
---
Precisei criar um mecanismo de busca para uma intranet e lembrei do final da década de 90 e os infinitos mecanismos de busca que apareciam e sumiam todo mês haha. Sistemas de buscas que pareciam definitivos como **altavista.digital.com** ou **webcrawler.com**, foram dando espaço para o **Yahoo!** e o hoje hegemônico **Google**. Lembro que tudo era feito com CGI(Common Gateway Interface) usando PERL&#8230; <del><em>Sou preconceituoso contra PERL então sou suspeito para falar(hahahahaha)</em></del> mas era engraçado, mil a uma linhas de código para adicionar e indexar paginas, fora a busca em sí. Hoje, com PHP, nao precisei nem de 60 linhas de código para fazer o mesmo(<del>vai ver a culpa é do PERL hahahaha</del>).  
E é bem fácil, primeiro, precisamos de um banquinho de dados para facilitar a vida. Estou usando o MySQL porque ele está em todo lugar, mas voce pode usar até sqlite se quiser(e cheirar cola). Vou chamar minha base de dados de &#8220;busca&#8221;. Eu seu, sou criativo demais ;D

<pre class="brush: sql; title: ; notranslate" title="">CREATE DATABASE `busca`
USE `busca`;
CREATE TABLE `searchengine` (
`id` INT NOT NULL AUTO_INCREMENT,
`url` VARCHAR( 255 ) NOT NULL ,
`conteudo` TEXT NOT NULL ,
PRIMARY KEY ( `id` )
) ENGINE = MYISAM
</pre>

Bom, o objetivo não é ser tão eficiente quanto o googe, entao apenas salvo a url e o conteudo da pagina inicial para buscas posteriores, nada muito elaborado como contagem de palavras, etc.  
Primeiro vamos criar um arquivo com as definiçoes de conexão com o banco e chamá-lo de banco.php:

<pre class="brush: php; title: ; notranslate" title="">&lt;?php
mysql_connect("localhost", "usuario", "senha");
mysql_select_db("busca");
?&gt;
</pre>

Simples assim. Agora vamos criar a interface de adiçao de sites e chamá-lo de addurl.php:

<pre class="brush: php; title: ; notranslate" title="">&lt;html&gt;&lt;head&gt;&lt;title&gt;prototipo - busca&lt;/title&gt;&lt;/head&gt;&lt;body&gt;
&lt;form action="#" method="POST"&gt;
URL: &lt;input type="text" name="url" size="50"&gt;&lt;input type="submit" value="Add URL"&gt;
&lt;/form&gt;
&lt;?php
if(isset($_POST['url'])){
include('banco.php');
$url=$_POST['url'];
if( substr($url,0,7) != "http://" ){ $url = "http://" . $url; }
$pagedata = file_get_contents($url);
$search = array(
'@&lt;script[^&gt;]*?&gt;.*?&lt;/script&gt;@si',
'@&lt;style[^&gt;]*?&gt;.*?&lt;/style&gt;@si',
'@&lt;[\/\!]*?[^&lt;&gt;]*?&gt;@si',
'@&lt;![\s\S]*?--[ \t\n\r]*&gt;@'
);
$pagedata = preg_replace($search, '',$pagedata);
$pagedata = str_replace("'","",$pagedata);
mysql_query("INSERT INTO searchengine VALUES ('','$url','$pagedata')");
echo "URL Adicionada.&lt;br&gt;&lt;a href='./addurl.php'&gt;Inicio...&lt;/a&gt;";
}
?&gt;
&lt;/body&gt;&lt;/html&gt;
</pre>

como se pode ver, nao tem nada demais, apenas faz alguns ajustes na pagina, e o array $search contem os campos para cortar as tags html, scripts e css, para deixar o conteudo mais texto puro possivel. Obviamente o mesmo arquivo provê a lógica php para adicionar e o HTML de apoio. O ultimo passo é a interface de busca em sí. Vamos chama-la de index.php:

<pre class="brush: php; title: ; notranslate" title="">&lt;html&gt;&lt;head&gt;&lt;title&gt;prototipo - busca&lt;/title&gt;&lt;/head&gt;&lt;body&gt;
&lt;center&gt;
&lt;form action="#" method="GET"&gt;
&lt;b&gt;&lt;/b&gt;&lt;input type="text" name="q" size="50"&gt;&lt;input type="submit" value="Search"&gt;
&lt;/center&gt;
&lt;/form&gt;
&lt;?php
if(isset($_GET['q'])){
include('banco.php');
$sql = mysql_query("SELECT * FROM searchengine WHERE url LIKE '%$_GET[q]%' OR conteudo LIKE '%$_GET[q]%' LIMIT 0,20");
while($ser = mysql_fetch_array($sql)) {
echo "&lt;h2&gt;&lt;a href='$ser[pageurl]'&gt;$ser[pageurl]&lt;/a&gt;&lt;/h2&gt;";
}
echo '&lt;a href="index.php"&gt;Voltar&lt;/a&gt;';
}
?&gt;
&lt;/body&gt;&lt;/html&gt;
</pre>

É só isso? É sim haha. simples assim. Deste jeito está funcionando na intranet que escrevi.

Quando uma busca é feita, ele procura o texto na URL e no conteúdo da página inicial(por isto a necessidade de limpar os elementos html/script/css do documento). Não existe um rank, nem algoritmo inteligente de resposta, mas isso é facilmente implementável. Outra coisa é que isso mostrará apenas os primeiros 20 resultados devido a query sql &#8220;LIMIT 0,20&#8221;, porem é trivial fazr um count nos resultados e fazer um paginador, substituindo o **0,20** por qualquer resultado inicial e final.

Não dá para competir com o google ainda, mas é legal implementar em uma intranet e fazer um pré-parsing na query antes de chamar a pesquisa, para executar automaticamente algumas funçoes de conversão, e até de consulta de dados internos. Eu fiz isso antes do &#8220;include(&#8216;banco.php&#8217;);&#8221;, se voce digitar &#8220;+funcionarios&#8221;, ele consulta a tabela de ponto e diz quantos estão trabalhando, ou &#8220;+agenda data&#8221;, mostra os compromissos globais para a data definida ou para o dia atual, caso nenhuma data seja definida. Defini todos os comandos para iniciar com &#8220;+&#8221; apenas para não pesar o parser, mas nada impede de usar um texto normal e passar por um parser mais sofisticado .

Fica a ideia.