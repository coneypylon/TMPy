'''Utilities for making card decks.
Possibly actually useful someday.

Loosely corresponds to CN Car Control from ~1967
'''

from random import randint

def pad(num,spaces):
    tnum = str(num)
    while len(tnum)<spaces:
        tnum = "0" + tnum
    return tnum

class consist:
    def __str__(self):
        return "G%s%s%s%s " % (self.infoslug,self.locslug,self.contentslug,self.journalslug)
    

class car(consist):
    def __init__(self,initials,number,condition,type,destination,block,zone,onlinedest,delto,onlineorig,recfrom,commoditycode,consignee,contents,taretons,nettons,waybillnum,journalnum):
        self.railroad = initials
        self.number = number
        self.registration = initials + number
        self.condition = condition
        self.type = type
        self.infoslug = self.registration + condition + type
        self.destination = destination
        self.destblock = block
        self.destzone = zone
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
        self.journalvers = journalnum
        self.journalslug = waybillnum + journalnum

class trailer(consist):
    def __init__(self,initials,number,condition,type,carryingcar,trailerOwner,nettons,journalnum):
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
        self.journalvers = journalnum # this is supposed to be some global magic number
        self.journalslug = self.billnum + journalnum

class trainjournal:
    def __init__(self, trainNumber, stationFrom, stationTo, cars, orderTime, departureTimeStamp,leadcode,callletters,number=0,open=True):
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
        self.units = [] # presumption is that the train is departing AND being created. Weirdly, the manual doesn't proscribe assigning units other than the lead
        self.lead = leadcode
        self.callletters = callletters # no idea how to generate
        self.open = open
        self.exceptions = dict()
    def cardformat(self,type):
        cardstack = []
        if type == 'D':
            selector = "#somekindofcodeshre*                                                            "
            addresses = "H Some kind of address goes here but I have no idea what it be  *               "
            departure = "D%s%s%s    %s%s%s                   %s%s %s    -%s %s " % (self.trainNumber,self.fr,self.to,pad(self.loads,3),pad(self.empties,3),self.orderTime,self.departure,pad(self.tonnage,5),self.lead,self.callletters,self.number)
            carlst = list(map(str,self.carconsist))
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
        return "[%s] Journal %s for train %s from %s to %s with %s loads and %s empties." % (ostatus,self.number,self.trainNumber,self.fr,self.to,self.loads,self.empties)

def loadJournal(filename):
    fr = ''
    to = ''
    trainnum = ''
    leadunit = ''
    number = ''
    ordert = ''
    dept = ''
    consists = []
    exceptions = []
    with open(filename,"r") as f:
        for x in f.readlines():
            card = x[:-1] # remove newline
            if card[0] in ("A","D","K"): # arrival, origin or departure header
                trainnum = card[1:5]
                number = ''
                if card[0] in ("A","C","D") and number == '':
                    number = card[74:79]
                if card[0] == "D":
                    ordert = card[25:29]
                    dept = card[48:56]
                    leadunit = card[62:66]
                fr = card[5:10]
                to = card[10:15]
            elif card[0] == "G":
                cardcar = car(card[1:5],card[5:11],card[11],card[12:14],card[14:22],card[22:24],card[24:26],card[26:31],card[31],card[32:37],card[37],card[38:45],card[48:58],card[58:64],card[64:66],card[66:68],card[68:74],card[74:79])
                consists.append(cardcar)
            elif card[0] == "H":
                exceptions.append(card)
        out = trainjournal(trainnum,fr,to,consists,ordert,dept,leadunit,"LO",number=number)
    for ex in exceptions:
        out.addexception(ex)
    return out


if __name__=="__main__":
    unattachedConsists = dict()
    loadedJournals = dict()
    while True:
        if len(loadedJournals.values()) > 0:
            print("Loaded Journals: ")
            for x in loadedJournals.values():
                print(str(x))
        if len(unattachedConsists.values()) > 0:
            print("Unattached consists: ")
            for x in unattachedConsists.values():
                print(str(x))
        print("Available options are [O]riginate a car, [T]erminate a train, Track an [A]rrival, Track a [D]eparture, [L]oad a card deck, [W]rite a card deck")
        choice = input("Please select an option: ")[0].lower()
        if choice == "l":
            fname = input("Please enter filename: ")
            tjournal = loadJournal(fname)
            loadedJournals[tjournal.number] = tjournal
        elif choice == "w":
            wjournal = input("Enter a journal number: ")
            typ = input("What kind of deck to write? Available options are (D). ").upper()
            fname = input("What filename to use? ")
            if "." not in fname:
                fname += ".t80"
            loadedJournals[wjournal].write(type=typ,filename=fname)
        elif choice == "o":
            railroad = ''
            number = ''
            condition = ''
            typ = ''
            finalDest = ''
            block = ''
            zone = ''
            onLineDest = ''
            