# cometblue-asyncio

This is a Python library for interacting with the Eurotronic Comet Blue
thermostatic radiator valves and their clones (see below).

It is a refactored fork of @zero-udo/eurotronic-cometblue with additional
credits to @rikroe and
[Thorsten Tränker](https://www.torsten-traenkner.de/wissen/smarthome/heizung.php).

What sets it aside from other Comet Blue libraries?

- It is built on @hbldh/bleak, which is well-designed, up-to-date and
  functional. Do you know that e.g. pygatt will only work under root, because
  it will _fully restart your system BlueZ service_ upon every connection?
  I had serious issues with that until I switched to bleak.

- It is simple, minimalistic and does only what you ask for. The bluetooth
  communication is minimal, it only sends the commands that you explicitly
  request. Some other libs try to e.g. download everything on first/each
  connection, which takes forever.

- (Once refactoring is finished) Pythonic, no scaffolding code with hidden
  typos. API expects sane programmers, no babysitting through excess
  sanitization of unthinkable input combinations.

## Compatible devices

I have tested it on _Silvercrest RT2000BT_. The original library was tested on
_Eurotronic Comet Blue_ and _Sygonix HT100 BT_. It should also work on _Xavax
Hama_ (untested).

My own _Silvercrest RT2000BT_ has the issue that it sometimes randomly messes
up its programmed weekly schedule. The frequency in which it happens is
correlated with the the frequency of bluetooth communication, however it is not
caused by this library specifically, because it happens even if I only use the
original Eurotronic Android app (any of the 2 versions). The solution for me is
to check the schedule every few connections and correct it programatically.

## Installation

```
pip install cometblue-asyncio
```

## Usage

Sorry, so far no more documenation than:

```python
from cometblue-asyncio import CometBlue

help(CometBlue)
```
