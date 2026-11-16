---
title: "Scanning 90's Relic Using 2026's Services"
date: 2026-11-15 12:00:00 -0300
author: paolo
layout: post
permalink: /2026/11/15/scanning-90s-relic-using-2026s-services/
categories:
  - en-US
tags:
  - security
  - measurement
  - shodan
  - dialup
  - fax
  - telecommunications
excerpt: "I do not even have a proper POTS line anymore. I still wanted to know how much of the dial-up world survives on the public internet, so I pointed Shodan at it."
---

I do not even have a proper POTS line anymore. Nobody I know does. The copper
pair that used to bring 56 kbit/s into my house was pulled or ported years
ago, and the modem in the drawer is a paperweight(kinda, but this is another story lol)
That is exactly why I wanted to check this. If dial-up is dead in practice, what is still connected
to the public internet on its behalf? Not in archives, not in museums: live, scannable, answering right now.

So I ran a <b>biased</b> census. Shodan, an edu/research-enabled account, about fifty queries over a boring sunday
afternoon. The question is narrower than it sounds: Shodan sees IP-side
services, not phone lines. A modem bank itself is invisible unless something
IP-reachable sits in front of it. What I measured is the population of
*artifacts*: terminal servers, fax servers, ISDN card configuration planes,
outdial pools. Anything whose banner implies a POTS or ISDN data path still
wired somewhere behind it. I wish I could also wardial but, again, I have nothing similar to a proper phone line (and I checked, I cannot even order one)

## The banner that made the whole afternoon worth it

One host in Wichita Falls, Texas, on AT&T consumer address space, port 23:

```text
Trying...
Connected.
Escape character is '^]'.

Remote Access Terminal Server
Outdial Modem Pool / Switch Maintenance

Initializing modem channel...
+++
OK
AT&F1
OK
ATE1V1X3S7=45S8=2&C1&D2
OK
ATDT9,,1405W23
```

That is a live modem initializing. `AT&F1` resets to factory profile,
`ATE1V1X3S7=45S8=2&C1&D2` is a classic dial-in setup string (echo on, verbose
results, 45-second carrier wait, blind-dial pause, DCD/DTR handling), and
`ATDT9,,1405W23` is dialing out through a PBX: 9 for an outside line, two
comma pauses for the second dial tone, then the number, with a `W` waiting
for dial tone before the last digits. Someone's telnet session walks straight
into a Hayes-compatible handshake in 2026. The same host has an unauthenticated
management plane on telnet, which is a disclosure problem for someone, but the
banner alone is the best relic I found.

## The other banners that looked different

The interesting thing about a census like this is that each device class has
a signature frozen in its login string. Three worth showing.

The Livingston PortMaster, the classic early-90s dial-in terminal server,
still answering telnet on a CenturyLink address:

```text
ComOS - Livingston PortMaster

login:
```

The U.S. Robotics Total Control NETServer, its rival from the same era,
ten of the twelve surviving units on a single US ISP:

```text
U.S. Robotics
Total Control (tm) NETServer 8/16

login:
```

And the fax side, which turned out to be bigger than the dial-up side. A
HylaFAX server in Italy announcing itself over FTP like it is 1998:

```text
220 fifo.mynet.it server (HylaFAX (tm) Version 6.0.6) ready.
```

A Dialogic Diva ISDN card configuration web server, which means an ISDN
line is plugged into that card somewhere:

```text
HTTP/1.0 200 Ok
Server: DivaWebConfig
<title>Dialogic&reg; Diva&reg; Configuration</title>
```

A T38Modem bridge, fax-over-IP speaking SIP with its age in the User-Agent:

```text
SIP/2.0 200 OK
User-Agent: T38Modem/2.0.0
```

And one commercial FaxBack server whose SQL Server instance helpfully
announces its own name and product:

```text
SQL Server Browser Service:
  Instance #1:
    Server Name: T3-FAXBACK-01
    Instance Name: NETSATISFAXTION
    Version: 13.2.5026.0
```

## What the census found

Here is the final count, after the honeypot cleaning explained further
below. Note the log scale, because the distribution spans nearly three
orders of magnitude:

<figure>
  <img src="{{ site.baseurl }}/uploads/2026/11/dialup-fax-census.svg" alt="Log-scale bar chart of honeypot-cleaned Shodan-visible dial-up and fax artifacts, 15 November 2026: Westermo industrial dial routers 680, email-to-fax 252, HylaFAX 29, Internet Rex 17, Digi PortServer 30, Lantronix MSS100 15, Livingston PortMaster 6, live BBS/FidoNet systems 3." />
  <figcaption>Shodan-visible artifacts by class, honeypot-cleaned, 15 Nov 2026. Log scale.</figcaption>
</figure>

| Class | Hits | What it is |
|---|---|---|
| Westermo industrial dial/ISDN routers | 680 | MRD-315/350/355/455 on European utility and SCADA networks, live remote-maintenance dial lines |
| Email-to-fax (Kazoo/2600hz) | 252 | FoIP infrastructure, SMTP front ends, not POTS |
| HylaFAX | 29 | Open-source fax server, versions 6.0.6/6.0.7 in the banners |
| Internet Rex (FidoNet) | 17 | FidoNet mailers, some still handshaking EMSI on telnet |
| FaxBack / NetSatisFAXtion | 27 | Commercial fax server, full Windows stack exposed |
| Digi PortServer TS | 30 | Serial console servers still managed over the network, JP/MX/CL-heavy |
| Diva/Eicon ISDN config | 13 | ISDN/fax card admin planes, direct line implication |
| Lantronix MSS100 | 15 | 90s serial terminal servers, mostly rehomed into cloud ASNs |
| Livingston PortMaster | 6 | Legacy RAS hardware, CenturyLink/Windstream/Citytelecom/DE/CN/FR |
| T38Modem (FoIP) | 1 | Fax-over-IP bridge, Austria |
| USRobotics NetServer 8/16 | 1 | Legacy RAS hardware, the only genuine survivor of the "fleet" |
| Guru BBS / FrontDoor / MBSE | 3 | Live BBS and FidoNet mailer systems |

These counts exclude the honeypot farm described in the round two section
below. The MikroTik `RO BRAS DIAL-UP` boxes from my first pass are gone from
the table entirely: they are L2TP broadband routers with "dial-up" in their
hostnames, not POTS, and keeping them would have been classification by
branding.

Queries that returned nothing are part of the result too. Cisco AS5xxx access
servers, Ascend MAX, 3Com Total Control, Bay Annex, USR Courier, `CONNECT
56000`, ISDN backup, analog backup, PSTN backup: zero or near-zero. The
classic NAS fleet that once served the entire modem internet has essentially
vanished from public telemetry.

## Three things worth noting

The classic consumer dial-up RAS fleet is nearly extinct and concentrated.
PortMaster plus NETServer comes to seven genuine boxes worldwide, most of the
PortMasters on three US incumbent telephone company networks. This is the
tail of a decommissioned industry, visible only because the last units were
never turned off. The Round two section adds the twist: industrial dial-up,
which is not this fleet at all, is doing fine.

Fax is the survivor. The fax population (HylaFAX, FaxBack, Diva cards, T38
bridges, plus the 252 email-to-fax front ends) is an order of magnitude
larger and more diverse than the consumer dial-up RAS population. That
matches what you would expect from regulation and business practice:
healthcare, legal, and Japanese SMEs kept fax alive long after consumer
dial-up died, and the IP-side plumbing followed.

Dial-up backup is invisible to this method. I found exactly **one** banner
containing "dial backup", and it is a MikroTik router in Indonesia using the
phrase as a VPN label. Real dial backup, the DDR configuration that dials a
POTS line when a primary link fails, lives in router configs, not in banners.
Absence of banner evidence is not evidence that backup lines are gone, and I
am not claiming that. It's the opposite! I know for a fact that a few SCADA and government
services has dial up backup, but this is also another story lol.

## Round two: industrial dial-up is alive, and I got fooled by a honeypot farm

I went back for a second pass the same day, chasing the classes I had missed,
and the biggest thing I found was not a new device. It was an error in my own
method.

Some of the banners in the first pass were too good. The U.S. Robotics
NETServer "fleet", ten of twelve units on a single ISP, a host answering with
a thousand different services on a thousand ports, another one with
`Sportster Pro ... Sagem D-BOX2` banners on random ports next to `550 4m2v4
FUZZ_HERE` SMTP greetings. That last string was the giveaway: `FUZZ_HERE` is
a placeholder from a protocol fuzzer. What I had caught was a **honeypot and
tarpit farm**: whole netblocks (a `/24` and a `/22`, both on the same
hosting operator) where hundreds of IPs answer on hundreds of ports with
synthetic banners sampled from a corpus of 90s software. The bitmask junk
(`550 12345 0ffffff7000000...`) on every port was the same fingerprint.

So the first numbers I had were polluted, and the table above is the
corrected one. The lesson generalizes: a census built on banner
classification is only as good as your ability to distinguish a genuine 1995
banner from a 2026 server *pretending* to be one. The honeypots are, in
their own way, a monument to the same nostalgia.

Now the good news, because the second pass found the real treasure.

**Westermo industrial dial/ISDN routers: 680 of them, all over Europe.** This
is the largest class in the entire census and it was invisible to my first
queries. The MRD series (MRD-315, MRD-350, MRD-355, MRD-455) are industrial
PSTN and ISDN dial routers used for remote maintenance of SCADA, substations,
traffic cabinets, water plants. They sit on Telia in Sweden, Vodafone in
Czechia, Eircom in Ireland, dozens on Spanish utility networks, plus Poland,
Denmark, Norway, UK, France. One French unit answered SNMP with firmware
compiled **August 2026**. This is not a relic. This is live infrastructure
that industry still installs on purpose, because a dial line does not route
through the internet and does not care about your VPN. The consumer modem is
dead; the industrial dial-up is quietly thriving.

**A real BBS, on a real residential line, still answering.** Guru BBS in
Czechia (`bbs.bajer.cz`, on Vodafone residential address space) announces
itself on FTP with full ASCII art:

```text
220-         GGGGGG UU   UU RRRRRR  UU   UU         BBBBBB  BBBBBB   SSSSS
220-        GG      UU   UU RR   RR UU   UU         BB   BB BB   BB SS
220-        GG  GGG UU   UU RRRRRR  UU   UU         BBBBBB  BBBBBB   SSSSS
220-        GG   GG UU   UU RR RR   UU   UU         BB   BB BB   BB      SS
220-         GGGGGG  UUUUU  RR  RR   UUUUU          BBBBBB  BBBBBB  SSSSSS
220-
220-                Operating 24 hours a day,
220-                7 days a week.
220-                V.90/x2/V.34/V.FC/V.32terbo/HST/V.32bis/V.32/V.22bis/V.22
220-                Your system operator: Milos Bajer (milos@bajer.cz)
220 FtpServer 2.78 ready
```

That modem list is a fossil record: V.32terbo and USRobotics HST were
proprietary pre-V.34 standards from around 1992. The box runs OS/2. Whether
the phone line behind it still answers, I cannot verify from here, but the
software stack is up and the sysop is reachable.

**FidoNet is still transferring mail.** The Sursum Corda! BBS on a Comcast
residential line runs Internet Rex 2.67 for OS/2: FTP, POP3, SMTP, and on
port 23, an actual FidoNet EMSI handshake:

```text
**EMSI_REQA77E
```

Another host in the US runs FrontDoor 24.01, the classic FidoNet mailer,
which answers with `**EMSI_MD5...**EMSI_REQA77E` and the message
`Press <Esc> twice for Maximus`. There is a MBSE BBS in Poland, T-Mail
mailers in Russia, a FidoNet nodelist FTP mirror in Europe. The BBS world
did not die; it moved to TCP/IP and kept the same handshake protocol running
for thirty years.

**Serial terminal servers are still managed from web pages.** Digi
PortServer TS units (Japan's OPTAGE ISP runs a small fleet, TOTAL PLAY in
Mexico has 15, Telefonica Chile 5), Lantronix MSS100 units rehomed into
cloud providers, one Xyplex in Taiwan answering only SNMP. These are the
un glamourous descendants of the terminal server lineage that the PortMaster
started.

I also owe the MikroTik `RO BRAS DIAL-UP` hosts a correction: those
Indonesian boxes are labeling themselves "dial-up" but they are L2TP
broadband routers, branding rather than POTS. Classifying them as dial-up
was my error, and they drop out of the census entirely.

The usual caveat applies to all counts: Shodan sees what its scanners can
reach. Cloud and hosting networks are over-represented, and anything behind
NAT or a firewall is invisible. These numbers are a floor, not a proper census. The
honest version of the claim is: at least this many relics are answering on
the public internet in 2026, and the true population is larger.

All raw queries, banners, and host records are in the research package, and
the census is repeatable with the scripts there if you want to run your own
count or watch the population decay over time. I might do the longitudinal
version next year; the decay curve of the last PortMasters is a dataset that
only gets more interesting as it shrinks toward zero.
