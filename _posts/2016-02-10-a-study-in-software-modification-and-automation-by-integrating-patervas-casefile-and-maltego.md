---
title: "A study in software modification and automation by integrating Paterva's CaseFile and Maltego"
date: 2016-02-10T01:48:21+00:00
author: paolo
layout: post
permalink: /2016/02/10/a-study-in-software-modification-and-automation-by-integrating-patervas-casefile-and-maltego/
geo_public:
  - "0"
categories:
  - en-US
tags:
  - hacks
  - python
---
**Maltego** is an excellent intelligence and data visualization tool, but the need of being online(and the requirement of an registered account) make it pretty much useless for more sophisticated usages(like crime investigation or any other private and offline usage). For this, **CaseFile** was created, which is, basically, Maltego offline without the transforms. But transforms(offline and over closed-source data) would make the life of analysts easier in checking/validating information. To have the best of two worlds, I&#8217;ve extracted the transform engine from Maltego and inserted on CaseFile, also, removing the need of login and information leakage that the tool usually allow, making trustable and usable even by the government.

_<font color="#ff0000">First, Maltego is a great tool and everyone who likes it should support Paterva and buy licenses. This is a study in software modification, automation and should not be used to cause harm to Paterva&#8217;s copyrights/busines model by any means. That&#8217;s why I&#8217;m using old versions of Maltego and Casefile.</font>_

The versions used was:

  * Maltego **3.1**: maltego-3.1.1_CE-2012-04-11.zip md5 400b427652ca3e8ed60a6d6b7a457e81
  * CaseFile **1.0**: maltego-CF.1.0.1_community-2012-03-14.zip md5 8d009eae5c899d74458712fe0e1458e1

They were originally downloaded from:

  * http://www.paterva.com/malv31/community/maltego-3.1.1_CE-2012-04-11.zip
  * http://www.paterva.com/cf10/community/maltego-CF.1.0.1_community-2012-03-14.zip

The base tools used was:

  * **Jasmin** ( <http://jasmin.sourceforge.net/> ), an assembler for the Java Virtual Machine. It takes ASCII descriptions of Java classes, written in a simple assembler-like syntax using the Java Virtual Machine instruction set. It converts them into binary Java class files, suitable for loading by a Java runtime system.
  * **ClassFileAnalyzer** ( <http://classfileanalyzer.javaseiten.de/> ), an analyzer and disassembler (Jasmin syntax 2) for Java class files.

First, I removed the annoying background image at **maltego/modules/locale/com-paterva-maltego-ui-graph_maltego.jar**.

Then, I&#8217;ve copied some files related to transform from Maltego to CaseFile:

<pre class="brush: plain; title: ; notranslate" title="">from maltego-ui/
    com-paterva-maltego-transforms-standard
    com-paterva-maltego-transform-protocol-v2
    com-paterva-maltego-transform-manager
    com-paterva-maltego-transform-finder     # needed by com-paterva-maltego-transform-manager
    com-paterva-maltego-transform-discovery  # needed by com-paterva-maltego-transform-protocol-v2
    com-paterva-maltego-transform-runner     # needed by com-paterva-maltego-transform-protocol-v2
  from maltego-core-platform/
    com-paterva-maltego-typing               # for com.paterva.maltego.typing.TypeNameValidator
</pre>

The next step was define a series of modifications and fine tunning on CaseFile:

  * remove savetoserver and fake transform
  * remove startpage website
  * remove server discovery from manage transforms toolbar
  * always use trivialurldisplay
  * make showURL a stub in trivialurldisplay
  * remove google-me and wikipedia-me actions
  * remove all discover transforms actions
  * remove lots of webbrowser actions
  * enable transform limit toolbar

For that, I&#8217;ve put all modifications in _.diff_, _.jdiff_ or _.java_ where .diff is applied by standard POSIX **patch** utility, .jdiff is recompiled with **jasmine** and .java is compiled with jdk&#8217;s **javac** and integrated into target application.

**Instructions:**

  * Run cfpatch: <pre class="brush: plain; title: ; notranslate" title="">./cfpatch maltego-3.1.1_CE-2012-04-11.zip maltego-CF.1.0.1_community-2012-03-14.zip CF-custom.zip</pre>

  * Extact CF-custom.zip to the place where you want to install the custom CaseFile.

**Extra**
Create an .java file with the header:

<pre class="brush: plain; title: ; notranslate" title="">//target-contains: com/paterva/maltego/graph/MaltegoGraph.class
//filename: org/hopto/im/Test.java
</pre>

to integrate a new piece of software on Casefile. Example:

<pre class="brush: java; title: ; notranslate" title="">//target-contains: com/paterva/maltego/graph/MaltegoGraph.class
//filename: org/hopto/im/Test.java

// the above lines are to indicate that this class will be added
// in the same JAR module that file com/paterva/maltego/graph/MaltegoGraph.class
// and that the original name of this file is org/hopto/im/Test.java

package org.hopto.im;
public class Test {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
</pre>

All the working scripts and tools can be found at: <https://github.com/paoloo/casefile-extender>
