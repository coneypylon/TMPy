import configparser, os, sys, sqlite3, time

def pad(num,spaces):
    if type(num) == str:
        tnum = num
        while len(tnum)<spaces:
            tnum = " " + tnum
    else:
        tnum = str(num)
        while len(tnum)<spaces:
            tnum = "0" + tnum
    return tnum

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
        return "= 'CN'"
    elif selcode == '2': # CGTX
        return "= 'CGTX'"
    elif selcode == '3': # CP
        return "= 'CP'"
    elif selcode == '4': # UTLX
        return "= 'UTLX'"
    elif selcode == '8': # Other Foreign
        return "NOT IN ('CN','CGTX','CP','UTLX')"
    elif selcode == '9': # All Foreign
        return "NOT IN ('CN')" # probably could be strict equality, but I'm not sure how GTW/CVR is handled.
    else:
        raise Exception

def parse_n_route_string(string,curs,conn):
    if len(string) != 8:
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

    #print((statusq,mainq,exceptionsq))

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
            record = '%s%s %s/%s %s%s' % (result[2],result[3],pad(result[4],2),pad(result[5],4),pad(str(result[6]),4),result[7])
        else:
            fullrecord = [result[2],result[3],pad(result[4],2),pad(result[5],4),pad(str(result[6]),4)]
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