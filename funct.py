import csv
import serial

class cscs:
# init function added purely out of necessity
    def __init__(self):
        None

# function that formats and exports data to the .csv
    def dataOut(self,allData):
        with open('motorData.csv', 'w', newline='') as csvw:
            writer = csv.writer(csvw, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Motor Config'])
            for i in range(0,5):
                if i != None:
                    writer.writerow([allData[i]])

# reads data from .csv file and returns as array
    def readData(self):
        out = []
        with open('motorData.csv') as r:
            data = list(csv.reader(r))
            for i in range(1,len(data)):
                stri = None
                try:
                    float(data[i][0])
                except:
                    stri = True
                if stri == True:
                    out.append(data[i][0])
                else:
                    out.append(float(data[i][0]))
            return out

    async def blink(self):
        print('d')
        #time.sleep(6)
