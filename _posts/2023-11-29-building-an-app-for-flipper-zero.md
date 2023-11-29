---
title: Building an APP for Flipper Zero
date: 2023-11-29T22:00:43+00:00
author: paolo
layout: post
permalink: /2023/11/29/building-an-app-for-flipper-zero/
categories:
  - en-US
tags:
  - flipper
  - RF
---

I gonna use python and <a href="https://github.com/flipperdevices/flipperzero-ufbt">uFBT</a> ("micro Flipper Build Tool"), a cross-platform tool for building applications for Flipper Zero. It is a simplified version of <a href="https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md">fbt (Flipper Build Tool)</a>.

I did install it with `python3 -m pip install --upgrade ufbt` and run `ufbt` for the first time to download the flipper firmware as well as all dependencies. If you want to work with specific versions of the firmware, change the `channel`(think of this as a branch, which can be "dev", "rc" or "release") using something like `ufbt update --channel=dev`.


Now, to create a project, create a directory, cd into it and run: `ufbt create APPID=nasty_app`.
```
paolo@phobos ~/Workspace/Flipper/nastyapp $ ufbt create APPID=nasty_app
scons: Entering directory `/home/paolo/.ufbt/current/scripts/ufbt'

fbt: warning: App folder '/home/paolo/Workspace/Flipper/nastyapp': missing manifest (application.fam)
LoadAppManifest, line 131, in file "/home/paolo/.ufbt/current/scripts/fbt_tools/fbt_apps.py"
Creating '/home/paolo/Workspace/Flipper/nastyapp/nasty_app.c'
	INSTALL	/home/paolo/Workspace/Flipper/nastyapp/nasty_app.png
Creating '/home/paolo/Workspace/Flipper/nastyapp/application.fam'
Mkdir("/home/paolo/Workspace/Flipper/nastyapp/images")
Touch("/home/paolo/Workspace/Flipper/nastyapp/images/.gitkeep")
Copy("/home/paolo/Workspace/Flipper/nastyapp/.github", "project_template/app_template/.github")
```
it generates all required files.
```
paolo@phobos ~/Workspace/Flipper/nastyapp $ ls
application.fam  images  nasty_app.c  nasty_app.png
```
Running `ufbt` agin will build it
```
paolo@phobos ~/Workspace/Flipper/nastyapp  flipper $ ufbt
scons: Entering directory `/home/paolo/.ufbt/current/scripts/ufbt'
	ICONS	/home/paolo/.ufbt/build/nasty_app/nasty_app_icons.c
	CDB	/home/paolo/Workspace/Flipper/nastyapp/.vscode/compile_commands.json
	CC	/home/paolo/Workspace/Flipper/nastyapp/nasty_app.c
	CC	/home/paolo/.ufbt/build/nasty_app/nasty_app_icons.c
	LINK	/home/paolo/.ufbt/build/nasty_app_d.elf
	APPMETA	/home/paolo/.ufbt/build/nasty_app.fap
	INSTALL	/home/paolo/Workspace/Flipper/nastyapp/dist/debug/nasty_app_d.elf
	FAP	/home/paolo/.ufbt/build/nasty_app.fap
	FASTFAP	/home/paolo/.ufbt/build/nasty_app.fap
	INSTALL	/home/paolo/Workspace/Flipper/nastyapp/dist/nasty_app.fap
	APPCHK	/home/paolo/.ufbt/build/nasty_app.fap
		Target: 7, API: 46.0
```
and it will generate a new set of files
```
paolo@phobos ~/Workspace/Flipper/nastyapp $ ls
application.fam  dist  images  nasty_app.c  nasty_app.png
paolo@phobos ~/Workspace/Flipper/nastyapp $ tree dist
dist
├── debug
│   └── nasty_app_d.elf
└── nasty_app.fap

1 directory, 2 files
```

`nasty_app.fap` is the flipper binary:
```
paolo@phobos ~/Workspace/Flipper/nastyapp  flipper $ file dist/nasty_app.fap
dist/nasty_app.fap: ELF 32-bit LSB relocatable, ARM, EABI5 version 1 (SYSV), not stripped
```

You can upload and start the app on a Flipper attached over USB using `ufbt launch` OR just copy the fap using qFlipper.

To update the current version of the firmware(on my case, I had 0.95.1 and I need to update to 0.96.1) just do:
```
paolo@phobos ~/Workspace/Flipper/nastyapp  flipper $ ufbt update
18:48:55.669 [I] Deploying SDK for f7
18:48:55.669 [I] Fetching version info for UpdateChannel.RELEASE from https://update.flipperzero.one/firmware/directory.json
18:48:56.168 [I] Using version: 0.96.1
18:48:56.169 [I] uFBT SDK dir: /home/paolo/.ufbt/current
18:48:56.501 [I] Deploying SDK
18:48:56.778 [I] SDK deployed.
```

too simple
