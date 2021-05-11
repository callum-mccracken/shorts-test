#!/usr/bin/python
import os
import math
import argparse
parser = argparse.ArgumentParser(description='Translates mappings for fun')
parser.add_argument('-q', metavar='quad', required=True,  help='Quad [QS1P/C, QS2P/C, QS3P/C, QL1P/C, QL2P/C, QL3P/C]')
parser.add_argument('-l', metavar='layer', required=True,  help='Layer number [1...4]')
parser.add_argument('-e', metavar='electrode', required=True,help='Electrode type [wire/pad/strip]')
parser.add_argument('-m', metavar='mapping', required=True,help='Mapping [VMM, Alam, Benoit]')
parser.add_argument('-c', metavar='channel', required=True,help='Channel number [... (for VMM, use e.g. 1:8)]')
argus = parser.parse_args()


def read(quad,layer,etype):
   fIn = open("mapping.txt",'r')
   channels = []
   for line in fIn:
      words = line.split()
      if(quad  not in words[0]): continue
      if(layer not in words[2]): continue
      if(etype not in words[3]): continue
      channels.append( {"VMMid":int(words[4]), "VMMch":int(words[5]), "Benoit":int(words[6]), "Alam":int(words[7]), "GFZ Connector":words[9], "GFZ Pin":words[10], "GFZ Channel":words[11]} )
   fIn.close()
   return channels

def get(mapping, channel, channels):
   c = "channel not found"
   for chn in channels:
      if(mapping=="VMM"):
         if(channel != str(chn["VMMid"])+":"+str(chn["VMMch"])): continue
      else:
         if(channel != str(chn[mapping])): continue
      c = chn
      break
   return c

### do the work
channels = read(argus.q, argus.l, argus.e)
print("got %g channels" % len(channels))
# print(channels)
channel = get(argus.m, argus.c, channels)
print(channel)
