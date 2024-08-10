---
title: Video Download
date: 2024-08-10T22:00:43+00:00
author: paolo
layout: post
permalink: /2024/08/10/video-download/
categories:
  - en-US
tags:
  - comp
  - hacks
  - bash
---

I will use this post to store a few ways of downloading video data from different places. This is useful to avoid searching for the commands all the time.

## To copy lives from youtube:

```bash
yt-dlp --list-formats https://www.youtube.com/watch?v=<VIDEO-CODE>
yt-dlp -f 95 -g https://www.youtube.com/watch?v=<VIDEO-CODE>
ffmpeg -i <CONTENT FROM THE PREVIOUS COMMAND> -c copy output.ts
```

## To convert m3u8 to mp4:

- Download the m3u8 and run:

```bash

ffmpeg -protocol_whitelist "file,http,https,tcp,tls,crypto" \
  -i index-v1-a1.m3u8 \
  -map 0:v:0 -map 0:a:0 \
  -c copy -bsf:a aac_adtstoasc -movflags +faststart \
  output.mp4

```

