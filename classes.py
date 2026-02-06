from random import randint
import sqlite3

# helper function - makes a circular dependency if moved
def backpad(num,spaces):
    if type(num) == str:
        tnum = num
        while len(tnum)<spaces:
            tnum += " "
    else:
        tnum = str(num)
        while len(tnum)<spaces:
            tnum += "0"
    return tnum

# helper classes.
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
        insq = "INSERT INTO Carfile VALUES ('%s',%s,'%s','%s');" % (backpad(self.Initial,4), self.Number,self.Type,self.Grade)
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