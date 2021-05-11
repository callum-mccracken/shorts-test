#!/usr/bin/python3

""" Renamer.py: Script which renames old short-test format files into new format """
__author__ = "Jacob Syndikus"
__date__ = "9/29/2020"

from os import listdir, system
from datetime import datetime

originalFiles = listdir(".")
newFiles = list()

for i in range(len(originalFiles)):
    if ".xlsx" in originalFiles[i]:
        newName = originalFiles[i].replace("Python\\Results\\","")
        # Pad and Strip Name
        if "Pad" in newName:
            newName = newName.replace("Pad_","")
            ending = "_P_P1.xlsx"
        elif "P2_Strip" in newName:
            newName = newName.replace("P2_Strip_","")
            ending = "_S_P2.xlsx"
        elif "P1_Strip" in newName:
            newName = newName.replace("P1_Strip_","")
            ending = "_S_P1.xlsx"
        # Layernumber
        ending = "LAYER{}{}".format(newName[4], ending)
        # Quad Name and date extraction
        if "QL1" in newName:
            date = datetime.strptime(newName[6:-5:],'%d-%m-%Y-%H-%M-%S')
            beginning = "QL1_C_9/"
            ending = "_sTGC_QL1_C_9_{}".format(ending)
        elif "QL2" in newName:
            date = datetime.strptime(newName[6:-5:],'%d-%m-%Y-%H-%M-%S')
            beginning = "QL2_C_7/"
            ending = "_sTGC_QL2_C_7_{}".format(ending)
        elif "QL3" in newName:
            date = datetime.strptime(newName[6:-5:],'%d-%m-%Y-%H-%M-%S')
            beginning = "QL3_C_11/"
            ending = "_sTGC_QL3_C_11_{}".format(ending)
        # Date
        datestr = date.strftime("%Y_%b_%d")
        # Add new filename to list
        system("mv {} {}".format(originalFiles[i].replace("\\","\\\\"), beginning + datestr + ending))
