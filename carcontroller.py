'''
Loose approximation of CN Car Control from ~1967

Works on TTY or card decks fed to it.
'''

from helpers import carcard, trainjournal, Station, Car, FileCar, confirm, frontpad
from inquiry import parse_n_route_string
import configparser, sqlite3, sys

def makecard(card:str,curs:sqlite3.Cursor)->tuple[str,carcard | trainjournal | str]:
    if card[0] in ("A","D","K"): # arrival, origin or departure header
        trainnum = card[1:5]
        nber = ''
        lunit = '0000'
        ordert = ''
        dept = ''
        if card[0] in ("A","C","D") and nber == '':
            nber = card[74:80]
        if card[0] == "D":
            ordert = card[25:29]
            dept = card[48:56]
            leadunit = card[62:66]
            lunit = frontpad(int(leadunit),4)
        fr = Station(int(card[5:10]),curs)
        to = Station(int(card[10:15]),curs)
        out = trainjournal(int(trainnum),fr,to,[],ordert,dept,lunit,"LO",number=int(nber))
        return (0,out)
    elif card[0] == "G":
        cardcar = carcard(initials=card[1:5],number=card[5:11],condition=card[11],type=card[12:14],destination=card[14:22],block=card[22:24],zone=card[24:26],onlinedest=int(card[26:31]),delto=card[31],onlineorig=int(card[32:37]),recfrom=card[37],commoditycode=card[38:45],consignee=card[48:58],contents=card[58:64],taretons=int(card[64:66]),nettons=int(card[66:68]),waybillnum=card[68:74])
        return (1,cardcar)
    elif card[0] == "H":
        return (2,card)
    
def loadJournal(fileorcards: str | list[str],curs,tty=False):
    fr = None
    to = None
    tj = None
    trainnum = 0000
    leadunit = 0000
    number = ''
    ordert = '0000'
    dept = '0000'
    consists = []
    exceptions = []
    if not tty:
        with open(fileorcards,"r") as f: # TODO: Refactor to use makecard
            cards = f.readlines()
    else:
        cards = fileorcards
    for x in cards:
        if not tty:
            card = x[:-1] # remove newline
        else:
            card = x
        if card[0] in ("A","D","K"): # arrival, origin or departure header
            trainnum = card[1:5]
            nber = '42069'
            if card[0] in ("A","C","D") and nber == '':
                nber = card[74:80]
            if card[0] == "D":
                ordert = card[25:29]
                dept = card[48:56]
                leadunit = card[62:66]
            fr = Station(int(card[5:10]),curs)
            to = Station(int(card[10:15]),curs)
        elif card[0] == "G":
            cardcar = carcard(initials=card[1:5],number=card[5:11],condition=card[11],type=card[12:14],destination=card[14:22],block=card[22:24],zone=card[24:26],onlinedest=int(card[26:31]),delto=card[31],onlineorig=int(card[32:37]),recfrom=card[37],commoditycode=card[38:45],consignee=card[48:58],contents=card[58:64],taretons=int(card[64:66]),nettons=int(card[66:68]),waybillnum=card[68:74])
            consists.append(cardcar)
        elif card[0] == "H":
            print(card)
            exceptions.append(card)
    tmp = frontpad(int(leadunit),4)
    out = trainjournal(trainnum,fr,to,consists,ordert,dept,tmp,"LO",number=int(nber))
    for ex in exceptions:
        out.addexception(ex)
    return out


'''
D 4204619087930    0010001130                   0718123600080    4        42069
GCNR 420690ABXKITCHENE11  46190 87930 CYANIDE   TEAMTRACK CYANID0104123456     
HCNR 420690IMPORTANT HANDLE WITH CARE                                   NM     
P END OF TRANSMISSION%%@@@@@@@@@@#AB*                                          
'''

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
            startstat = Station(int(snum),curs)
        except Exception as e:
            print(str(e))
    while endstat == 0: # we will do some error checking
        snum = input("Enter To Station: ")
        try:
            endstat = Station(int(snum),curs)
        except Exception as e:
            print(str(e))
    
    while True:
        initial = input("Enter car initials (e.g. 'CNR'): ")
        number = int(input("Enter car number: "))
        try:
            foundcar = Car(initial,number,curs)
            fields = ['Waybill Number','Commodity Code', 'Contents', 'Tonnage','Consignee','Final Destination','Online Origin','On-Coming Junction','Online Destination','Off-Going Junction','Block Number','Zone']
            values = [foundcar.billnum,foundcar.commodity,foundcar.contents,foundcar.tonnage,foundcar.consignee,foundcar.destination,foundcar.onlineorig,foundcar.recfrom,foundcar.onlinedest,foundcar.delto,foundcar.block,foundcar.zone]
            foundcar.billnum,foundcar.commodity,foundcar.contents,foundcar.tonnage,foundcar.consignee,foundcar.destination,foundcar.onlineorig,foundcar.recfrom,foundcar.onlinedest,foundcar.delto,foundcar.block,foundcar.zone = confirm(fields,values)
            if int(foundcar.tonnage) > 0:
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
            onlineorig = Station(int(input("Enter origin code: ")),curs)
            recfrom = input("Enter on-coming junction: ")
            onlinedest = Station(int(input("Enter destination code: ")),curs) # likely we will have to eventually put a separate destination
            delto = input("Enter off-going junction: ")
            desttext = onlinedest.name
            block = input("Enter block number: ")
            zone = '  '

            card = carcard(initial,str(number),cond,typ,desttext,block,int(onlinedest.number),int(onlineorig.number),int(tare),zone,delto,recfrom,commodity,consignee,contents,int(tonnage),waybillnum)
            inst = input("Insert directly into Carfile? ")
            if inst[0].upper() == 'Y' and arrival:
                fcar = card.genFileCar()
                fcar.addtofile(curs)
            elif inst[0].upper() == 'Y':
                fcar = card.genFileCar()
                fcar.addtofile(curs)
            conn.commit()
        cont = input("Added %s. Add another car? " % foundcar.registration)
        if cont.upper()[0] != 'Y':
            break

    return trainjournal(int(tnum),startstat,endstat,cars,otime,time,int(lead),callcode,jnum)


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

    if len(sys.argv) > 1: # someone helpfully included some arguments
        if sys.argv[1].upper() == 'TTY': # they want the TTY interface described in the TMP Car Control Manual
            curj = None
            curdeck = []
            while True:
                try:
                    entry = input().upper()
                    
                    curdeck.append(entry)
                    if entry.startswith('P'):
                        try:
                            tjournal = loadJournal(curdeck,conn.cursor(),tty=True)
                            curdeck = []
                        except KeyError as e:
                            print('S? %s' % str(e)[23:29])
                            curdeck = []
                            raise Exception
                        tjournal.close(conn)
                        compstr = "REC'D %s - %sL%sE%sT" % (tjournal.trainNumber,tjournal.loads,tjournal.empties,tjournal.tonnage)
                        print(compstr)
                    else:# 
                        if entry.startswith('I'): # inquiry
                            t = entry[1:]
                        else:
                            t=entry
                        t = parse_n_route_string(t,conn.cursor(),conn,embedded=True)
                        for x in t:
                            for y in x:
                                print(y)
                except KeyboardInterrupt:
                    exit()
        elif sys.argv[1].lower().endswith('t80'): # they gave us a card deck to read
            fname = sys.argv[1]
            tjournal = loadJournal(fname,conn.cursor())
            tjournal.close(conn)
            compstr = 'Train %s logged and closed successfully' % tjournal.trainNumber
            print(compstr)
        elif len(sys.argv[1]) == 80: # they are probably giving us a bunch of cards directly on the commandline
            pass
        else:
            print("No valid commandline arguments detected")
    else:
        # User interactive interface
        while True:
            if len(loadedJournals.values()) > 0:
                print("Loaded Journals: ")
                for x in loadedJournals.values():
                    print(str(x))
            if len(unattachedConsists.values()) > 0:
                print("Unattached consists: ")
                for x in unattachedConsists.values():
                    print(str(x))
            print("Available options are [O]riginate a car, [T]erminate a train, Track an [A]rrival, Track a [D]eparture, [C]lose a train journal, [L]oad a card deck, [W]rite a card deck")
            choice = input("Please select an option: ")[0].lower()
            if choice == "l":
                fname = input("Please enter filename: ")
                try:
                    tjournal = loadJournal(fname,conn.cursor())
                except FileNotFoundError:
                    try:
                        tjournal = loadJournal(fname + ".t80",conn.cursor())
                    except FileNotFoundError:
                        print('Could not find card deck')
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
                conn.commit()
            elif choice == 'c':
                wjournal = input("Enter a journal number: ")
                try:
                    test = loadedJournals[wjournal].close(conn)
                except KeyError: # the journal doesn't exist/hasn't been made
                    print("No such journal has been loaded.")

'''
AA42088994879301420001000    0                 08211841                   42069
GCNR 830000ASHGASPE   10  87930 88994 STOCK     M JACQUES HORSES0505696742

'''