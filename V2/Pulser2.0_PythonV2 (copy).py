import csv
import serial
from datetime import datetime
import time
import os
import xlsxwriter
import sys
import pandas as pd
from easygui import choicebox, ccbox
import numpy as np
import math

# Window
from tkinter import *

from files.functions import Channel, mensaje, check, grounds, serial_ports, portIsUsable, escexcell, calculate_PCA_Voltage, calculate_ADC_code, calculate_RS_drop, correlated_pins, calculate_equivalent_resistance, NumberToPosition, NumberToPosition_QL3Par, Window2



#############################################################################
##########################-OPTIONS-##########################################
#Debug
debug = False

#Minimum short circuit resistance, only needed if use_resistance=True
SC_upper_res = 100000
use_resistance = False

#Thresholds
threshDCs = 220
threshDCi = 190

threshACs = 400
threshACi = 80

#Serial Communication
portName = ''
bps = 57600

#Print info to CSV
print_CSV = False



#Advanced options
debug2 = True
adc_voltage_ref = 1.1


# Window to select parameters
root = Tk()
window2 = Window2(root)

while(True):
    root.mainloop()

    # readout parameters
    selected_map_filename = window2.getSelected_map()
    selected_board = window2.getSelected_board()



    # cleanup selected map for use with .csv files
    selected_map = selected_map_filename[:3]+"P"+selected_map_filename[-1:]


    padStrip_choices = ["S_P1", "S_P2", "P_P1", "P_P2"]
    if selected_board == padStrip_choices[0]:
        not_in_map_str = 'NONE'
        df = pd.read_csv("files/P1_sTGC_AB_Mapping_strip.csv")
        df.drop('GFZ Connector', axis=1, inplace=True)
        df.set_index('GFZ_NAME', drop=True, inplace=True)
        df.fillna(not_in_map_str, inplace=True)
        if debug2:
            print(df.head())

        save_prefix = 'P1_Strip_'

    elif selected_board == padStrip_choices[1]:
        not_in_map_str = 'NONE'
        df = pd.read_csv("files/P2_sTGC_AB_Mapping_strip.csv")
        df.drop('GFZ Connector', axis=1, inplace=True)
        df.set_index('GFZ_NAME', drop=True, inplace=True)
        df.fillna(not_in_map_str, inplace=True)
        if debug2:
            print(df.head())
        save_prefix = 'P2_Strip_'

    elif selected_board == padStrip_choices[2]:
        not_in_map_str = 'NONE'
        df = pd.read_csv("files/sTGC_AB_Mapping_Pad.csv")
        df.set_index('GFZ_NAME', drop=True, inplace=True)
        df.fillna(not_in_map_str, inplace=True)
        if debug2:
            print(df.head())
        save_prefix = 'Pad_'
        # cleanup selected map for use with .csv files in case a pad is selected
        selected_map = selected_map_filename[:3]+selected_map_filename[4]+selected_map_filename[-1:]

    # TODO better design
    elif selected_board == padStrip_choices[3]:
        print("This does not exist, rerun programm")
        sys.exit(0)

    # show infos
    msg = 'The selected options are: ' + selected_board + ', ' + selected_map_filename + '.\n Do you want to continue?'
    title = 'Please Confirm'
    if ccbox(msg, title):     # show a Continue/Cancel dialog
        pass  # user chose Continue
    else:  # user chose Cancel
        sys.exit(0)


    if len(portName) < 3:
        ports = serial_ports()
        portName = choicebox('COM port not selected, please select the right port.', 'COM port Selector', ports)
        if debug:
            print(ports)

    ## Load connector information and mapping
    with open('files/Maping.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        numero = -1
        channels = []
        for row in csv_reader:
            if debug2:
                print(row)
            channels.append(Channel(row, ADC_ref=adc_voltage_ref))

    if debug:
        print('')
        print('GFZ to', selected_map,'Mapping')


    if "S" in selected_map :
        wedgeangle_deg=8.5
    elif "L" in selected_map :
        wedgeangle_deg=14

    WEDGEANGLE=wedgeangle_deg/360.*2*math.pi


    for channel in channels:
        name = df.loc[channel.gfz, selected_map]
        if name == not_in_map_str:
            channel.pad_map = name
        else:
            channel.pad_map = str(int(name))

            if "QL3" in selected_map and int(name)>170:
                channel.PARposition = NumberToPosition_QL3Par(selected_board, channel.pad_map)
            else:
                channel.position = NumberToPosition(WEDGEANGLE, selected_board, channel.pad_map)

        if debug:
            print(channel.gfz, '-->', channel.pad_map)







    AC_cal_val = []
    DC_cal_val = []
    estimated_source_V = 0

    ## Commands [Start,ID,Letter,Port,Number,Comand,Stop]
    ##Send
    ## [#,S,0,0,0,$] Start
    ## [#,W,2,0,1,$] Write Mult A Port 0 and Pin 1 a signal of 5V, read current and send it back
    ## [#,E,0,0,0,$] Read errors and send them back
    ## [#,P,I,0,0,$] Turn PWM ON
    ## [#,P,O,0,0,$] Turn PWM OFF

    ##Recive
    ## Turn on PWM
    ## [#,P,I,0,0,$] Turn PWM ON
    if portIsUsable(portName):
        print_CSV = True
        arduino = serial.Serial(portName, bps)
        print('')
        print('Arduino on port:', arduino.name)

        if debug:
            print('DEBUG MODE ON')

        if debug:
            print('')
            print('Checking multiplexers')
        arduino.timeout = 5
        time.sleep(2)
        ##Start comunication
        arduino.write('#'.encode('utf-8'))
        cond = True
        while cond:
            msj = arduino.readline()
            if len(msj) > 0:
                if mensaje(msj) == 1:
                    cond = False
                if debug:
                    print(msj.decode('utf-8'))



        # Start Voltage sensing Test
        if debug:
            print('Measuring PCA voltage')
        arduino.write(('#P'+'O'+'$').encode('utf-8'))   # Turn off PWM
        print((arduino.readline()).decode('utf-8'))
        time.sleep(0.4)
        for test in range(0,10):
            msj = '#W640$'
            arduino.write(msj.encode('utf-8'))
            msj = arduino.readline()
            msj = msj.decode('utf-8')
            DC_cal_val.append(int(msj.split(',')[4]))
            if debug:
                print(str(test) + ". DC test value", int(msj.split(',')[4]))


        estimated_source_V = calculate_PCA_Voltage(np.mean(DC_cal_val))
        if debug:
            print('Estimated PCA source voltage:', '{0:.3g}'.format(estimated_source_V) + 'V')
            print('')


        if use_resistance:
            threshDCs = calculate_ADC_code(SC_upper_res, V=estimated_source_V)
            threshDCi = calculate_RS_drop(10500, V=estimated_source_V)
            print('Modifying existing threshold to match max SC resistance:', SC_upper_res, 'Ohms')
            print('Lower DC thrshold:', threshDCi)
            print('Upper DC thrshold:', threshDCs)
            print('')





        ## Start AC Test
        print('AC test')
        arduino.write(('#P'+'I'+'$').encode('utf-8')) ## Turn on PWM
        print((arduino.readline()).decode('utf-8'))
        time.sleep(0.5)


        for test in range(0,10):
            msj = '#W640$'
            arduino.write(msj.encode('utf-8'))
            msj = arduino.readline()
            msj = msj.decode('utf-8')
            AC_cal_val.append(int(msj.split(',')[4]))
            if debug2:
                print(str(test) + ". AC test value", int(msj.split(',')[4]))
                print('')


        time.sleep(0.2)
        for channel in channels:
            if channel.mult >= 0:
                msj = '#W' + str(channel.mult) + str(channel.port) + str(channel.pin) + '$'
                arduino.write(msj.encode('utf-8'))
                msj = arduino.readline()
                msj = msj.decode('utf-8')
                channel.responseAC = msj
                channel.ADC_AC = int(msj.split(',')[4])
                check(channel.info2, msj)
                if debug:
                    print(channel.info+': ' + str(channel.ADC_AC))
                elif channel.pad_map != not_in_map_str:
                    print(channel.pad_map+': ' + str(channel.ADC_AC))


        # Start DC Test
        print('\n\n')
        print('DC test')
        arduino.write(('#P'+'O'+'$').encode('utf-8'))   # Turn off PWM
        print((arduino.readline()).decode('utf-8'))
        time.sleep(0.4)


        time.sleep(0.2)
        for channel in channels:
            if channel.mult >= 0:
                msj = '#W' + str(channel.mult) + str(channel.port) + str(channel.pin)+'$'
                arduino.write(msj.encode('utf-8'))
                msj = arduino.readline()
                msj = msj.decode('utf-8')
                channel.responseDC = msj
                channel.ADC_DC = int(msj.split(',')[4])
                check(channel.info2, msj)
                if debug:
                    print(channel.info+': '+str(channel.ADC_DC))
                elif channel.pad_map != not_in_map_str:
                    print(channel.pad_map + ': ' + str(channel.ADC_DC))

                channel.calculate_short_res(estimated_source_V)




        for channel in channels:
            if channel.mult >= 0:
                if channel.ADC_AC > threshACs:
                    channel.messages.append('Error in AC current (to High)')
                elif channel.ADC_AC > threshACi:
                    channel.connection = True
                else:
                    channel.messages.append('Error in AC current (to Low)')


                if channel.ADC_DC > threshDCs:
                    channel.cc = True
                    msj = '#E' + str(channel.mult) + str(channel.port) + str(channel.pin) + '$'
                    arduino.write(msj.encode('utf-8'))

                    cond = True
                    while cond:
                        msj = arduino.readline()
                        msj = msj.decode('utf-8')
                        msj = msj.split(',')
                        if msj[0] == 'R':
                            cond = False
                        else:
                            channel.errors.append([msj[1], msj[2], msj[3]])

                        if debug:
                            print(msj)

                    channel.messages.append('Error in DC current (to High)')

                elif channel.ADC_DC < threshDCi:
                    channel.messages.append('Error in DC current (to Low)')
        arduino.close()

    else:
        print("Couldn't open COM port, aborting...")

    if print_CSV:
        grounds(channels)

        # Excel setup
        outputDir = datetime.now().strftime("%b_%d_sTGC_"+selected_map_filename+"_"+selected_board)
        #print('OutputDir= %s ' %(self.outputDir))
        nombre= '~/sTGC_Tester/Python/Results/'+outputDir+'.xlsx'


        fecha = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        print('')
        print("Date and Time =", fecha)
        workbook = xlsxwriter.Workbook('Results/'+outputDir + '.xlsx')

        bueno = workbook.add_format()
        bueno.set_bg_color('green')
        bueno.set_align('center')
        bueno.set_border(1)

        malo = workbook.add_format()
        malo.set_bg_color('red')
        malo.set_align('center')
        malo.set_border(1)

        white = workbook.add_format()
        white.set_bg_color('white')
        white.set_border(1)
        white.set_align('center')




        prueba = workbook.add_worksheet('Test')
        prueba.write(0, 0, fecha)
        prueba.write(0, 3, 'NAME:')
        prueba.write(0, 4, selected_map)
        prueba.set_column(3, 4, 10)
        escexcell(['Mult', 'Port', 'Pin', 'ADC DC', 'Voltage DC', 'Current DC mA', 'ADC AC', 'Voltage AC', 'GFZ_Name', 'Name', 'Map Number', 'Messages'], 2, prueba, 0, white)
        prueba.write(0, 0, fecha)

        errores = workbook.add_worksheet('Errors')
        errores.write(0, 0, 'NAME:')
        errores.write(0, 1, selected_map)
        errores.write(1, 0, 'GFZ NAME:')
        errores.write(1, 1, 'GFZ CHANNEL:')
        errores.write(1, 2, 'PIN NAME:')
        errores.write(1, 3, 'POSITION:')
        errores.write(1, 4, 'PARPOSITION:')
        escexcell(['Name', 'Map Number'], 1, errores, 7, white)
        escexcell(['Name', 'Map Number'], 1, errores, 12, white)


        conectorDC = workbook.add_worksheet('ConnectorDC')
        conectorDC.set_column(0, 0, 20)
        conectorDC.write(0, 0, 'Upper DC Threshold:', white)
        conectorDC.write(0, 1, threshDCs, white)
        conectorDC.write(1, 0, 'Lower DC Threshold:', white)
        conectorDC.write(1, 1, threshDCi, white)
        conectorDC.write(2, 0, 'NAME:', white)
        conectorDC.write(2, 1, selected_map, white)
        conectorDC.set_column(3, 12, 12)


        conectorAC = workbook.add_worksheet('ConnectorAC')
        conectorAC.set_column(0, 0, 20)
        conectorAC.write(0, 0, 'Upper AC Threshold:', white)
        conectorAC.write(0, 1, threshACs,white)
        conectorAC.write(1, 0, 'Lower AC Threshold:', white)
        conectorAC.write(1, 1, threshACi, white)
        conectorAC.write(2, 0, 'NAME:', white)
        conectorAC.write(2, 1, selected_map, white)
        conectorAC.set_column(3, 12, 12)


        for channel in channels:
            if channel.connection:
                if channel.pad_map == not_in_map_str:
                    channel.AC_color_code = white
                else:
                    channel.AC_color_code = bueno
            else:
                channel.AC_color_code = malo

            if channel.cc:
                channel.DC_color_code = malo
                channel.color_code = malo
            else:
                if channel.pad_map == not_in_map_str:
                    channel.DC_color_code = white
                    channel.color_code = white
                else:
                    channel.DC_color_code = bueno
                    channel.color_code = bueno


        counter1 = 1
        counter2 = 1
        results_df = pd.DataFrame(columns=['pad_map', 'gfz', 'ADC_DC', 'voltageDC', 'SCR','ADC_AC', 'voltageAC'])
        for channel in channels:
            channel.update_VI()
            channel.update()

            if channel.mult >= 0:
                results_df.loc[channel.gfz, 'pad_map'] = channel.pad_map
                results_df.loc[channel.gfz, 'gfz'] = channel.gfz
                results_df.loc[channel.gfz, 'ADC_DC'] = channel.ADC_DC
                results_df.loc[channel.gfz, 'voltageDC'] = channel.voltageDC
                results_df.loc[channel.gfz, 'ADC_AC'] = channel.ADC_AC
                results_df.loc[channel.gfz, 'voltageAC'] = channel.voltageAC
                results_df.loc[channel.gfz, 'SCR'] = channel.short_resistance


            # AC window
            conectorAC.write(channel.x + 2, channel.y + 2, str(channel.gfzchannel) +': '+str(channel.ADC_AC), channel.AC_color_code)

            # Test window
            escexcell(channel.summary, counter1 + 2, prueba, 0, channel.color_code)

            # DC window
            conectorDC.write(channel.x + 2, channel.y + 2, str(channel.gfzchannel) + ': ' + str(channel.ADC_DC), channel.DC_color_code)
            if channel.cc:
                #Error window
                errores.write(counter2 + 2, 0, channel.gfz, channel.DC_color_code)
                errores.write(counter2 + 2, 1, channel.gfzchannel, channel.DC_color_code)
                errores.write(counter2 + 2, 2, channel.pad_map, channel.DC_color_code)
                errores.write(counter2 + 2, 3, channel.position, channel.DC_color_code)
                errores.write(counter2 + 2, 4, channel.PARposition, channel.DC_color_code)
                offset = 7
                for error in correlated_pins(channels, channel.errors):
                    escexcell(error, counter2 + 2, errores, offset, channel.color_code)
                    offset += 5
                counter2 += 1


            counter1 += 1






        workbook.close()
        if debug2:print("Loop done")


        # if debug:
        #     pd.set_option('display.max_rows', 500)
        #     print('')
        #     print(results_df)
        #     plt.scatter(results_df.SCR, results_df.ADC_AC)
        #     plt.show()









