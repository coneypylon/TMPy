# this contains things that would have been actual trains/people doing things IRL
# probably eventually this is replaced by a UI with some people, or some (non-LLM) AI in a game
# if that's the case, this is an automated test suite/setup library

from main import cleantraces, getcars
from random import randint, choice

def runDay(trains,conn, cur, trainday,allroute):
    for train in trains:
        loc = train.location()
        cars = getcars(loc,cur) # returns FileCars
        result = train.move()
        if result != 0: # 0 indicates the train has completed its journey.
            traintime = randint(0,2400)
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