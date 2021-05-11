#!/usr/bin/python3

currentTwiki = open("files/currentTwikiPage.txt",'r')
quadname = ""
layer = ""
etype = ""
gFZConnector = ""
channel = ""
comment = ""
debug = False
position = ""

def read(quad,layer,etype):
   fIn = open("files/NSW_sTGC_Channel_Mapping-master/mapping.txt",'r')
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




for i in currentTwiki:
    splitted = i.split("|")
    # removes previous VMM mapping
    if len(splitted) == 8:
        del splitted[4]
    # Bugfix, as some entries have 4 Space before a Layer
    if i[3:5] == "  ":
        i = i[:3] + i [5:]
    # Or before a ^
    if "  ^  " in i:
        i = i.replace("  ^  ","^")
    # actual code
    if i == "\n":
        continue
    elif i[0] != '|' and i[0] != '-':
        print(i)
        continue
    elif i[0:5] == "---++":
        quadname = "{}{}".format(i[5:8],i[9])
        print("\n\n{}".format(i))
        continue
    elif splitted[1][0:4] == '  *G':
        print("|  *GFZ Connector*  |  *GFZ Ch.*  |  *Alam Ch.*  |  *VMM Ch.*  |  *Position*  |  *Action / Comment*  |")
        continue
    elif "Layer" in splitted[1]:
        layer = i[9]
        if i[11] == 'S':
            etype = "strip"
            gFZConnector = i[13:15]
        elif i[11] == 'P':
            if int(splitted[2].strip()) >= 128:
                etype = "wire"
            else:
                etype = "pad"
            gFZConnector = 'P1'
        channel = splitted[2].strip()
        position = splitted[4].strip()
        comment = splitted[5].strip()
    elif i[1] == '^':
        channel = splitted[2].strip()
        position = splitted[4].strip()
        comment = splitted[5].strip()
    if debug: print(quadname)
    if debug: print(layer)
    if debug: print(etype)
    if debug: print(gFZConnector)
    if debug: print(channel)
    if debug: print(comment)
    if debug: print(position)
    
    channels = read(quadname, layer, etype)
    channelAll = get("GFZ Channel", channel, channels)
    try:
        # Fixes Error of accidently choosing a P2 connector when in a P1
        if gFZConnector == 'P1' and int(channelAll['Alam']) >= 256:
            print("|  {}  |  {}  |  {}  |  {}:{}  |  {}  |  {}  |".format(splitted[1].strip(), channel, int(channelAll['Alam'])-256, int(channelAll['VMMid'])+4, channelAll['VMMch'], position, comment))
        else:
            print("|  {}  |  {}  |  {}  |  {}:{}  |  {}  |  {}  |".format(splitted[1].strip(), channel, channelAll['Alam'], channelAll['VMMid'], channelAll['VMMch'], position, comment))
    except TypeError:
        print(i,end="")
#    print("|  {}  |  {}  |  {}  |  {}  |  {}  |  {}:{}  |  {}  |  {}  |".format(quadname, layer, gFZConnector, etype, channel, channelAll["VMMid"], channelAll["VMMch"], position, comment))
