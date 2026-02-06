# this script loads an ODS file into a database for use by my implementation of CNR's ICTS/TMP

import pyexcel_odsr as ods, sys, sqlite3
from datetime import datetime,UTC
from random import randint, choice
from tqdm import tqdm


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
if randconf.upper()[0] == 'Y':
    routeconf = input("Route the cars on trains after loaded? ")
    if routeconf.upper()[0] == 'Y':
        routeconf = True
        routenum = int(input("How many iterations of routing? "))
    else:
        routenum = 0

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
    
class FileCar:
    def __init__(self,initial,number,lore,curdest):
        self.number = number
        self.initial = initial
        self.lore = lore
        self.curdest = curdest
    def removewaybill(self,cur): # someday this should be date sensitive
        delq = "DELETE FROM Waybillfile WHERE Initial = '%s' AND Number = %s;" % (self.initial, self.number)
        cur.execute(delq)
        self.curdest = 0
    def genwaybill(self,consign,start,end,cargo,day,time,cur):
        wayq = "INSERT INTO Waybillfile (Initial, Number, Consignee, Contents, Destination, OriginStation, Day, Time) VALUES ('%s',%s,'%s','%s',%s,%s,%s,%s);" % \
                (self.initial,self.number,consign,cargo,start,end,day,time)
        cur.execute(wayq)
        self.curdest = end
    def gentrace(self,aord,loc,day,time,trnum,lore,cur): # we will want to delete old traces at some point
        traceq = "INSERT INTO Tracefile VALUES ('%s',%s,'%s',%s,%s,%s,%s,'%s');" % (self.initial,self.number,aord,loc,day,time,trnum,lore)
        try:
            cur.execute(traceq)
            self.lore = lore
        except sqlite3.IntegrityError: # we looped around months and had a problem
            pass


class Train:
    def __init__(self, number, route):
        self.curpos = randint(0,len(route) - 1)
        self.route = route
        self.number = number
    def move(self):
        if self.curpos == len(self.route) -1:
            self.curpos = 0
            return 0
        else:
            self.curpos += 1
            return self.route[self.curpos]
    def location(self):
        return self.route[self.curpos]

# helper functions
def cleantraces(cur):
    getdelqs = "SELECT * FROM TracesToDelete;"
    cur.execute(getdelqs)
    results = cur.fetchall()
    for row in results:
        delq = "DELETE FROM Tracefile WHERE Initials = '%s' AND Number = %s AND Day = %s AND Time = %s;" % row
        cur.execute(delq)


def getcars(loc,cur):
    findq = "SELECT Initial, Number, LoadedOrEmpty, DestinationStation FROM LastLocationComplete WHERE StationNumber = %s;" % (loc)
    cur.execute(findq)
    results = cur.fetchall()
    outlst = []
    for result in results:
        outlst.append(FileCar(result[0],result[1],result[2],result[3]))
    return outlst


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
    if station == []:
        break # end of file
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
startd = endd - 5 - routenum # 15 days seems about right

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
    newstat = choice(rawstats)[0]
    aord = choice(ad)
    lore = choice(le)
    day = randint(startd,endd-routenum)
    while day < 1:
        day += 30
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

allroute = []

if routeconf:
    startd = endd - routenum
    trains = []
    rawtrains = data["Trains"][1:]
    for train in rawtrains:
        route = train[1].split(',')
        allroute.extend(route)
        num = int(train[0])
        trains.append(Train(num,route))
    for x in tqdm(range(0,routenum)):
        for train in trains:
            loc = train.location()
            cars = getcars(loc,cur) # returns FileCars
            result = train.move()
            if result != 0:
                traintime = randint(0,2400)
                trainday = startd + x
                while trainday < 1:
                    trainday += 30
                for car in cars:
                    if result == car.curdest:
                        lore = 'E'
                        car.gentrace('A',result,trainday,leavet + 198, train.number, lore,cur)
                    elif randint(0,10) > 8: # 10% chance to generate a new waybill. The examples in the manual show nonsensical waybilling as well.
                        car.removewaybill(cur) # not necessary later
                        lore = 'L'
                        leavet = randint(0,2200)
                        car.genwaybill("SMONE, LLC",loc,choice(allroute),"SOMCGO",trainday-1,leavet,cur) # not clever date
                        car.gentrace('D',loc,trainday - 1,leavet + 198, train.number, lore,cur)
                        car.gentrace('A',result,trainday,traintime, train.number, lore,cur)
                    elif randint(0,10) > 5: # should be a 40% chance
                        car.gentrace('A',result,trainday,traintime, train.number,car.lore,cur)
        cleantraces(cur)
        conn.commit()
