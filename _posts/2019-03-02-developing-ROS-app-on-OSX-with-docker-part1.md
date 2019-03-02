---
title: Developing ROS application on OSX with docker part1
date: 2019-03-02T22:00:43+00:00
author: paolo
layout: post
permalink: /2019/03/02/Developing-ROS-app-on-OSX-with-docker-part1/
categories:
  - en-US
tags:
  - ROS
  - Robotics
  - Docker
  - C++
---


part 1: setting up docker


- get ROS docker image (melodic is the newer)
```
docker pull ros:melodic
```
- create network
```
docker network create ros
docker network ls
```
- run master node
```
master:
docker run --rm -it --name roscore --net ros ros:melodic roscore
```

#1 - TERMINAL / TEXT-ONLY
- run nodes

**node1:**
```
docker run --rm -it --net ros -e ROS_MASTER_URI=http://roscore:11311 ros:melodic rostopic echo /chatter
```
**node2:**
```
docker run --rm -it --net ros -e ROS_MASTER_URI=http://roscore:11311 ros:melodic rostopic pub -1 /chatter std_msgs/String 'Hello From Docker'
```

#2- GRAPHICS / X11 
- install `xquartz`

**XQuartz**
> The XQuartz project is an open-source effort to develop a version of the X.Org X Window System that runs on OS X. To install it, you have two options: you can get the *dmg* (here)[https://www.xquartz.org] or just `brew cask install XQuartz` if you are a cool kid and use brew.

now, run xquartz(close the terminal window if it opens by itself), configure docker and xquartz integration then, finally, run container:
```
$ ip=$(ifconfig|grep 'inet '|grep -v '127.0.0.1'| tail -1|awk '{print $2}')
$ socat TCP-LISTEN:6001,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\" &
$ docker run -it --name turtlesim --net ros -e ROS_MASTER_URI=http://roscore:11311 -e XAUTHORITY=/tmp/xauth -e DISPLAY=$ip:1 ros:melodic bash

# root@e3bf7235a0c0:/# apt-get update
# root@e3bf7235a0c0:/# apt-get install ros-$(rosversion -d)-turtlesim -y
# root@e3bf7235a0c0:/# rosrun turtlesim turtlesim_node
```
to test, run another docker image to send data to turtle:
```
$ docker run --rm -it --name turtleteleopkey --net ros -e ROS_MASTER_URI=http://roscore:11311 ros:melodic bash
# root@e3bf7235a0c0:/# apt-get update
# root@e3bf7235a0c0:/# apt-get install ros-$(rosversion -d)-turtlesim -y
# rosrun turtlesim turtle_teleop_key
```
everything working like a charm!

++++++++++++++++++++++++++++++

**NOTE**: the first time that I tried to use XQuartz, it didn't worked as expected. To fix it I opened it with command+space and, it comes attached to a terminal, where I added `xhost +`, which let's *anyone* attach to your X(so, be careful).

End of part 1. Next: ROS tests and CI

