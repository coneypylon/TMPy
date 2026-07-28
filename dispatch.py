# this contains things that would have been actual trains/people doing things IRL
# probably eventually this is replaced by a UI with some people, or some (non-LLM) AI in a game
# if that's the case, this is an automated test suite/setup library

from helpers import cleantraces, getcars, Train, truncstr, backpad
from random import randint, choice
import sys
from sqlite3 import connect
import pyexcel_odsr as ods


companies = ["Bruce Wayne Ltd.","Fast Forwarding","Great Plastics","King St Ltd","Robins Hoods Cloaks","Shoobie Snacks","Wallys World","Weber Street Enterprises","William and Sons"] # TODO: not this
commodities = ["ABRASV","ACTATE","ACETON","ACRAFT","ALCHOL","ALFALF","ALUMNA","ALUMN","AMMO","ANCHOR","ABGARS","TALLOW","APCOTS","ASBEST","ASPHLT","AUTOS","APARTS","BBLS","BASKTS","BATRYS","BATUBS","BAUXTE","WALLBD","BEETPP","BENZEN","BERRYS","BILLET","IMPTS","BISCTS","BOILRS","BOTTLS","BROCLI","BRUSHS","BWHEAT","BLDGS","MACHY","CABBGE","CALCUM","CGOODS","CANTS","CARBDE","CARBON","CARDBD","CARROT","CARTON","CASING","CASTGS","CATLGS","CATFD","CFLOWR","CSODA","CEREAL","CHCOAL","FRAMES","CHEM","CHRRYS","CWARE","CHIPBD","CHLRNE","XTREES","CIGTS","CINDER","CBEANS","CCONUT","COMPD","CONTRS","COOPMT","CRNBRY","CREOSO","CROKRY","CUKES","CYAMID","CYNIDE","DAIRYP","DOXIDE","ERWARE","ENGS","EXLOS","EXTRAT","EXFRT","FASTGS","FELSPR","FENCE","FERTZ","FIBRBD","FITTGS","FLSHGS","FURSPR","FURNAC","FURN","GASKET","GASO","GENRTR","GLWARE","GLYCRN","GRANIT","GRANLS","GRPFRT","GRFITE","HDWARE","HTRS","HHGDS","INSIDS","INSULN","JELLY","KRSENE","KLENEX","LAQUER","LEATHR","LETUCE","LIMSTN","LINOLM","LINSED","LIQUOR","STOCK","MAGS","MARG","MIDDS","MLTYST","MLKPDR","MOLASS","NAPTHA","NAPKIN","PAPER","OILCTH","ORANGS","PEACHS","PEANUT","PEATMS","OIL","PHOSRK","TRLRS","PAPPLS","PLASTR","PLASBD","PLSTIC","PLYWD","POPCRN","SPUDS","PLTRY","PULPBD","PYRITE","RADS","RAISIN","RFRGRS","ROOFNG","SAWDST","SCRNGS","SHAVGS","SHINGL","SHRUBS","SILICN","SODASH","SOLVNT","SBEANS","SPRING","STDUST","STRWBD","STYRNE","SGBEET","SULPHR","SUNDRS","TAPOCA","TINPLT","TOBACO","TOMS","TRACTR","TURKYS","TURNIP","TURPS","VARNSH","VEGTS","VINGAR","WALNUT","WMELON","WHISKY","WDFLOR","WPULP"]



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
                    billcomp = backpad(truncstr(choice(companies).upper(),10),10)
                    billcomm = choice(commodities)
                    car.genwaybill(billcomp,loc,choice(allroute),billcomm,wdate,leavet,1234567,cur) # not clever date
                    car.gentrace('D',loc,wdate,leavet + 198, train.number, lore,cur)
                    car.gentrace('A',result,trainday,traintime, train.number, lore,cur)
                elif randint(0,10) > 5: # should be a 40% chance
                    car.gentrace('A',result,trainday,traintime, train.number,car.lore,cur)
    cleantraces(cur)
    conn.commit()


if __name__ == "__main__":
    conn = connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("SELECT MAX(Day) FROM Tracefile;")
    trainday = int(cur.fetchone()[0]) + 1
    if trainday > 31:
        trainday = trainday - 31
    trens = []
    allroutes = []
    if len(sys.argv) == 1:
        basebook = 'bigdata.ods' #TODO: put this in the DB.
        data: dict = ods.get_data(basebook)
        rawtrains: list[list[str]] = data["Trains"][1:]
        for train in rawtrains:
            if train == []:
                break
            route = train[1].split(',')
            allroutes.extend(route)
            num = int(train[0])
            trens.append(Train(num,route))
    else:
        for x in sys.argv[1:]:
            xsp = x.split(',')
            trens.append(Train(xsp[0],xsp[1:]))
            allroutes.extend(xsp[1:])
    runDay(trens,conn,cur,trainday,allroutes)