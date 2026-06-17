# this contains things that would have been actual trains/people doing things IRL
# probably eventually this is replaced by a UI with some people, or some (non-LLM) AI in a game
# if that's the case, this is an automated test suite/setup library

from helpers import cleantraces, getcars, Train
from random import randint, choice
import sys
from sqlite3 import connect

def runDay(trains: list[Train],conn, cur, trainday,allroute):
    for train in trains:
        #print(train.number)
        #print(train.curpos)
        loc = train.location()
        cars = getcars(loc,cur) # returns FileCars
        result = train.move()
        #print(result)
        if result != 0: # 0 indicates the train has completed its journey.
            traintime = randint(0,2400)
            while trainday < 1:
                trainday += 30
            for car in cars:
                #print(car.curdest)
                if result == car.curdest:
                    lore = 'E'
                    car.gentrace('A',result,trainday,leavet + 198, train.number, lore,cur)
                elif randint(0,10) > 8: # 10% chance to generate a new waybill. The examples in the manual show nonsensical waybilling as well.
                    car.removewaybill(cur) # not necessary later
                    lore = 'L'
                    leavet = randint(0,2200)
                    wdate = trainday -1
                    while wdate == 0:
                        wdate += 1
                    car.genwaybill("SMONE, LLC",loc,choice(allroute),"SOMCGO",wdate,leavet,1234567,cur) # not clever date
                    car.gentrace('D',loc,wdate,leavet + 198, train.number, lore,cur)
                    car.gentrace('A',result,trainday,traintime, train.number, lore,cur)
                elif randint(0,10) > 5: # should be a 40% chance
                    car.gentrace('A',result,trainday,traintime, train.number,car.lore,cur)
    cleantraces(cur)
    conn.commit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py TrainNum,RouteStop1,RouteStop2,etc")
    conn = connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("SELECT MAX(Day) FROM Tracefile;")
    trainday = int(cur.fetchone()[0]) + 1
    if trainday > 31:
        trainday = trainday - 31
    trens = []
    allroutes = []
    for x in sys.argv[1:]:
        xsp = x.split(',')
        trens.append(Train(xsp[0],xsp[1:]))
        allroutes.extend(xsp[1:])
    runDay(trens,conn,cur,trainday,allroutes)