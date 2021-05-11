import serial
#from libreria import separar, portIsUsable
import sys
import glob
import math

# necessary for window class
import os
from tkinter import *
import subprocess
import time
import datetime
from tkinter import messagebox
from PIL import Image
import files.QABmap
import files.setchan

class Channel():

    def __init__(self, info, ADC_ref=1.1, reversed_x=True):
        self.multiplexer = info[0]

        if info[0]=='A':
            self.mult = 0
        elif info[0]=='B':
            self.mult = 1
        elif info[0]=='C':
            self.mult = 2
        elif info[0]=='D':
            self.mult = 3
        elif info[0]=='E':
            self.mult = 4
        elif info[0]=='F':
            self.mult = 5
        elif info[0] == 'G':
            self.mult = 6
        else:
            self.mult = -1


        self.port = info[1]
        self.pin = info[2]

        self.gfz = info[3]
        self.gfzchannel = Pin2GFZChannel(info[3])


        self.x = int(info[4])
        if reversed_x:
            self.y = int(info[5])
        else:
            self.y = 10-int(info[5])

        self.name = info[6]


        self.resistance = 470
        self.ADC_REF = ADC_ref
        self.ADC_DC = 0
        self.ADC_AC = 0
        self.currentDC = 0
        self.currentAC = 0
        self.voltageDC = 0
        self.voltageAC = 0
        self.short_resistance = 0



        self.responseDC = ""
        self.responseAC = ""

        self.info = str(self.multiplexer) + ', ' + self.port + ', ' + self.pin
        self.info2 = str(self.mult) + ',' + self.port + ',' + self.pin

        self.connection = False
        self.cc = False
        self.errors = []
        self.summary = []
        self.messages = []
        self.pad_map = 'NA'
        self.PARposition = 'NA'
        self.position = 'NA'


    def update(self):
        format_str = '{0:.3g}'
        self.summary = [self.multiplexer, self.port, self.pin, self.ADC_DC, format_str.format(self.voltageDC), format_str.format(self.currentDC), self.ADC_AC, format_str.format(self.voltageAC), self.gfz, self.name, self.pad_map]
        for i in self.messages:
            self.summary.append(i)



    def calculate_short_res(self, V):
        self.short_resistance = calculate_equivalent_resistance(self.ADC_DC, V)


    def mult_list(self):
        return [self.multiplexer, str(self.port), str(self.pin)]




    def update_VI(self):
        self.voltageDC = self.ADC_DC * self.ADC_REF / 1024
        self.voltageAC = self.ADC_AC * self.ADC_REF / 1024

        self.currentDC = (self.voltageDC / self.resistance) * 1000
        self.currentAC = (self.voltageAC / self.resistance) * 1000


def mensaje(msj,deb=False):
    msj = msj.decode("utf-8")
    primer = msj[0]
    if primer == '#':
        splited = msj.split(',')
        mensaje = splited[1:splited.index('$')]
        if deb:
            print(mensaje)
        primer = mensaje[0]

        if primer=='I':
            return 1
        elif primer=='E':
            return 2
        elif primer=='L':
            return 3
        elif primer=='R':
            return 4
        elif primer=='C':
            return 5
        elif primer=='Q':
            return 6
        elif primer=='$':
            return -1
        else:
            return 0
    else:
        ##if(debug):
            ##print('Error decodificando')
        return 0

def check(msj1,msj2,debug=False):
    msj1 = msj1.split(',')
    msj2 = msj2.split(',')
    if msj1==msj2[1:4]:
        if debug:
            print(msj2)
    else:
        print('Communication error')

def grounds(list):
#    new = Channel(['G', '2', '0', 'G0', '4', '6', 'GND'])
    for ch in list:
        if ch.gfz == 'G0':
            ch.pad_map = 'GND'
            new = ch

        elif 'G' in ch.gfz:
            ch.port = new.port
            ch.pin = new.pin
            ch.multiplexer = new.multiplexer
            #ch.mult = new.mult

            ch.currentDC = new.currentDC
            ch.currentAC = new.currentAC

            ch.responseDC = new.responseDC
            ch.responseAC = new.responseAC

            ch.info = new.info
            ch.info2 = new.info2

            ch.connection = new.connection
            ch.cc = new.cc
            #ch.errors = new.errors
            ch.summary = new.summary
            ch.messages = new.messages

            ch.pad_map = 'GND'

            ch.update()

def encodeMessage(message):
    string = ''
    for item in message:
        string = string + str(item)

    return string.encode('utf-8')

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def portIsUsable(portName):
    try:
        return serial.Serial(portName)
    except:
        return False

def escexcell(info,fila,hoja,offset,color):
    for i in range(len(info)):
        hoja.write(fila,i+offset, info[i],color)

def calculate_RS_drop(Req, V=4.9, Rs=470, ADC_ref=1.1):
    # Calculates the expected ADC code [0,1023] based on an equivalent resistance
    I = V/Req
    V_ADC = Rs*I
    ADC_code = 1024*V_ADC/ADC_ref
    return int(ADC_code)

def calculate_ADC_code(Rc, V, Rp=9530, Rs=470, ADC_ref=1.1):
    #Calculates the expected ADC code [0,1023] based on an short circuit resistance
    Req = ((Rc+Rp)*Rp+Rs*(Rc+2*Rp))/(Rc+2*Rp)
    I = V/Req
    V_ADC = Rs*I
    ADC_code = 1024*V_ADC/ADC_ref
    return int(ADC_code)


def calculate_PCA_Voltage(ADC_code, Rp=9530, Rs=470, ADC_ref=1.1):
    #Calculates the expected Voltage at the output of a PCA9698 based on an adc reading
    Req = Rp + Rs
    V_ADC = (ADC_code * ADC_ref)/1024
    I = V_ADC / Rs
    V = Req * I
    return V


def calculate_equivalent_resistance(ADC_code, V, Rp=9530, Rs=470, ADC_ref=1.1):
    V_ADC = (ADC_code * ADC_ref)/1024
    I = V_ADC / Rs
    Req =  V / I

    if Req < (Rp+Rs):
        Rc = (2*Req*Rp - Rp*Rp - 2*Rs*Rp) / (Rp + Rs - Req)
    else:
        Rc = 2731515

    return int(Rc)

def correlated_pins(chns, errors):
    err_lst = []
    for ch in chns:
        for err in errors:
            if ch.mult_list() == err:
                err_lst.append([ch.pad_map, ch.name])
                pass
    return err_lst



if __name__ == "__main__":
    import pandas as pd
    results_df = pd.DataFrame(columns=['1', '2'])
    for i in range(20):
        results_df.loc[str(i), '1'] = i

        pass

    print(results_df)


def Pin2GFZChannel(pin):
    chan = 999
    letter = pin[:1]
    n = pin[1:len(pin)]
    num = int(n)

    if letter == "i":
        chan = 255 - num
   
    elif letter == "j":
        chan = 127 - num 

    return chan



STRIPPITCH=3.2

def NumberToPosition(WEDGEANGLE, AB, objectNumber):
    position = -999
    if "S" in AB:
        position=(int(objectNumber)-9)*(STRIPPITCH/math.cos(WEDGEANGLE))+1.685
    return position

def NumberToPosition_QL3Par(AB, objectNumber):
    position = -999
    if "S" in AB:
        position=(352-int(objectNumber)-9)*(STRIPPITCH)+1.685
    return position

# Window class for unified GUI
class Window2:
    # Initialize window
    def __init__(self, master):
        self.frame2 = Frame(master)


        STGCdef = StringVar()
        UNIQUEdef = StringVar()
        LAYERdef = StringVar()
        ABdef = StringVar()
        GFZdef = StringVar()
        PCdef = StringVar()

        # Set default values for the GUI window
        STGCdef.set("QS3")
        UNIQUEdef.set("wedge1")
        LAYERdef.set("2")
        ABdef.set("S")
        GFZdef.set("P1")
        PCdef.set("P")

        #stgcframe = Frame(padx=50, pady=10)
        #stgcframe.pack()
        #stgclabel = Label(stgcframe, text='sTGC Type: (ex: QS1)', width=25)
        #stgclabel.pack(side=LEFT)
        #self.stgc = Entry(stgcframe, width=25, textvariable=STGCdef)
        #self.stgc.pack(side=RIGHT)

        stgcframe = Frame(padx=50, pady=10)
        #stgcframe.pack()
        stgclabel = Label(stgcframe, text='sTGC Type', width=25)
        stgclabel.pack(side=LEFT)
        stgc = StringVar()
        QS1 = Radiobutton(stgcframe, text='QS1', variable=stgc, value='QS1')
        QS2 = Radiobutton(stgcframe, text='QS2', variable=stgc, value='QS2')
        QS3 = Radiobutton(stgcframe, text='QS3', variable=stgc, value='QS3')
        QL1 = Radiobutton(stgcframe, text='QL1', variable=stgc, value='QL1')
        QL2 = Radiobutton(stgcframe, text='QL2', variable=stgc, value='QL2')
        QL3 = Radiobutton(stgcframe, text='QL3', variable=stgc, value='QL3')
        self.stgc = stgc

#        stgcframe.columnconfigure(0, pad=3)
#        stgcframe.columnconfigure(1, pad=3)
#        stgcframe.columnconfigure(2, pad=3)
#        stgcframe.columnconfigure(3, pad=3)
#
#        stgcframe.rowconfigure(0, pad=3)
#        stgcframe.rowconfigure(1, pad=3)
#        stgcframe.rowconfigure(2, pad=3)
#        stgcframe.rowconfigure(3, pad=3)
#        stgcframe.rowconfigure(4, pad=3)
#
#        QS1selected_map_filename[:2].grid(column=1, row=1 )
#        QS1HV1.grid(column=2, row=1 )
#        QS2.grid(column=3, row=1    )
#        QS3.grid(column=4, row=1    )
#
#        QL1HV0.grid(column=1, row=2 )
#        QL1HV1.grid(column=2, row=2 )
#        QL2.grid(column=3, row=2    )
#        QL3.grid(column=4, row=2    )

        QL3.pack(side=RIGHT)
        QL2.pack(side=RIGHT)
        QL1.pack(side=RIGHT)
        QS3.pack(side=RIGHT)
        QS2.pack(side=RIGHT)
        QS1.pack(side=RIGHT)


        stgcframe.pack()



        PCframe = Frame(padx=50, pady=10)
        PCframe.pack()
        #PClabel = Label(PCframe, text='Pivot or Confirm: [P,C]', width=25)
        PClabel = Label(PCframe, text='Pivot or Confirm: ', width=25)
        PClabel.pack(side=LEFT)
        Pivot = Radiobutton(PCframe, text='Pivot', variable=PCdef, value='P')
        Confirm = Radiobutton(PCframe, text='Confirm', variable=PCdef, value='C')
        #self.PC = Entry(PCframe, width=25, textvariable=PCdef)
        self.PC = PCdef
        Confirm.pack(side=RIGHT)
        Pivot.pack(side=RIGHT)

        uniqueframe = Frame(padx=50, pady=10)
        uniqueframe.pack()
        uniquelabel = Label(uniqueframe, text='Unique Identifier: (ex: wedge1)', width=25)
        uniquelabel.pack(side=LEFT)
        self.unique = Entry(uniqueframe, width=25, textvariable=UNIQUEdef)
        self.unique.pack(side=RIGHT)

        layerframe = Frame(padx=50, pady=10)
        layerframe.pack()
        layerlabel = Label(layerframe, text='Layer Number: [1-4]', width=25)
        layerlabel.pack(side=LEFT)
        One = Radiobutton(layerframe, text='1', variable=LAYERdef, value='1')
        Two = Radiobutton(layerframe, text='2', variable=LAYERdef, value='2')
        Three = Radiobutton(layerframe, text='3', variable=LAYERdef, value='3')
        Four = Radiobutton(layerframe, text='4', variable=LAYERdef, value='4')
        #self.layer = Entry(layerframe, width=25, textvariable=LAYERdef)
        self.layer = LAYERdef 
        #self.layer.pack(side=RIGHT)
        Four.pack(side=RIGHT)
        Three.pack(side=RIGHT)
        Two.pack(side=RIGHT)
        One.pack(side=RIGHT)

        ABframe = Frame(padx=50, pady=10)
        ABframe.pack()
        #ABlabel = Label(ABframe, text='Adapter Board: [S,P]', width=25)
        ABlabel = Label(ABframe, text='Adapter Board: ', width=25)
        ABlabel.pack(side=LEFT)
        Strip = Radiobutton(ABframe, text='Strip', variable=ABdef, value='S')
        Pad = Radiobutton(ABframe, text='Pad', variable=ABdef, value='P')
        #self.AB = Entry(ABframe, width=25, textvariable=ABdef)
        self.AB = ABdef
        Pad.pack(side=RIGHT)
        Strip.pack(side=RIGHT)

        gfzframe = Frame(padx=50, pady=10)
        gfzframe.pack()
        #gfzlabel = Label(gfzframe, text='GFZ Number: [P1,P2]', width=25)
        gfzlabel = Label(gfzframe, text='GFZ Number: ', width=25)
        gfzlabel.pack(side=LEFT)
        P1 = Radiobutton(gfzframe, text='P1', variable=GFZdef, value='P1')
        P2 = Radiobutton(gfzframe, text='P2', variable=GFZdef, value='P2')
        #self.gfz = Entry(gfzframe, width=25, textvariable=GFZdef)
        self.gfz = GFZdef
        P2.pack(side=RIGHT)
        P1.pack(side=RIGHT)
        
        # Read button
        readframe = Frame(padx=50, pady=10)
        readframe.pack()
        readlabel = Label(readframe, text='Read the config parameters', width=25)
        readlabel.pack(side=LEFT)
        self.resetusb = Button(readframe, text="RESET USB", command=self.ResetUSB)
        self.read = Button(readframe, text="READ", command=self.Read)
        #self.resetusb.pack(side=RIGHT) # does not work
        self.read.pack(side=RIGHT)

        # Run button
        runframe = Frame(padx=50, pady=10)
        runframe.pack()
        runlabel = Label(runframe, text='Run the sTGC Shorts Test', width=25)
        runlabel.pack(side=LEFT)
        self.run = Button(runframe, text="RUN", command=self.Run)
        self.run.pack(side=RIGHT)
        self.run.config(state=DISABLED)

        mapframe = Frame(padx=50, pady=10)
        mapframe.pack()
        maplabel = Label(mapframe,text='Display GFZ Mapping', width=25)
        maplabel.pack(side=LEFT)
        self.mapping = Button(mapframe, text='SHOW', command=self.Display)
        self.mapping.pack(side=RIGHT)
        self.mapping.config(state=DISABLED)

        channelframe = Frame(padx=50, pady=10)
        channelframe.pack()
        channellabel = Label(channelframe, text='Select Channel to Read and Locate:', width=25)
        channellabel.pack(side=LEFT)
        self.channel = Entry(channelframe, width=25)
        self.channel.pack(side=LEFT)
        self.channel.config(state=DISABLED)

        setbutton = Button(channelframe, text='Set', command=self.Set)
        setbutton.pack(side=RIGHT, padx=10)

        locateframe = Frame(padx=50, pady=10)
        locateframe.pack()
        locatelabel = Label(locateframe, text='Locate Channel', width=25)
        locatelabel.pack(side=LEFT)
        self.locate = Button(locateframe, text='LOCATE', command=self.Locate)
        self.locate.pack(side=RIGHT)
        self.locate.config(state=DISABLED)


        quitframe = Frame(padx=50, pady=10)
        quitframe.pack(side=BOTTOM)
        back = Button(quitframe, text="Back", command=self.frame2.quit)
        back.pack(side=LEFT)

        self.frame2.pack()

    def Read(self):
        # do it only once
        self.stgcval = str(self.stgc.get()).upper()
        self.uniqueval = str(self.unique.get()).upper()
        self.layerval = str(self.layer.get()).upper()
        self.ABval = str(self.AB.get()).upper()
        self.gfzval = str(self.gfz.get()).upper()
        self.PCval = str(self.PC.get()).upper()
        if self.PCval[0] == 'P':
            positioning = 'PIVOT'
        elif self.PCval[0] == 'C':
            positioning = 'CONFIRM'
        else:
            positioning = self.PCval

        # continue process
        self.frame2.quit()

        #print (getFoldersList (self.uniqueval, self.stgcval, (int)self.layerval, self.ABval, self.gfzval, '') )
 
        self.outputDir =  datetime.datetime.now().strftime("%b_%d_sTGC_"+self.stgcval+"_"+positioning+"-"+self.uniqueval+"_Layer"+self.layerval+"_"+self.ABval+"_GFZ"+self.gfzval)
        #print('OutputDir= %s ' %(self.outputDir))
        filenameRawOutput= '~/sTGC_Tester/Python/Results/'+self.outputDir+'/rawOutput.csv'
        if os.path.exists(filenameRawOutput) and os.path.getsize(filenameRawOutput) > 0:
            # Non empty file exists
            print('rawOutput= %s exists and has non-zero size.' %(filenameRawOutput))
            print('You can use this file by clicking "SORT" instead of "RUN"')
            #self.sort.config(state=NORMAL)

            filenameSorted= 'data/'+self.outputDir+'/database.csv'
            if os.path.exists(filenameSorted) and os.path.getsize(filenameSorted) > 0:
                # Non empty file exists
                print('Sorted= %s exists and has non-zero size.' %(filenameSorted))
                print('You can use this file by clicking "COMPARE" instead of "SORT"')
                self.compare.config(state=NORMAL)

                filenameGFZ= 'data/'+self.outputDir+'/sortedpulserdata.csv'
                if os.path.exists(filenameGFZ) and os.path.getsize(filenameGFZ) > 0:
                    # Non empty file exists
                    print('sortedpulserdata file= %s exists and has non-zero size.' %(filenameGFZ))
                    print('You can show the GZF map by clicking "SHOW"')
                    self.mapping.config(state=NORMAL)
                else:
                    # Non existent file
                    #print('GFZ= %s does not exist or has zero size.' %(filenameGFZ))
                    #print('You need to "RUN"')
                    self.mapping.config(state=DISABLED)
            else:
                # Non existent file
                print('Sorted= %s does not exist or has zero size.' %(filenameSorted))
                print('You need to "RUN"')
                self.compare.config(state=DISABLED)
        else:
            # Non existent file
            print('rawOutput= %s does not exist or has zero size.' %(filenameRawOutput))
            print('You need to "RUN"')
            #self.sort.config(state=DISABLED)
        self.run.config(state=NORMAL)
        self.channel.config(state=NORMAL)
        self.locate.config(state=NORMAL)


    def ResetUSB(self):
        n=0
        unbind = ['sudo', 'echo', '/sys/bus/usb/drivers/usb/1-5', '>', 'unbind']
        wait = ['sleep', '3']
        bind = ['sudo', 'echo', '/sys/bus/usb/drivers/usb/1-5', '>', 'bind']
        try:            
            subprocess.check_call(unbind)         
            subprocess.check_call(wait)         
            subprocess.check_call(bind)         
        except:
            n=1
        if n==0:
            print("reset usb successful")
        elif n==1:
            print("reset usb FAILED")


    def Run(self):
        try:            
            subprocess.check_call('echo','"test"')
            print("test print")
        except:
            n=1
            print("failed testprint")










#        n=0
#        pbc = ['sudo', 'python', 'pulserBoardControl.py', str(self.outputDir), str(self.stgcval), str(self.PCval), str(self.ABval), str(self.gfzval), str(self.layerval)]
#        try:            
#            subprocess.check_call(pbc)         
#        except:
#            n=1
#        if n==0:
            # Immediately run the Sort algorithm, without waiting for somebody to click the "OK" button on the GUI
#            self.sort.config(state=NORMAL)
#            self.Sort()
            #tkMessageBox.showinfo('Pulser Test Status', 'Pulser Test Complete') 
#        elif n==1:
#            messagebox.showinfo('Pulser Test Status', 'Failed To Run Pulser Test')

    def Sort(self):
        m=0
        cs = ['sudo', 'python', 'PSDVCsorting.py', str(self.outputDir), '0', str(self.stgcval), str(self.PCval), str(self.ABval), str(self.gfzval), str(self.layerval)]
        try:
            subprocess.check_call(cs)
        except:
            m=1
        if m ==0:
            tkMessageBox.showinfo('Sorting Status', 'Pulser Data Sorted')
            self.locate.config(state=NORMAL)
            self.mapping.config(state=NORMAL)
            self.channel.config(state=NORMAL)
            self.compare.config(state=NORMAL)
            self.Display()
        elif m == 1:
            tkMessageBox.showinfo('Sorting Status', 'Failed To Sort Pulser Data')
 
    def Compare(self):
        m=0
        comp = ['sudo', 'python', 'compareAmplitudeVsChannel.py', str(self.outputDir), '0', str(self.stgcval), str(self.PCval), str(self.ABval), str(self.gfzval), str(self.layerval)]
        try:
            subprocess.check_call(comp)
        except:
            m=1
        if m ==0:
            tkMessageBox.showinfo('Compare Status', 'Pulser Data Compared')
        elif m == 1:
            tkMessageBox.showinfo('Compare Status', 'Failed To Compare Pulser Data')
        
       
    def Display(self):
        scp = ['sudo', 'python', 'sortedchannelplot.py', 'data/'+str(self.outputDir), str(self.stgcval), str(self.PCval), str(self.ABval), str(self.gfzval), str(self.layerval)]
        try:
            subprocess.check_call(scp)
        except:
            m=1
            print('sortedchannelplot failed')

    def Locate(self):
        try:
            inchannel = self.channel.get()
            channelval = int(inchannel)   
            # Gerneralized mapping
            print('You selected channel %s in %s of the %sAB on layer %s of the %s-%s' %(channelval, self.gfzval, self.ABval, self.layerval, self.stgcval, self.PCval))
            QABmap.Qmap(self.layerval,self.ABval,self.gfzval,channelval, self.PCval, self.stgcval)
            bad = ['python', 'identifyBadChannels.py', str(self.outputDir), '0', str(self.stgcval), str(self.PCval), str(self.ABval), str(self.gfzval), str(self.layerval)]
            try:
                subprocess.check_call(bad)
            except:
                m=1
                print('identify bad channel failed')
    
            self.plot.config(state=NORMAL)
            #else:
            #    print("I'm sorry, There is no mapping function for the %s" %(stgcval))
        except:
            tkMessageBox.showinfo('Location Function', 'Please fill in the required information')

    def Set(self):
        self.arduino = setchan.connect()
        inset = str(self.channel.get())
        print("inset %s" %(inset))
        setchan.setChannel(inset, self.arduino)
        print('Channel Set to %s' %(inset))
       
    def PLOT(self):
        if self.stgcval == 'QS3':
            locator = 'Plots/layer%slocate.png' %(self.layerval)
            #print('locator= %s' %(locator) )
            plt = Image.open(locator)
            plt.show()
        elif self.stgcval == 'QL2':
            print('Locator plot for the %s not finalized' %(self.stgcval))

    def getSelected_map(self):
        selected_map = self.stgcval + "_" + self.PCval + "_" + self.uniqueval + "_LAYER" + self.layerval
        return selected_map

    def getSelected_board(self):
        selected_board = self.ABval + "_" + self.gfzval
        return selected_board
