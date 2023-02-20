from typing import Dict
import PySimpleGUI as sg
import serial
import serial.tools.list_ports
import csv
import time
import webbrowser
import os.path
from funct import cscs

print('Starting up CSCS GUI Version 0.7.5\n')

# allData contains name, current limit, direction, position counter, microstepping mode
allData = [None,None,None,0,None]

# create list of available com ports
ports = []
ports = list(serial.tools.list_ports.comports())

# set theme and layout etc.
sg.theme('SystemDefault1')

tabLayout1 = [
    [sg.Text('Please press "Initialize"',key='-NEW-')],

    [sg.Button('Initialize',tooltip='Use to update GUI and/or to detect errors.')],
    [sg.Button('Shutdown',tooltip='Shuts down the GUI.')],
    [sg.Text('Select COM Port:'),sg.Combo(ports,key='-B-',size=(16,3))]
]

tabLayout2 = [
    [sg.Button('Config',tooltip='Input the motor name and current limit')], 
    [sg.Text('Motor Name:'),sg.Text(key='-NAME0-')],
    [sg.Text('Motor Current Limit (mA):'),sg.Text(key='-CURR0-')],
    [sg.Button('Forward',tooltip='Enables forward stepping'),
     sg.Button('Backward',tooltip='Enables backward stepping'),
     sg.Text('Current Direction:'),sg.Text('Forward',key='-M1D-')],
    [sg.Text('Input Number of Steps'),sg.Input(size=(8,1),default_text=0,key='-ST-')],
    [sg.Text('Position:'),sg.Text(allData[3],key='-P-')],
    [sg.Text('Micro-step Mode'),sg.Combo(['1','1/2','1/4','1/8'],default_value=1,key='-MC-'),
     sg.Button('Confirm',tooltip='Updates program with entered micro-step value.')],

    [sg.Text('')],

    [sg.Button('Enable',tooltip='Enable the motor'),
     #sg.Button('Disable',tooltip='Disable the selected motor'),
     sg.Button('Reset Motor',tooltip='Return motor to original position')]
]

layout = [
    [sg.Text(size=(8,1)),sg.Button(image_filename='Graphics\cscs.png',image_size=(160,85),key='-LO-')],
    [sg.Text('Driver Control Menu',font=11,background_color='#B5B4B4')],
    [sg.TabGroup([[sg.Tab('Tab 1', tabLayout1), sg.Tab('Tab 2', tabLayout2)]])]
]

errorM = [
    [sg.Text('Error')]
]

# create the window
window1 = sg.Window('CSCS Device Control Menu',layout,resizable=True)

# variables used in event loop
newState = None
sel = None
k = 0
on = 1
i = 0
j = 1
initPin = 1
errorPin = 0
flag = 1

# dictionary pairing microstep ratios with numeric representation
fd: dict[str, float] = {
    '1': 1,
    '1/2': 2,
    '1/4': 4,
    '1/8': 8
}
# reverse lookup
df: dict[float, str] = {
    1: '1',
    2:'1/2',
    4:'1/4',
    8:'1/8'
}

# checks if the .csv exists. if it does, imports. if not, creates file.
if os.path.exists('motorData.csv') == True:
    newState = 0
    print('motorData.csv exists! Importing data...\n')
    allData = cscs.readData(None)
    print(allData)
else:
    newState = 1
    print('motorData.csv does not exist. Creating file.\n')
    open('motorData.csv','x')

# create an event loop
while True:
    # also receive values from the device
    # detect motor data from device to set newstate to 1, detect faults
    event,values = window1.Read()

    if newState == 1:
        if flag == 1:
            window1['-NEW-'].update('No configuration detected! Please configure the motor on Tab 2.')
            allData[4] = fd[values['-MC-']]
            allData[2] = 0
    else:
        if flag == 1:
            window1['-NEW-'].update('Existing configuration detected.')
            window1['-NAME0-'].update(allData[0])
            window1['-CURR0-'].update(allData[1])
            if(allData[2] == 0):
                window1['-M1D-'].update('Forward')
            if(allData[2] == 1):
                window1['-M1D-'].update('Backward')
            window1['-MC-'].update(df[allData[4]])
            flag = 0

    if event == 'Initialize': # skips one loop forward so new motor message displays
        print('Program initialized. Event loop skipped forward.\n')
        window1['-P-'].update(allData[3])
        continue

    if event == 'Refresh': # ensures that displayed values are up to date
        allData[4] = fd[values['-MC-']]
        continue

    if event == 'Test': # function outputs values pulled from GUI for debugging purposes
        print(values)

    if event == 'Forward': # sets direction parameter to 0
        allData[2] = 0
        window1['-M1D-'].update('Forward')

    if event == 'Backward': # sets direction parameter to 1
        allData[2] = 1
        window1['-M1D-'].update('Backward')

    if event == 'Enable': # send parameters to device to begin operation
        comP = str(values['-B-'])[0:4]
        print(comP)
        cscs.dataOut(None, allData)

        # create error exception if selected com port doesn't work
        try:
            ser = serial.Serial(comP)
            ser.close()
        except:
            print('COM port not available.\n')
            sg.popup('COM port not available.')
            continue

        # check if any parameters are missing
        for par in allData:
            if par == None:
                sg.popup('Error. Motor parameter missing.')
                print('Error. Motor parameter missing.\n')
                continue

        ser = serial.Serial(comP,9600,timeout=2)  # open serial port
        time.sleep(2)
        cur = 'Z' + str(allData[1])  # append current value to current id bit
        print(cur)
        ser.write(cur.encode())
        time.sleep(2)
        ser.write(b'E') # send error checking bit
        time.sleep(1)
        er = ser.read(size=10) # receive error byte
        print(er.decode())
        if er == 'e':
            print('Fault detected in device. Ceasing operation. Please manually check for and clear faults.\n')
            sg.popup('Fault detected in device. Ceasing operation. Please manually check for and clear faults.\n')
            continue
        else:
            print('No errors detected.\n')
        time.sleep(2)
        micro = 'M' + str(allData[4]) # append microstepping mode to micro id bit
        print(micro)
        ser.write(micro.encode())
        time.sleep(2)

        # determine whether to send forward or backward bit
        if allData[2] == 0: # forward
            fwd = 'F'+values['-ST-'] # package forward bit with no. of steps
            print(fwd)
            ser.write(fwd.encode())
        if allData[2] == 1: # backward
            rvs = 'R'+values['-ST-'] # package forward bit with no. of steps
            print(rvs)
            ser.write(rvs.encode())
        time.sleep(2)
        ser.close() # closes serial por
        # update microstep mode
        allData[4] = fd[values['-MC-']]
        # update position tracker
        if allData[2] == 0:
            allData[3] += (1 / float(allData[4])) * float(values['-ST-'])
        else:
            allData[3] -= (1 / float(allData[4])) * float(values['-ST-'])
        print('Position:', allData[3], '\n')
        window1['-P-'].update(allData[3])
        window1.Refresh()

    if event == 'Reset Motor': # returns motor to original position
        res = ''
        cmP = str(values['-B-'])[0:4]
        print(cmP)
        # create error exception if selected com port doesn't work
        try:
            ser = serial.Serial(cmP)
            ser.close()
        except:
            print('COM port not available.\n')
            sg.popup('COM port not available.')
            continue
        
        cmp = str(values['-B-'])[0:4]
        print('Go home\n')
        print(allData[3])
        ser = serial.Serial(cmp,9600,timeout=2)  # open serial port
        time.sleep(2)
        cur = 'Z' + str(allData[1])  # append current value to current id bit
        print(cur)
        ser.write(cur.encode())
        time.sleep(2)
        if float(allData[3]) > 0:
            res = 'H' + str(allData[3])
            print(res)
            print('\nGoing in reverse')
            ser.write(res.encode())

        if float(allData[3]) < 0:
            res = 'O' + str(abs(allData[3]))
            print(res)
            print('\nGoing forward')
            ser.write(res.encode())

        time.sleep(2)
        allData[3] -= allData[3]
        ser.close()
        window1['-P-'].update(allData[3])
        window1.Refresh()

    if event == sg.WIN_CLOSED: # window closed
        print('Closing program, ceasing operation')
        cscs.dataOut(None,allData)
        break

    if event == 'Shutdown': # shuts down program
        print('Closing program, ceasing operation')
        cscs.dataOut(None,allData)
        break

    if event == 'Config': # opens popups for input of name and current limit
        allData[0] = sg.popup_get_text(
            'Enter a motor name.', location=(1000, 200))
        allData[1] = sg.popup_get_text(
            'Enter motor current limit (mA).', location = (1000, 200))
        if allData[1] != None:
            while(allData[1].isnumeric() == False):
                allData[1] = sg.popup_get_text(
                    'Please enter a numeric current limit.', location=(1000, 200))
            while(int(allData[1]) >= 2000):
                allData[1] = sg.popup_get_text(
                    'Please enter a current limit under 2000 mA or 2 A.', location=(1000, 200))

        window1['-NEW-'].update('Existing configuration detected.')

        # update GUI layout
        window1['-NAME0-'].update(allData[0])
        window1['-CURR0-'].update(allData[1])
        #print(allData[i][0],allData[i][1])

        cscs.dataOut(None,allData)
    if event == '-LO-': # opens link to project webpage
        webbrowser.open('https://sites.google.com/view/cscontroller/home')
window1.close()
#ser.close()
