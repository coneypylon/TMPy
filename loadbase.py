# this script loads an ODS file into a database for use by my implementation of CNR's ICTS/TMP

import pyexcel_odsr as ods, sys, sqlite3
from main import pad

# variables/constants
basebook = sys.argv[1]
db = "db.sqlite3"
schema = "db.sqlite3-Schema.sql"

# helper classes. Maybe move these elsewhere someday. Could probably be refactored.
class Station:
    def __init__(self, header, data):
        order = ["number", "code", "interchangedrailway", "name", "railway", "interchange"]
        values = []
        for col in order:
            for x in range(0,len(header)):
                if header[x] == col:
                    values.append(data[x])
                    break
        self.number, self.code, self.interrrwy, self.name, self.railway, self.interstat = values
    def getq(self):
        insq = "INSERT INTO stations VALUES (%s,'%s','%s','%s','%s',%s);" % (self.number,self.code,self.interrrwy,self.name,self.railway,self.interstat)
        return insq

class Car:
    def __init__(self, header, data):
        order = ["Initial","Number","Type","Grade"]
        values = []
        for col in order:
            for x in range(0,len(header)):
                if header[x] == col:
                    values.append(data[x])
                    break
        self.Initial, self.Number,self.Type,self.Grade = values
    def getq(self):
        insq = "INSERT INTO Carfile VALUES ('%s',%s,'%s','%s');" % (pad(self.Initial,4), self.Number,self.Type,self.Grade)
        return insq

conf = input("This will wipe out %s. Continue? " % db)
if conf.upper()[0] != 'Y':
    exit()
else:
    with open(db,'w') as f:
        f.write('')

conn = sqlite3.connect(db)
cur = conn.cursor()

with open(schema,"r") as f:
    q = f.read()

cur.executescript(q) # set up the DB
conn.commit() # write it

data = ods.get_data(basebook)

# load stations
stationheader = data['Stations'][0]
rawstations = data['Stations'][1:]
stations = []
stationsqs = []

for station in rawstations:
    ts = Station(stationheader,station)
    stations.append(ts)
    stationsqs.append(ts.getq())


for station in stationsqs:
    cur.execute(station)

conn.commit()

# load cars
carheader = data['Cars'][0]
rawcars = data['Cars'][1:]
cars = []
carsqs = []

for car in rawcars:
    ts = Car(carheader,car)
    cars.append(ts)
    carsqs.append(ts.getq())


for car in carsqs:
    cur.execute(car)

conn.commit()
