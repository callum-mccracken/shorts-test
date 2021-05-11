#!/usr/bin/python3

import pandas
import time

quad = 'QS3P'
layer = '2'
etype = 'strip'
gFZConnector = 'P2'

def read(quad,layer,etype,gFZConnector):
    fIn = open("files/NSW_sTGC_Channel_Mapping-master/mapping.txt",'r')
    channels = []
    for line in fIn:
        words = line.split()
        if(quad  not in words[0]): continue
        if(layer not in words[2]): continue
        if(etype not in words[3]): continue
        if(gFZConnector not in words[9]): continue
        channels.append( {"VMMid":int(words[4]), "VMMch":int(words[5]), "Alam":int(words[7]), "GFZ Pin":words[10], "GFZ Channel":words[11]} )
    fIn.close()
    return channels

start = time.time()
dataframe = pandas.DataFrame(read(quad, layer, etype, gFZConnector))
end = time.time()
print(dataframe)
print("Time needed: {}".format(end-start))
