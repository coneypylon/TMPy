'''Utilities for making card decks.
Possibly actually useful someday.

Loosely corresponds to CN Car Control from ~1967
'''

from helpers import carcard, trainjournal, Station, Car, FileCar, confirm, frontpad
import configparser, sqlite3

def loadJournal(filename,curs):
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
                fr = Station(int(card[5:10]),curs)
                to = Station(int(card[10:15]),curs)
            elif card[0] == "G":
                cardcar = carcard(initials=card[1:5],number=card[5:11],condition=card[11],type=card[12:14],destination=card[14:22],block=card[22:24],zone=card[24:26],onlinedest=card[26:31],delto=card[31],onlineorig=card[32:37],recfrom=card[37],commoditycode=card[38:45],consignee=card[48:58],contents=card[58:64],taretons=card[64:66],nettons=card[66:68],waybillnum=card[68:74])
                consists.append(cardcar)
            elif card[0] == "H":
                exceptions.append(card)
        out = trainjournal(trainnum,fr,to,consists,ordert,dept,leadunit,"LO",number=number)
    for ex in exceptions:
        out.addexception(ex)
    return out


def interactivejournal(jnum,arrival: bool,conn):
    curs = conn.cursor()

    # things we need to figure out from the user in some way:
    tnum = input("Enter train number: ")
    startstat = 0
    endstat = 0
    month = frontpad(input("Enter month #: "),2)
    day = input("Enter date: ")
    time = input("Enter time of report: ")
    otime = input("Enter order time: ")
    lead = input("Enter lead unit #: ")
    callcode = input("Enter call code: ")
    cars = []

    # computed entries
    empties = 0
    loads = 0
    tons = 0

    while startstat == 0: # we will do some error checking
        snum = input("Enter From Station: ")
        try:
            startstat = Station(snum,curs)
        except Exception as e:
            print(str(e))
    while endstat == 0: # we will do some error checking
        snum = input("Enter To Station: ")
        try:
            endstat = Station(snum,curs)
        except Exception as e:
            print(str(e))
    
    while True:
        initial = input("Enter car initials (e.g. 'CNR'): ")
        number = int(input("Enter car number: "))
        try:
            foundcar = Car(initial,number,curs)
            fields = ('Waybill Number','Commodity Code', 'Contents', 'Tonnage','Consignee','Final Destination','Online Origin','On-Coming Junction','Online Destination','Off-Going Junction','Block Number','Zone')
            values = (foundcar.billnum,foundcar.commodity,foundcar.contents,foundcar.tonnage,foundcar.consignee,foundcar.destination,foundcar.onlineorig,foundcar.recfrom,foundcar.onlinedest,foundcar.delto,foundcar.block,foundcar.zone)
            foundcar.billnum,foundcar.commodity,foundcar.contents,foundcar.tonnage,foundcar.consignee,foundcar.destination,foundcar.onlineorig,foundcar.recfrom,foundcar.onlinedest,foundcar.delto,foundcar.block,foundcar.zone = confirm(fields,values)
            if foundcar.tonnage > 0:
                foundcar.isloaded = True
            else:
                foundcar.isloaded = False
            # ^ no checking of values - could be problematic
            cars.append(foundcar)
        except KeyError: # we didn't find a car
            pass
            cond = input("Enter car condition: ")
            typ = input("Enter car type")
            tare = input("Enter the tare weight of the car: ")
            waybillnum = input("Enter waybill number: ")
            commodity = input("Enter commodity code: ") # probably should be a lookup
            contents = input("Enter content text")
            consignee = input("Enter consignee: ")
            tonnage = input("Enter tonnage of %s: ") % contents
            onlineorig = Station(int(input("Enter origin code: ")))
            recfrom = input("Enter on-coming junction: ")
            onlinedest = Station(int(input("Enter destination code: "))) # likely we will have to eventually put a separate destination
            delto = input("Enter off-going junction: ")
            desttext = onlinedest.name
            block = input("Enter block number: ")
            zone = '  '

            card = carcard(initial,number,cond,typ,desttext,block,onlinedest.number,onlineorig.number,tare,zone,delto,recfrom,commodity,consignee,contents,tonnage,waybillnum)
            inst = input("Insert directly into Carfile? ")
            if inst[0].upper() == 'Y' and arrival:
                fcar = card.genFileCar()
                fcar.addtofile(tare,curs)
            elif inst[0].upper() == 'Y':
                fcar = card.genFileCar()
                fcar.addtofile(tare,curs)
        cont = input("Added %s. Add another car? " % foundcar.registration)
        if cont.upper()[0] != 'Y':
            break

    return trainjournal(tnum,startstat,endstat,cars,otime,time,lead,callcode,jnum)


if __name__=="__main__":
    unattachedConsists = dict()
    loadedJournals = dict()

    # DB setup
    # fetch the config
    config = configparser.ConfigParser()
    config.read("reservations.ini")
    db = config.get('DEFAULT','db', fallback='db.sqlite3')
    
    # set up the db connection
    conn = sqlite3.connect(db)

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
            tjournal = loadJournal(fname,conn.cursor())
            loadedJournals[tjournal.number] = tjournal
        elif choice == "w":
            wjournal = input("Enter a journal number: ")
            try:
                test = loadedJournals[wjournal]
                typ = input("What kind of deck to write? Available options are (D). ").upper()
                fname = input("What filename to use? ")
                if "." not in fname:
                    fname += ".t80"
                loadedJournals[wjournal].write(type=typ,filename=fname)
            except KeyError: # the journal doesn't exist/hasn't been made
                print("No such journal has been loaded.")
        elif choice == "a":
            wjournal = input("Enter a journal number: ")
            loadedJournals[wjournal] = interactivejournal(wjournal,True,conn)
        elif choice == "d":
            wjournal = input("Enter a journal number: ")
            loadedJournals[wjournal] = interactivejournal(wjournal,False,conn)
        elif choice == "o":
            initial = input("Enter railroad initials: ")
            number = input("Enter car number: ")
            tare = int(input("Enter tare weight of car: "))
            nucar = FileCar(initial,number,'E',tare=tare).addtofile(conn.cursor())