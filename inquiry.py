import configparser, sys, sqlite3, time
from helpers import lookuproads, frontpad, clear_screen



def parse_n_route_string(string,curs,conn):
    if len(string) < 3 or len(string) > 8: # we accept single-digit car numbers
        return "usage: script.py RINNNNNN"
    
    # helpful constants and variables
    rq = string[0]
    initialsubquery = lookuproads(string[1],curs)
    num = int(string[2:])
    outputs = dict() # it's possible there are multiple returned.

    
    # get the meat
    if rq in ['1','2']:
        mainq = "SELECT * FROM LastLocationComplete WHERE Number = %s AND Initial %s;" % (num,initialsubquery)
    elif rq in ['3','4']:
        mainq = "SELECT * FROM RunningRecordsComplete WHERE Number = %s AND Initial %s;" % (num,initialsubquery)
    else:
        raise NotImplementedError

    # get the status line(s) and the exception(s)
    statusq = "SELECT * FROM StatusLine WHERE Number = %s AND Initial %s;" % (num,initialsubquery)
    exceptionsq = "SELECT * FROM CanonicalExceptions WHERE Number = %s AND Initial %s;" % (num,initialsubquery)

    # request them
    curs.execute(statusq)
    rawstatus = curs.fetchall()
    for result in rawstatus:
        outputs[result[1]+str(result[0])] = ['--%s%s %s/%s' % result]

    curs.execute(mainq)
    rawcore = curs.fetchall()
    for result in rawcore:
        car = str(result[0]) + str(result[1])
        if str(result[10]) == 'None' or rq in ['1','3']: # empty, abbreviated
            record = '%s%s %s/%s %s%s' % (result[2],result[3],frontpad(result[4],2),frontpad(result[5],4),frontpad(str(result[6]),4),result[7])
        else:
            fullrecord = [result[2],result[3],frontpad(result[4],2),frontpad(result[5],4),frontpad(str(result[6]),4)]
            fullrecord.extend((result[7:]))
            record = '%s%s %s/%s %s%s %s%s%s%s %s %s%s%s %s' % tuple(fullrecord)
        outputs[car].append(record)

    curs.execute(exceptionsq)
    rawexcept = curs.fetchall()
    for result in rawexcept:
        car = str(result[0]) + str(result[1])
        outputs[car].append(result[2])
    return outputs.values()



if __name__ == "__main__": # we're not in a lambda anymore
    # fetch the config
    config = configparser.ConfigParser()
    config.read("reservations.ini")
    db = config.get('DEFAULT','db', fallback='db.sqlite3')
    
    # set up the db connection
    conn = sqlite3.connect(db)

    cur = conn.cursor()
    request = sys.argv[1].upper()
    if request == 'INT':
        clear_screen()
        while True:
            request = input().upper()
            for x in parse_n_route_string(request,cur,conn):
                for y in x:
                    time.sleep(1)
                    print(y)
            time.sleep(1)
            print()
    for x in parse_n_route_string(request,cur,conn):
        for y in x:
            print(y)