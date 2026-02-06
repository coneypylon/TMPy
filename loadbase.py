# this script loads an ODS file into a database for use by my implementation of CNR's ICTS/TMP

import pyexcel_odsr as ods, sys, sqlite3
from datetime import datetime,UTC
from random import randint, choice


def pad(num,spaces):
    if type(num) == str:
        tnum = num
        while len(tnum)<spaces:
            tnum += " "
    else:
        tnum = str(num)
        while len(tnum)<spaces:
            tnum = "0" + tnum
    return tnum

# variables/constants
basebook = sys.argv[1]
db = "db.sqlite3"
schema = "db.sqlite3-Schema.sql"

# confirmations
conf = input("This will wipe out %s. Continue? " % db)
randconf = input("Randomize car locations once loaded? ")

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

# helper functions
def timestmp():
    now = datetime.now(UTC)
    formatted_time = now.strftime(r"%d%H%M")
    return (int(formatted_time[0:2]),int(formatted_time[2:4])) # probably there's another way to do this, but w/e

# the script

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

# randomize if user asked us to
if randconf.upper()[0] != 'Y':
    exit()

# get date range
endd, endt = timestmp()
startd = endd - 5 # 5 days seems about right

# get stations
statq = "SELECT number FROM stations;"
cur.execute(statq)
rawstats = cur.fetchall()

# get cars
carq = "SELECT Initial, Number FROM Carfile;"
cur.execute(carq)
rawcars = cur.fetchall()

# variables & constants
traces = []
ad = ('A','D')
le = ('L','E')
trains = (401,405,402,406,225,226) # these will have to be localized later. Right now I need a lot of data.

for car in rawcars:
    num2do = randint(1,4)
    for x in range(0,num2do):
        newstat = choice(rawstats)[0]
        aord = choice(ad)
        lore = choice(le)
        day = randint(startd,endd)
        trn = choice(trains)
        if day == endd:
            tim = randint(0,endt)
        else:
            tim = randint(0,2400)
        value = "('%s',%s,'%s',%s,%s,%s,%s,'%s')" % (car[0],car[1],aord,newstat,day,tim,trn,lore)
        traces.append(value)

traceq = "INSERT INTO Tracefile VALUES "

for x in traces:
    try:
        tq = traceq + x + ";"
        cur.execute(tq)
    except sqlite3.IntegrityError: # we accidentally a duplicate
        pass

conn.commit()