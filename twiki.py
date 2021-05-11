#!/usr/bin/python3

""" Program which outputs all shorts-test-errors in a format suitable for the ATLAS Twiki """
__author__ = "Jacob Syndikus"
__date__ = "9/29/2020"

import matplotlib.pyplot as plt
from os import listdir
import xlrd
import sys
from files.functions import Pin2GFZChannel

# Prints Layer name
def haserror(string):
    print("|  Layer {}  |  {}".format(gfzlist[i][j][-11:-5].replace("P_P1","Pad").replace("_"," "), string))
    return

# Debug options
debug = False
debugColor = False

# Global variables
allok = True
oldFormat = ""

# Get all Excel sheets for each gfz connector on a wedge
quadlist = sorted(listdir("./Results"))
gfzlist = list()
for quad in quadlist:
    gfzlist.append(sorted(listdir("./Results/"+quad)))
    for i in range(len(gfzlist[-1])):
        gfzlist[-1][i] = "./Results/" + quad + "/" + gfzlist[-1][i]

# once for the strips, once for the pads
connectorACValues = list()
# save them in an accessiable format
workbooks = list()
sheets = list()
num = 0
for i in gfzlist:
    workbooks.append(list())
    sheets.append(list())
    for j in i:
        if debug: print(j)
        try:
            workbooks[num].append(xlrd.open_workbook(j))
        except xlrd.biffh.XLRDError:
            sys.stderr.write("ERROR: Please close all excel sheets\n")
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        sheets[num].append(workbooks[num][-1].sheet_by_index(1))
    num = num + 1

# get the measurement data for all Errors data
for i in range(len(sheets)):
    allok = True
    print("\n\n---++{}\n".format(quadlist[i].replace("_",".")))
    print("|  *GFZ Connector*  |  *GFZ Ch.*  |  *Alam Ch.*  |  *Position*  |  *Action / Comment*  |")
    data = list()
    for j in range(len(sheets[i])):
        cnt = 3
        plotLayerName = True
        while True:
            output = ""
            try:
                try:                    
                    pos = round(float(sheets[i][j].cell_value(cnt,3)),1)
                except ValueError:
                    try:
                        pos = "PAR {}".format(round(float(sheets[i][j].cell_value(cnt,4)),1))
                    except:
                        pos = -999.0
                try:
                    if sheets[i][j].cell_value(cnt,2) == 'NONE' and int(sheets[i][j].cell_value(cnt,1)) != 999:
                        output += "{}  |  -  |  -  |  Shorted even though there is no channel behind  |".format(int(sheets[i][j].cell_value(cnt,1)))
                        allok = False
                        if plotLayerName:
                            haserror(output)
                            plotLayerName = False
                        else:
                            print("|^|  {}".format(output))
                    elif pos != -999.0 and int(sheets[i][j].cell_value(cnt,1)) != 999:
                        output += "{}  |  {}  |  {}  | |".format(int(sheets[i][j].cell_value(cnt,1)), sheets[i][j].cell_value(cnt,2), pos)
                        allok = False
                        if plotLayerName:
                            haserror(output)
                            plotLayerName = False
                        else:
                            print("|^|  {}".format(output))
                except ValueError:
                    if int(sheets[i][j].cell_value(cnt,2)) != 999:
                        output += "{}  |  {}  |  {}  | |".format(Pin2GFZChannel(sheets[i][j].cell_value(cnt,1)), sheets[i][j].cell_value(cnt,0), "Manual intervention needed")
                        allok = False
                        if plotLayerName:
                            haserror(output)
                            plotLayerName = False
                        else:
                            print("|^|  {}".format(output))
                        oldFormat += "Old format detected in file with name \"{}\". Please investigate!\n".format(gfzlist[i][j])
                    pass
                cnt += 1
            except IndexError:
                break
    if allok: print("|No shorted channels detected|||||")

# show errors resulting from old format
if debug: print(oldFormat)
