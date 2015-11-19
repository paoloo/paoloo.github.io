---
title: 'Lua + C - uma combinação perfeita'
date: 2015-11-19T11:28:42+00:00
author: paolo
layout: post
permalink: /2015/11/19/lua-c-uma-combinacao-perfeita-2/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - comp
  - hacks
  - LUA
---
Lua é uma linguagem de script imperativa, procedural, pequena(sério, muito pequena), reflexiva e leve, projetada para expandir aplicações em geral, com o objetivo de agilizar a prototipagem e ser embarcada em softwares complexos.

Embarcar lua em C/C++ por ter sido o pensamento original da linguagem, é algo muito fácil e incrivelmente util.

antes vamos instalar a biblioteca de desenvolvimento do lua no ubuntu:

<pre class="brush: plain; title: ; notranslate" title=""># apt-get install liblua5.1-0-dev
</pre>

Agara vamos fazer algo simples: uma função em C que executa instruções em lua

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; 1.c &lt;&lt; _EOF_
#include "lua.h"
#include "lauxlib.h"
int main(int argc, char **argv)
{
    lua_State *L = luaL_newstate();
    luaL_openlibs(L);
    luaL_dostring(L, "print('Hey hey hey, '.._VERSION)");
    return 0;
}
_EOF_
</pre>

compilar, lembrando de linkar a biblioteca do lua e adicionar ao include:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -I/usr/include/lua5.1 -o 1 1.c -llua5.1 -lm
$ ./1
Hey hey hey, Lua 5.1
</pre>

Ok, funcionou. Fazer o C carregar um arquivo contendo o script em lua é igualmente trivial, muda apenas a instrução luaL\_dostring() por luaL\_dofile(), visto a seguir:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; 2.c &lt;&lt; _EOF_
#include "lua.h"
#include "lauxlib.h"
int main(int argc, char **argv)
{
    lua_State *L = luaL_newstate();
    luaL_openlibs(L);
    luaL_dofile(L, "dois.lua");
    return 0;
}
_EOF_
</pre>

E criar o script &#8220;dois.lua&#8221; que será carregado. Neste caso, não estou gerenciando erros, mas é um código em C, todos os erros devem ser checados ou vai crashar tudo.

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; dois.lua &lt;&lt; _EOF_
print "go go go"
for i=1,5 do
   print(i) 
end
print "hell yeah!"
_EOF_
</pre>

compilar igualmente e rodar:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -I/usr/include/lua5.1 -o 2 2.c -llua5.1 -lm
$ ./2
go go go
1
2
3
4
5
hell yeah!
</pre>

Lembrando que o script pode ser mudado depois da compilação, esta é a ideia, na verdade haha.

Até aqui, tudo bem. Agora vamos fazer o lua acessar uma função do C:

<pre class="brush: plain; title: ; notranslate" title="">$ car &gt; 3.c &lt;&lt; _EOF_
#include "lua.h"
#include "lauxlib.h"
static int huehue(lua_State *L){ /* método que será chamado dentro do script */
  int n = lua_gettop(L); /* numero de argumentos */
  double sum = 0;
  int i;
  for (i = 1; i &lt;= n; i++){
    sum += lua_tonumber(L, i);
  }
  lua_pushnumber(L, sum / n); /* envia primeira resposta */
  lua_pushnumber(L, sum);     /* envia segunda resposta */
  lua_pushnumber(L, 666);     /* envia terceira resposta */
  return 3;                   /* quantidade de respostas */
}
int main(int argc, char **argv)
{
    lua_State *L = luaL_newstate();
    luaL_openlibs(L);
    lua_register(L, "huehue", huehue);
    luaL_dofile(L, "tres.lua");
    return 0;
}
_EOF_
</pre>

e o arquivo lua:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; tres.lua &lt;&lt; __EOF__
print("arquivo lua\n")
_r, _s, _t = huehue(1,2,3,5,8,9)
print(_r.." - ".._s.." - ".._t)
__EOF__
</pre>

A compilação continua a mesma:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -I/usr/include/lua5.1 -o 3 3.c -llua5.1 -lm
$ ./3
arquivo lua

4.6666666666667 - 28 - 666
</pre>

Beleza, so lebrar de registrar a função que se quer exportar para o script lua e tudo funciona muito bem.
Agora a ultima fronteira, fazer o C carregar uma função do lua. Para que isso? bom, vamos dizer que está extraindo dados do hardware de alguma forma em C, mas lidar com isso é complexo ou exige várias mudanças. Re-escrever e re-compilar não é exatamente a saída mais agradavel. Lua pode ser a resposta.
O exemplo que estou colocando, é, entretanto, mais simples. O C para dois parametros para uma função continha, que na prática executa o teorema de pitagoras, mas pode ser mudado para qualquer coisa sem requerer recompilação

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; 4.c &lt;&lt; _EOF_
#include "lua.h"
#include "lualib.h"
#include "lauxlib.h"
int main()
{
    double z;
    lua_State *L = lua_open();
    luaL_openlibs(L);
    luaL_loadfile(L, "quatro.lua");	/* arquivo lua */
    lua_pcall(L, 0, 0, 0);		/* limpa a pilha */
    lua_getglobal(L, "continha");	/* nome da função do lua */
    lua_pushnumber(L, 3);		/* envia primeiro argumento */
    lua_pushnumber(L, 4);		/* envia segundo argumento */
    lua_pcall(L, 2, 1, 0);
    z = lua_tonumber(L, -1);		/* pega resultados */
    printf("Resultado: %f\n",z);
    lua_pop(L, 1);
    lua_close(L);
    return 0;
}
_EOF_
</pre>

e o arquivo lua:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; quatro.lua &lt;&lt; _EOF_
function continha (x, y)
    return math.sqrt(x^2 + y^2)
end
_EOF_
</pre>

Como sempre, a compilação é a mesma:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -I/usr/include/lua5.1 -o 4 4.c -llua5.1 -lm
$ ./4
Resultado: 5.000000
</pre>

Lindo!
Como podemos ver, embarcar lua em c não só faz sentido, como pode facilitar muito a extensão de um software mais complexos. E é por isto que é tão udada em jogos e em aplicações mobile(compiladas com c++).
Usem lua, é uma coisa linda!
haha
