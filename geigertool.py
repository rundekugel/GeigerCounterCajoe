#!/usr/bin/env python3
"""
geiger counter tool
options:
-hex   view hexdump
-d=<format codes>  show values as u32,u16,s32,s16,float,double
-b=<baudrate>
-p=<portname>
-bs=<blocksize>
-xo=<0|1>          xon/xoff
-ts=<0|1|r>          timestamp on/off/relative
"""

import serial
import time
import sys,os
import struct

__version__ = "0.1.0"

#print(sys.version)
py3 = sys.version_info[0]==3

baudrate= 19200
baudrate= 20000
port="/dev/ttyUSB0"
xonoff = 0
verbosity=0
  
U8="B"
S8="b"
U16="H"
S16="h"
U32="I"
S32="i"
U64="Q"
S64="q"
f32="f"
f64="d"  
  
if sys.version_info[0] == 2:
  stringinstance = basestring
elif sys.version_info[0]==3:
  stringinstance = str
else:
  raise Exception("unknown python version: "+ str(sys.version_info))
    

WHITESPACES = [0,7,8,9,10,12,0xff]
def hexdump(src, length=16, startaddr=0):
  """
  :param src: bytes or string
  :param length: bytes per line
  :param startaddr: if None, it won't be displayed
  :return: hexdump as string
  """
  if not src:
    return "{}"
  if length < 1: length = 1
  if sys.version_info.major!=2:
    return  hexdump3(src, length, startaddr)
  result = []
  digits = 2
  if not isinstance(src, stringinstance):
    src = bytes2string(src, nullterminated=False)
  for i in range(0, len(src), length):
     s = src[i:i+length]
     hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])
#       text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
     text = b''.join([x if not ord(x) in WHITESPACES else b'.'  for x in s])
     if startaddr != None:
        result.append(b"%04X   %-*s   %s" % (startaddr + i, length * (digits + 1), hexa, text))
     else:
       result.append(b"%-*s   %s" % (length * (digits + 1), hexa, text))
  return os.linesep.join(result)

def hexdump3(src, length=16, startaddr=0):
    """hexdump for python 3""" +hexdump.__doc__
    result = []
    digits = 2
    if not isinstance(src, stringinstance):
      src = bytes2string(src, nullterminated=False)
    for i in range(0, len(src), length):
       s = src[i:i+length]
       hexa=''
       text=""
       for x in s:
        hexa+= " %02X" % (x)
        text += chr(x) if not x in WHITESPACES  else '.'
       if startaddr != None:
        result.append( "%04X\t %-*s   %s" % (startaddr +i, length*(digits + 1), hexa, text) )
       else:
         result.append("%-*s   %s" % ( length * (digits + 1), hexa, text))
    return os.linesep.join(result)


def bytes2string(bytesa, nullterminated = True):
  if sys.version_info.major==3:
    return bytes2string3(bytesa, nullterminated )
  t=b""
  for c in bytesa:
    if c == 0 and nullterminated:
      return t
    t += chr(c)
  return t

def bytes2string3(bytesa, nullterminated = True):
  '''Converts byte list to bytestring'''
  t = bytearray(b'')
  for c in bytesa:
    if c == 0 and nullterminated:
      return bytes(t)
    t.append(c)
  return bytes(t)


def dumpasfloat(t):
  if len(t)<4:
    return "-"
  r=[]
  #t=string2bytes3(t)
  for p in range(len(t)-4):
    f=struct.unpack("<f",t[p:p+4])[0]
    r.append(f"<{f:3.3f}")
    f=struct.unpack(">f",t[p:p+4])[0]
    r.append(f">{f:3.3f}")
  return "; ".join(r)
  
def dumpasdouble(t):
  if len(t)<8:
    return "-"
  r=[]
  #t=string2bytes3(t)
  for p in range(len(t)-8):
    f=struct.unpack("<d",t[p:p+8])[0]
    r.append(f"<d{f:3.3f}")
    f=struct.unpack(">d",t[p:p+8])[0]
    r.append(f">d{f:3.3f}")
  return "; ".join(r)
  
def dumpasS32(t):
  if len(t)<4:
    return "-"
  r=[]
  for p in range(len(t)-4):
    f=struct.unpack("<I",t[p:p+4])[0]
    r.append(f"<i{f}")
    f=struct.unpack(">I",t[p:p+4])[0]
    r.append(f">i{f}")
  return "; ".join(r)
  
def dumpasS16(t):
  if len(t)<2:
    return "-"
  r=[]
  for p in range(len(t)-2):
    f=struct.unpack("<H",t[p:p+2])[0]
    r.append(f"<h{f}")
    f=struct.unpack(">H",t[p:p+2])[0]
    r.append(f">h{f}")
  return "; ".join(r)

def decode0(t):
    r = ""
    t = t.decode("utf-8", "ignore")
    if t[:7] == "v*10000":
      v = t[7:-3]
      r = ("accumulated microS: " + v, float(v) / 10000)
      return r
    if t[:8] == "1000*usv":
      v = r[10:-3]
      r = ("usv/h: " + v, float(v) / 1000)
    return r


def decode(t):
  r = ""
  try:
    t = t.decode("utf-8", "ignore")
    if t[:7] == "v*10000":
      t=t[7:].split('l')[0]
      v= float(t)/10e3
      r=(">>>1 usv acc: "+t, round(v,7) )
      datacontainer.usa = v
      return r
    if "v*10000" in t:
      t=t.split("v*10000")[1].split('l')[0]
      v= float(t)/10e3
      r=(">>>usv acc: "+t, round(v,7) )
      datacontainer.usa = v
      return r
    if t[:8] == "1000*usv":
      t=t[8:-2]
      v = float(t) / 10e2
      datacontainer.ush = v
      r=(">>>1usv/h: " + t, round(v,4))
      return r
    if "usv/h" in t:
      t=t.split("usv/h")[1].split('l')[0]
      v = float(t) / 10e2
      datacontainer.ush = v
      r=(">>>usv/h: "+t, round(v,4) )
      return r
    if "ADC7" in t:
      t= t.split("e")[1].split("l")[0]
      v = float(t) / 900*100
      datacontainer.bat = v
      r=(">>>batt: "+t, round(float(t)/900*100,1))
  except:
    pass
  return r


def string2bytes3(text):
  '''converts strings to byte array. for python3'''
  if isinstance(text, bytes):
      return [x for x in text] #change bytearray to bytelist
  p=0
  bytea = []
  while (p +1) <= len(text):
    b = text[p]
    try:
      b = ord(b)
    except:
      b=0
    bytea += [b]
    p+=1
  return bytea

def getTimestamp():
  r=""
  t= time.localtime(time.time())[3:6]
  
  try:
    t10= str(time.time()).split('.')[1][:1]
  except:
    t10 = "0"
  r=f"{t[0]:02}:{t[1]:02}:{t[2]:02}.{t10:} "
  return r
  
class datacontainer:
    ush = None
    usa = 0
    bat = None

    @staticmethod
    def ToString():
      ush = datacontainer.ush
      if not ush:   ush = 0
      bat = datacontainer.bat
      if not bat:  bat = 0
      s = f"µS/h:{ush:5.2f} ; µS acc:{datacontainer.usa:7.4f} ; Bat:{bat:4.1f}"
      return s

#-- main --
def main():
  global baudrate, port, xonoff, verbosity
  doHex=0
  allFormat=0
  formats=[]
  timestamp=0
  
  print("Reader for Cajoe Geiger Counter Version:"+__version__)
  
  try:
    for p in sys.argv:
      if p =="-hex":
        doHex=1
        blocksize=16
      if p[:3]=="-p=":
        port=p[3:]
      if p[:3]=="-b=":
        baudrate=int(p[3:])
      if p[:4]=="-xo=":
        xonoff=int(p[4:])
      if p[:3]=="-t=":
        timeout=int(p[3:])
      if p[:4]=="-all":
        allFormat =1
      if p[:3]=="-d=":
        formats += p[3:].split(';')
      if p[:4]=="-ts=":
        timestamp =p[4:]
      if p[:4]=="-bs=":
        blocksize=int(p[4:])
      if p[:3]=="-v=":
        verbosity=int(p[3:])
      if p in ("?","-?","-h"):
        print(__doc__)
  except: 
    print("error parsing args!")

  print(f"baud:{baudrate}, port:{port}, pyver:{sys.version}")
  s=serial.Serial(port=port, baudrate=baudrate, timeout=2)
  print("Waiting for incoming data...")
  doit = 1
  lasttime=time.time()
  while doit:
    r=s.read(20)
    if r:
      if timestamp:
        if timestamp=='r':
          print(f"D:{time.time() - lasttime:05.1f} ", end="")
          lasttime=time.time()
        else:
          print(getTimestamp(), end="")
      if doHex:
        print(hexdump(r))
        if allFormat:
            print(dumpasfloat(r))
            print(dumpasS16(r))
            print(dumpasS32(r))
            print(dumpasdouble(r))
      else: 
        if verbosity>2:
          print(r.decode("utf-8","ignore"))
      d =decode(r)
      if verbosity:
        print(d)
      print(datacontainer.ToString())

#--- main call ---  
main()

#eof
