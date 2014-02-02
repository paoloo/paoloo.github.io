---
title: Escrevendo aplicaçoes para o RISC OS
date: 2014-02-02T04:06:13+00:00
author: paolo
layout: post
permalink: /2014/02/02/escrevendo-aplicacoes-para-o-risc-os/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - comp
  - OS
  - retrocomputing
  - RISC OS
---
Antes de mais nada, sistemas da década de 80 e 90 tinham algo em comum: **BASIC!** Não consegui achar referencia alguma a sistema antigo que não fosse baseado ou tivesse como parte mais importante o interpretador BASIC. E como é de se esperar, este evoluiu muito para se adequar as necessidades, de forma que BASIC era o padrão de desenvolvimento de qualse tudo. O RISC OS não era excessão. Herdou o BBC BASIC dos BBC Micros, fabricados pela Acorn para o governo britanico usar nas salas de aula, que é uma excelente implementação do padrão BASIC porem tem varias particularidades, irrelevantes no momento.  
Vamos começar com o básico(hehehe!). Escrever uma aplicação em BASIC é trivial, como se espera. Nada mais que texto interpretado? Correto, porem o **!Edit** precisa ser avisado que se trata de um fonte em BASIC e não texto puro, para ele &#8220;facilitar&#8221; para o parser tokenizando tudo e setando o fieletype correto(ffb). Isso é feito simplesmente clicando com o botão do meio no icone do **!Edit** na barra e selecionando o tipo para BASIC.

[<img class="alignnone size-full wp-image-367" src="{{ site.baseurl }}/uploads/2014/03/criabasic.png" alt="criaBasic" width="138" height="155" />]({{ site.baseurl }}/uploads/2014/03/criabasic.png)  
Depois é só questão de digitar o cógico e salvar. Vamos começar com o clássico Hello World:

10 PRINT "oi mundo"  
20 GOTO 10

Salva com F3 ou clicando no botão do meio > Save. Para executar é só dar um duplo click sobre o arquivo salvo. [<img class="alignnone size-medium wp-image-368" src="{{ site.baseurl }}/uploads/2014/03/rodando.png?w=300" alt="rodando" width="300" height="202" srcset="{{ site.baseurl }}/uploads/2014/03/rodando.png 491w, {{ site.baseurl }}/uploads/2014/03/rodando-300x202.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/rodando.png)  
OK. tudo muito bonito, um loop infinito de hello worlds, agora tente clicar em qualquer outra coisa ;D O sistema parou de responder não é? Isso é culpa do programador, mais especificamente, da Multitarefa Cooperativa, onde o programador define quando liberar tempo de execução para o resto do sistema. Mas criei um loop infinito que nunca libera nada de recurso pro resto do SO. Solução? Simples:

DIM b% 255  
SYS "Wimp_Initialise",200,&4B534154,"OiMundo"  
REPEAT  
SYS "Wimp_Poll",,b%  
PRINT "oi mundo"  
UNTIL FALSE

Uma explicação simples:  
SYS &#8220;Wimp_Initialise&#8221;,300,&4B534154,&#8221;OiMundo&#8221;  
**SYS** é um tipo de SYSCALL do RISC OS. Neste caso, temos 4 parametros:  
O primeiro diz ao SO para inicializa uma aplicacao;  
O segundo diz que a aplicação roda a partr do RISC OS 3 (versão minima * 100)  
O terceiro diz que a aplicação foi concebida para RISC OS e não a versão antiga, Arthur. Este parametro é o ASCII de TASK em little endian.  
O quarto parametro é o nome da aplicação, no caso, OiMundo.

Depois disto temos um loop simples e mais uma syscall que chama a funcão &#8220;Wimp_poll&#8221;, que retorna o controle do processamento para o SO. Eventualmente o SO devolve o controle a sua aplicação e ela executa o que deveria, em um ciclo infinito. Um detalhe aqui, a variavel que foi definida no inicio da aplicação, b% é um bloco de memoria pre-alocada para nossa aplicacao. Passamos o endereço dela na syscall para garantir que esta area é nossa e outra aplicação não tome.

Depois de executar, vemos que as coisas rodam como deveriam haha. Muito bem, uma aplicação multitask em BASIC&#8230; Mas isso ainda não é o padrao de aplicacao RISC OS. O próximo passo é criar uma aplicação completa, no padrão de deploy.  
O primeiro passo é criar um diretório com o nome iniciado por !, no meu caso, criei !oiMundo na raiz do volume HostFS (HostFS:$).[<img class="alignnone size-medium wp-image-369" src="{{ site.baseurl }}/uploads/2014/03/criarpasta.png?w=300" alt="criarpasta" width="300" height="93" srcset="{{ site.baseurl }}/uploads/2014/03/criarpasta.png 309w, {{ site.baseurl }}/uploads/2014/03/criarpasta-300x93.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/criarpasta.png)  
depois vamos entrar neste diretório(tem de segurar o shift ao clicar, para ele não tentar executar). Extamos em HostFS:$.!oiMundo  
Proximo passo é criar um arquivo OBEY para controlar a execução. Um OBEY é como um shell script ou um .BAT, é um arquivo de lote com comandos de sistema. É a primeira coisa que deve ser executada para que parametros de sistema ou o path seja setado. O processo é identico a criar um script basic:  
[<img class="alignnone size-full wp-image-370" src="{{ site.baseurl }}/uploads/2014/03/criaobey.png" alt="criaObey" width="142" height="155" />]({{ site.baseurl }}/uploads/2014/03/criaobey.png)  
o conteúdo dele:

Set oiMundo$Dir <Obey$Dir>  
IconSprites <oiMundo$Dir>.!Sprites  
WimpSlot -min 32k -max 32k  
Run <oiMundo$Dir>.!RunImage

Depois, só salvar como HostFS:$:!oiMundo.!Run  
[<img class="alignnone size-medium wp-image-371" src="{{ site.baseurl }}/uploads/2014/03/salvandorun.png?w=300" alt="salvandoRun" width="300" height="185" srcset="{{ site.baseurl }}/uploads/2014/03/salvandorun.png 439w, {{ site.baseurl }}/uploads/2014/03/salvandorun-300x186.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/salvandorun.png)  
Agora vamos criar um ícone para nossa aplicação ;D  
Coisa simples, abra o !Paint, crie uma imagem de 34&#215;17 pixels e desenhe o que quiser. Salve-a como HostFS:$.!oiMundo.!Sprites  
[<img class="alignnone size-medium wp-image-372" src="{{ site.baseurl }}/uploads/2014/03/criasprites.png?w=300" alt="criaSprites" width="300" height="109" srcset="{{ site.baseurl }}/uploads/2014/03/criasprites.png 633w, {{ site.baseurl }}/uploads/2014/03/criasprites-300x109.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/criasprites.png)  
Agora, tentar executar !oiMundo(que ja deve estar com icone) vai gerar o seguinte:  
[<img class="alignnone size-medium wp-image-373" src="{{ site.baseurl }}/uploads/2014/03/tentandoexecutar.png?w=300" alt="tentandoExecutar" width="300" height="267" srcset="{{ site.baseurl }}/uploads/2014/03/tentandoexecutar.png 383w, {{ site.baseurl }}/uploads/2014/03/tentandoexecutar-300x268.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/tentandoexecutar.png)  
A razão é que falta o principal, nossa aplicação definida no arquivo OBEY e que deve se chamar !RunImage. Vamos usar nosso código anterior, e renomeá-lo para HostFS:$.!oiMundo.!RunImage.  
voi lá:

[<img class="alignnone size-medium wp-image-368" src="{{ site.baseurl }}/uploads/2014/03/rodando.png?w=300" alt="rodando" width="300" height="202" srcset="{{ site.baseurl }}/uploads/2014/03/rodando.png 491w, {{ site.baseurl }}/uploads/2014/03/rodando-300x202.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/rodando.png)  
Depois, todos os arquivos continuam editáveis, so voltar lá e mudar o icone ridiculo por um melhorzinho. [<img class="alignnone size-medium wp-image-374" src="{{ site.baseurl }}/uploads/2014/03/melhorando.png?w=300" alt="melhorando" width="300" height="230" srcset="{{ site.baseurl }}/uploads/2014/03/melhorando.png 430w, {{ site.baseurl }}/uploads/2014/03/melhorando-300x230.png 300w" sizes="(max-width: 300px) 100vw, 300px" />]({{ site.baseurl }}/uploads/2014/03/melhorando.png)  
E assim, temos a primeira aplicação real multithread em BASIC no RISC OS haha.  
Tem manuais do BBC Basic em <http://www.bbcbasic.co.uk/bbcbasic/manual/>, <http://acorn.chriswhy.co.uk/docs/Acorn/OEM/AcornOEM_BBCBASICRM.pdf> e em vários locais facilmente encontrados via busca. E é so estudar um pouco que dá para fazer muita coisa.
