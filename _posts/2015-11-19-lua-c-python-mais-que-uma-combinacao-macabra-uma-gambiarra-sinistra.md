---
title: 'Lua + C + Python - Mais que uma combinação macabra, uma gambiarra sinistra'
date: 2015-11-19T11:30:14+00:00
author: paolo
layout: post
permalink: /2015/11/19/lua-c-python-mais-que-uma-combinacao-macabra-uma-gambiarra-sinistra/
geo_public:
  - "0"
categories:
  - pt-BR
tags:
  - comp
  - hacks
  - LUA
  - python
  - uC
---
Antes de mais nada: Por que?
Eu precisava fazer deploy de uma shared library em um ARM com linux(um raspberry Pi) extremamente capado, e não podia instalar todas as tools de dev, pois estava no limite de espaço do cartão, devido a aplicação dele. Mas precisava desta shared lib para carregar no python, via ctypes, pois o mesmo usaria as informações extraidas do hardware pelo .c, interpretaria e daria ordens ao resto da eletrônica. Acontece que os parametros do C variavam muito, precisavam ser tunados constantemente. Foi daí que rolou a ideia do LUA.
A ideia foi boa? Bom, funcionou. E até que faz um pouco de sentido, de alguma forma haha

vamos la, o loader, em python, é simplezão:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; loader.py &lt;&lt; _EOF_
import ctypes
biblioteca=ctypes.CDLL('./zoalib.so')
biblioteca.zoeira.restype = ctypes.c_int
biblioteca.zoeira.argtypes = [ctypes.c_int]
biblioteca.zoeira(5)
_EOF_
</pre>

O loader em C:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt;zoalib.c &lt;&lt; _EOF_
#include "lua.h"
#include "lauxlib.h"

int zoeira(int a)
{
    double z;
    lua_State *L = lua_open();
    luaL_openlibs(L);
    luaL_loadfile(L, "zoeira.lua");	/* arquivo lua */
    lua_pcall(L, 0, 0, 0);		/* limpa a pilha */
    lua_getglobal(L, "modelamotor");	/* nome da função do lua */
    lua_pushnumber(L, 3);		/* envia primeiro argumento */
    lua_pushnumber(L, 4);		/* envia segundo argumento */
    lua_pcall(L, 2, 1, 0);
    z = lua_tonumber(L, -1);		/* pega resultados */
    printf("Resultado: %f\n",z);
    lua_pop(L, 1);
    lua_close(L);
    return (a+1);
}
_EOF_
</pre>

E o script em lua:

<pre class="brush: plain; title: ; notranslate" title="">$ cat &gt; zoeira.lua &lt;&lt; _EOF_
function modelamotor (param1, param2)
    return math.sqrt(param1^2 + param^2)
end
_EOF_
</pre>

Agora, vamos compilar com estes poucos parametros e rodar haha:

<pre class="brush: plain; title: ; notranslate" title="">$ gcc -I/usr/include/lua5.1 zoalib.c -llua5.1 -lm -fPIC -shared -Wl,-soname,zoalib -o zoalib.so
$ python l.py
Resultado: 5.000000
6
</pre>

Hell yeah!
Embora isso seja absurdamente mais util nos raspberryPi/beaglebone, talvez haja algum uso no desktop, vai saber haha.
