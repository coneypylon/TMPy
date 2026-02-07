from random import randint
from datetime import datetime,UTC
import os, sqlite3

# helper function - makes a circular dependency if moved
def frontpad(num,spaces:int):
    if type(num) == str:
        tnum = num
        while len(tnum)<spaces:
            tnum = " " + tnum
    else:
        tnum = str(num)
        while len(tnum)<spaces:
            tnum = "0" + tnum
    return tnum

def backpad(num,spaces:int):
    if type(num) == str:
        tnum = num
        while len(tnum)<spaces:
            tnum += " "
    else:
        tnum = str(num)
        while len(tnum)<spaces:
            tnum += "0"
    return tnum

def getcars(loc,cur: sqlite3.Cursor):
    findq = "SELECT Initial, Number, LoadedOrEmpty, DestinationStation FROM LastLocationComplete WHERE StationNumber = %s;" % (loc)
    cur.execute(findq)
    results = cur.fetchall()
    outlst = []
    for result in results:
        outlst.append(FileCar(result[0],result[1],result[2],result[3]))
    return outlst

def getdattuple():
    now = datetime.now(UTC)
    formatted_time = now.strftime(r"%d%H%M")
    return (int(formatted_time[0:2]),int(formatted_time[2:4])) # probably there's another way to do this, but w/e

def cleantraces(cur: sqlite3.Cursor):
    getdelqs = "SELECT * FROM TracesToDelete;"
    cur.execute(getdelqs)
    results = cur.fetchall()
    for row in results:
        delq = "DELETE FROM Tracefile WHERE Initials = '%s' AND Number = %s AND Day = %s AND Time = %s;" % row
        cur.execute(delq)

def clear_screen():
    # Check the operating system name
    if os.name == 'nt':
        # For Windows
        _ = os.system('cls')
    else:
        # For Linux, macOS, and others ('posix' is the standard for non-Windows)
        _ = os.system('clear')

def lookuproads(selcode,curs):
    # if this ever becomes productionized, probably this should be an actual DB lookup. For now, it's hardcoded.
    if selcode == '1': # CN
        return "LIKE 'CN%'"
    elif selcode == '2': # CGTX
        return "= 'CGTX'"
    elif selcode == '3': # CP
        return "= 'CP'"
    elif selcode == '4': # UTLX
        return "= 'UTLX'"
    elif selcode == '8': # Other Foreign
        return "NOT IN ('CGTX','CP','UTLX') AND NOT LIKE 'CN%'"
    elif selcode == '9': # All Foreign
        return "NOT LIKE 'CN%'" # probably could be strict equality, but I'm not sure how GTW/CVR is handled.
    else:
        raise Exception

# helper classes.
class consist:
    def cardformat(self,journal:int=000000):
        self.infoslug = self.registration + self.condition + self.type
        if journal == 000000:
            journal = '      '
        self.locslug = self.destination + self.block + self.zone + str(self.onlinedest) + self.delto + str(self.onlineorig) + self.recfrom
        self.contentslug = str(self.commodity) + "   " + self.consignee + self.contents + str(self.tare) + str(self.tonnage)
        return "G%s%s%s%s " % (self.infoslug,self.locslug,self.contentslug,str(self.billnum) + str(journal))
    def genFileCar(self):
        if self.isloaded:
            lore = 'L'
        else:
            lore = 'E'
        return FileCar(backpad(self.railroad,4),self.number,lore,self.onlinedest)

class Car(consist):
    def __init__(self,initial: str, number: int, curs: sqlite3.Cursor):
        getcarq = "SELECT Grade, Type, FinalDestination, DestinationStation, OffGoingJunction, OriginStation, OnComingJunction, CommodityCode, Consignee, Contents, Tare, Tonnage, Waybill FROM CarControlfile WHERE initial='%s' AND number=%s;" % (backpad(initial,4),number)
        curs.execute(getcarq)

        results = curs.fetchall()

        if len(results) > 1:
            raise Exception("Ambiguous number of results for car %s" % number)
        elif len(results) == 1: # what we expect
            result = results[0]
            self.railroad = backpad(initial,4)
            self.number = number
            self.registration = self.railroad + str(number)
            self.condition, self.type, self.destination, self.onlinedest, self.delto, self.onlineorig, self.recfrom, self.commodity, self.consignee, self.contents, self.tare, self.tonnage, self.billnum = result
            if self.destination == None: # probably this should be done by the query or by the output. definitely should raise errors if you try to add a car to a train when the car has no orders to go somewhere.
                self.destination = '       '
            if self.onlinedest == None:
                self.onlinedest = '     '
            if self.delto == None:
                self.delto = ' '
            if self.onlineorig == None:
                self.onlineorig = '      '
            if self.recfrom == None:
                self.recfrom = ' '
            if self.tonnage == None:
                self.tonnage = 0
            if self.commodity == None:
                self.commodity = '         '
            if self.consignee == None:
                self.consignee = '         '
            if self.contents == None:
                self.contents = '       '
            if self.billnum == None:
                self.billnum = '      '
            self.block = '  '
            self.zone = '  '
            if int(self.tonnage) > 0:
                self.isloaded = True
            else:
                self.isloaded = False
        else:
            raise KeyError("No car with number %s found!" % number)

class carcard(consist):
    def __init__(self,initials: str,number: int,condition: str,type: str,destination: int,block,onlinedest: int,onlineorig: int,taretons: int,zone='  ',delto=' ',recfrom=' ',commoditycode='          ',consignee='          ',contents='      ',nettons=0,waybillnum='      '):
        self.railroad = initials
        self.number = number
        self.registration = initials + number
        self.condition = condition
        self.type = type
        self.infoslug = self.registration + condition + type
        try:
            self.destination = destination[:8].upper()
        except:
            self.destination = backpad(destination,8).upper()
        self.block = block
        self.zone = zone
        self.onlinedest = onlinedest
        self.delto = delto
        self.onlineorig = onlineorig
        self.recfrom = recfrom
        self.locslug = destination + block + zone + onlinedest + delto + onlineorig + recfrom
        self.commodity = commoditycode
        self.consignee = consignee
        self.contents = contents
        self.tare = taretons
        self.tonnage = nettons
        if int(self.tonnage) > 0:
            self.isloaded = True
        else:
            self.isloaded = False
        self.contentslug = commoditycode + "   " + consignee + contents + taretons + nettons
        self.billnum = waybillnum
    

class trailercard(consist):
    def __init__(self,initials,number,condition,type,carryingcar,trailerOwner,nettons):
        self.railroad = initials
        self.number = number
        self.registration = initials + number
        self.condition = condition
        self.type = type
        self.infoslug = self.registration + condition + type
        self.destination = carryingcar + "  "
        self.destblock = "  "
        self.destzone = "  "
        self.onlinedest = "     "
        self.delto = " "
        self.onlineorig = "     "
        self.recfrom = " "
        self.locslug = self.destination + self.destblock + self.destzone + self.onlinedest + self.delto + self.onlineorig + self.recfrom
        self.commodity = "          "
        self.consignee = trailerOwner
        self.contents = "      "
        self.tare = "05"
        self.tonnage = nettons
        self.contentslug = self.commodity + self.consignee + self.contents + self.tare + nettons
        self.billnum = "-     "

class trainjournal:
    def __init__(self, trainNumber: int, stationFrom: Station, stationTo: Station, cars: list[Car], orderTime: int, departureTimeStamp: str,leadcode: int,callletters: str,number=0,open=True):
        self.trainNumber=trainNumber
        self.fr = stationFrom
        self.to = stationTo
        if number == 0:
            self.number = str(randint(10000,99999)) # eventually a select from a DB
        else:
            self.number = str(number)
        self.carconsist = cars
        self.loads = 0
        self.empties = 0
        self.tonnage = 0
        for car in self.carconsist:
            if car.isloaded:
                self.loads += 1
            else:
                self.empties += 1
            self.tonnage += int(car.tonnage)
        self.orderTime = orderTime
        self.departure = departureTimeStamp # presumption is that the train is departing AND being created
        self.units = [] # presumption is that the train is departing AND being created. Weirdly, the manual doesn't prescribe assigning units other than the lead
        self.lead = leadcode
        self.callletters = callletters # no idea how to generate
        self.open = open
        self.exceptions = dict()
    def cardformat(self,type):
        cardstack = []
        if type == 'D':
            selector = "#somekindofcodeshre*                                                            "
            addresses = "H Some kind of address goes here but I have no idea what it be  *               "
            departure = "D%s%s%s    %s%s%s                   %s%s %s    -%s %s " % (self.trainNumber,self.fr.number,self.to.number,frontpad(self.loads,3),frontpad(self.empties,3),self.orderTime,self.departure,frontpad(self.tonnage,5),self.lead,self.callletters,self.number)
            carlst = []
            for x in self.carconsist:
                carlst.append(x.cardformat(self.number))
            exceptlst = []
            usedkeys = []
            for x in self.exceptions.values():
                exceptlst.extend(x)
            endoftrain = "H End of Train@@@@@@@@@@*                                                       "
            endoftransmission = "P END OF TRANSMISSION%%@@@@@@@@@@#SelectionCodesGoHereForMyOffice*              "
            cardstack = [selector,addresses,departure]
            cardstack.extend(carlst)
            cardstack.extend(exceptlst)
            cardstack.append(endoftrain)
            cardstack.append(endoftransmission)
        return cardstack
    def write(self,filename,type):
        cardstack = self.cardformat(type)
        with open(filename,"w") as f:
            for card in cardstack:
                f.write(f"{card}\n")
    def addexception(self,exception,format="text"):
        if format == "text":
            if exception[1] != ' ': # it's for a car
                key = exception[1:11]
            else: # eventually we probably want to have these, but they seem superfluous to my initial view.
                return
                #key = exception[2:14]
            if key not in self.exceptions.keys():
                self.exceptions[key] = [exception]
            else:
                self.exceptions[key].append(exception)
    def __str__(self):
        if self.open:
            ostatus = "OPEN"
        else:
            ostatus = "CLOSED"
        return "[%s] Journal %s for train %s from %s to %s with %s loads and %s empties." % (ostatus,self.number,self.trainNumber,self.fr.name,self.to.name,self.loads,self.empties)

class Station:
    def __init__(self, number: int, curs: sqlite3.Cursor):
        getstatq = "SELECT * FROM stations WHERE number=%s;" % number
        curs.execute(getstatq)

        results = curs.fetchall()

        if len(results) > 1:
            raise Exception("Ambiguous number of results for station %s" % number)
        elif len(results) == 1: # what we expect
            result = results[0]
            self.number = result[0]
            self.code = result[1]
            self.interrwy = result[2]
            self.name = result[3]
            self.railway = result[4]
            self.interstat = result[5]
        else:
            raise KeyError("No station with number %s found!" % number)
    def insertq(self):
        insq = "INSERT INTO stations VALUES (%s,'%s','%s','%s','%s',%s);" % (self.number,self.code,self.interrrwy,self.name,self.railway,self.interstat)
        return insq


class NewStation(Station):
    def __init__(self, header: list, data: list):
        order = ["number", "code", "interchangedrailway", "name", "railway", "interchange"]
        values = []
        for col in order:
            for x in range(0,len(header)):
                if header[x] == col:
                    values.append(data[x])
                    break
        self.number, self.code, self.interrrwy, self.name, self.railway, self.interstat = values

class NewCar:
    def __init__(self, header: list, data: list):
        order = ["Initial","Number","Type","Grade","Tare"]
        values = []
        for col in order:
            for x in range(0,len(header)):
                if header[x] == col:
                    values.append(data[x])
                    break
        self.Initial, self.Number,self.Type,self.Grade, self.Tare = values
    def getq(self):
        insq = "INSERT INTO Carfile(Initial, Number, Type, Grade, Tare) VALUES ('%s',%s,'%s','%s',%s);" % (backpad(self.Initial,4), self.Number,self.Type,self.Grade, self.Tare)
        return insq


    
class FileCar:
    def __init__(self,initial,number,lore,curdest=0,tare=22,grade='A'):
        self.number = number
        self.initial = initial
        self.lore = lore
        self.curdest = curdest
        self.Tare = tare
        self.Grade = grade
    def removewaybill(self,cur): # someday this should be date sensitive
        delq = "DELETE FROM Waybillfile WHERE Initial = '%s' AND Number = %s;" % (self.initial, self.number)
        cur.execute(delq)
        self.curdest = 0
    def genwaybill(self,consign,start,end,cargo,day,time,comcode,cur):
        tonnage = randint(1,20)
        wayq = "INSERT INTO Waybillfile (Initial, Number, Consignee, Contents, Destination, OriginStation, Day, Time, Tonnage, CommodityCode) VALUES ('%s',%s,'%s','%s',%s,%s,%s,%s,%s,%s);" % \
                (self.initial,self.number,consign,cargo,start,end,day,time, tonnage,comcode)
        cur.execute(wayq)
        self.curdest = end
    def gentrace(self,aord,loc,day,time,trnum,lore,cur): # we will want to delete old traces at some point
        traceq = "INSERT INTO Tracefile VALUES ('%s',%s,'%s',%s,%s,%s,%s,'%s');" % (self.initial,self.number,aord,loc,day,time,trnum,lore)
        try:
            cur.execute(traceq)
            self.lore = lore
        except sqlite3.IntegrityError: # we looped around months and had a problem
            pass
    def addtofile(self,curs):
        insq = "INSERT INTO Carfile(Initial, Number, Type, Grade, Tare) VALUES ('%s',%s,'%s','%s',%s);" % (backpad(self.Initial,4), self.Number,self.Type,self.Grade, self.Tare)
        curs.execute(insq)


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