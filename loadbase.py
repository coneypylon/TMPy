# this script loads an ODS file into a database for use by my implementation of CNR's ICTS/TMP

import pyexcel_odsr as ods, sys, sqlite3
from random import randint, choice
from tqdm import tqdm
from helpers import NewStation, NewCar, Train, getdattuple
from dispatch import runDay

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

# the script

if conf.upper()[0] != 'Y': # the user doesn't want to wipe the DB
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

# fetch the spreadsheet
data = ods.get_data(basebook)

# load stations
stationheader = data['Stations'][0]
rawstations = data['Stations'][1:]
stations = []
stationsqs = []

for station in rawstations:
    if station == []:
        break # end of file
    ts = NewStation(stationheader,station)
    stations.append(ts)
    stationsqs.append(ts.insertq())


for station in stationsqs:
    cur.execute(station)

conn.commit()

# load cars
carheader = data['Cars'][0]
rawcars = data['Cars'][1:]
cars = []
carsqs = []

for car in rawcars:
    ts = NewCar(carheader,car)
    cars.append(ts)
    carsqs.append(ts.getq())


for car in carsqs:
    cur.execute(car)

conn.commit()

# randomize if user asked us to
if randconf.upper()[0] != 'Y':
    exit()

# get date range
endd, endt = getdattuple()
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

allroute = [] # eventually needs to be some demand spreadsheet.

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
        trainday = startd + x
        runDay(trains,conn,cur,trainday,allroute)

conn.close() # seems a little superstitious to do this.