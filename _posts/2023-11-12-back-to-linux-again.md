---
title: Back to Linux (again)
date: 2023-11-12T22:00:43+00:00
author: paolo
layout: post
permalink: /2023/11/12/back-to-linux-again/
categories:
  - en-US
tags:
  - linux
  - random
  - comp
---

After a few years and a lot of hardcore experimentations with OSX, it was inevitable to go back to my roots. So, I finally bought a good mini pc(lenovo thinkcentre M920) and installed ubuntu!

I was expecting a good and easy installing/configuration process, but it was far from great! I feel like installing ubuntu for "normal" machines is easier than install a few tools on OSX.

Anyway, my configuration for ubuntu right now is pretty simple but it's already making my life so good! First of all I nstalled miniconda
```
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
conda config --set changeps1 false
conda config --set auto_activate_base false
```

Then, I installed git and my main editor and IDE: neovim
```
sudo apt install git nvim
```

And to configure it, I cloned my repo(`git clone git@github.com:paoloo/dotfiles.git`) and I did copy everything from `nvim` directory to `~/.config/nvim`, then
I opened `nvim` and installed the plugins with: `:PlugInstall` (on the first run, just ignoring the errors as it downloads and configures it async)
and that's it! I have my beautiful IDE ready to code... BUT I was trying the copilot from github and well, it supports neovim, and to install it, I just did:
```
mkdir -p ~/.config/nvim/pack/github/start/
git clone https://github.com/github/copilot.vim \
   ~/.config/nvim/pack/github/start/copilot.vim
```
Then, I opened nvim and typed `:Copilot setup` and that's it!!! too simple!

Well, the experience with ubuntu was already too good but I remember something that I love a lot on OSX: preview everything with space bar. Turns out that ubuntu can have such a feature as well!
And for that, I did install gnome-sushi: `sudo apt install gnome-sushi`

Now my new journey with ubuntu just began!
