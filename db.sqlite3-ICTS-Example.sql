BEGIN TRANSACTION;
DROP TABLE IF EXISTS "Carfile";
CREATE TABLE "Carfile" (
	"Initial"	TEXT,
	"Number"	INTEGER,
	"Type"	TEXT,
	"Grade"	TEXT,
	PRIMARY KEY("Initial","Number")
);
DROP TABLE IF EXISTS "ExceptionFile";
CREATE TABLE "ExceptionFile" (
	"Initial"	TEXT,
	"Number"	INTEGER,
	"Text"	TEXT,
	"Day"	TEXT DEFAULT (strftime('%d', 'now', 'localtime')),
	"Time"	TEXT DEFAULT (strftime('%H%M', 'now', 'localtime')),
	PRIMARY KEY("Text","Number","Initial"),
	FOREIGN KEY("Initial","Number") REFERENCES "Carfile"
);
DROP TABLE IF EXISTS "Tracefile";
CREATE TABLE "Tracefile" (
	"Initials"	TEXT,
	"Number"	INTEGER,
	"ArrOrDep"	TEXT CHECK("ArrOrDep" IN ('D', 'A')),
	"Station"	INTEGER,
	"Day"	INTEGER,
	"Time"	INTEGER,
	"Train"	INTEGER,
	"LoadOrEmpty"	TEXT CHECK("LoadOrEmpty" IN ('L', 'E')),
	PRIMARY KEY("Initials","Number","Day","Time"),
	FOREIGN KEY("Initials","Number") REFERENCES "Carfile",
	FOREIGN KEY("Station") REFERENCES "stations"("number")
);
DROP TABLE IF EXISTS "Waybillfile";
CREATE TABLE "Waybillfile" (
	"ID"	INTEGER PRIMARY KEY,
	"Initial"	TEXT NOT NULL,
	"Number"	INTEGER NOT NULL,
	"Consignee"	TEXT NOT NULL,
	"Contents"	TEXT,
	"Destination"	INTEGER NOT NULL,
	"OffJunction"	TEXT DEFAULT ' ',
	"OriginStation"	INTEGER NOT NULL,
	"OnJunction"	TEXT DEFAULT ' ',
	"Day"	INTEGER,
	"Time"	INTEGER,
	FOREIGN KEY("Destination") REFERENCES "stations"("number"),
	FOREIGN KEY("Initial","Number") REFERENCES "Carfile",
	FOREIGN KEY("OriginStation") REFERENCES "stations"("number")
);
DROP TABLE IF EXISTS "stations";
CREATE TABLE "stations" (
	"number"	INTEGER,
	"code"	TEXT NOT NULL,
	"interchangedrailway"	TEXT,
	"name"	TEXT NOT NULL,
	"railway"	TEXT NOT NULL,
	"interchange"	INTEGER NOT NULL,
	PRIMARY KEY("number")
);
INSERT INTO "Carfile" VALUES ('CGTX',123456,'T','A'),
 ('UTLX',654321,'T','A'),
 ('CV  ',246810,'X','A'),
 ('MDT ',246810,'X','A');
INSERT INTO "ExceptionFile" VALUES ('UTLX',654321,'BAD ORDERED AT JASPER        WHEELS          0110220088994','11','0815'),
 ('UTLX',654321,'CARE MR J A LAJEUNESSE OR MR JEAN MAURICE USEREAU','11','0815');
INSERT INTO "Tracefile" VALUES ('UTLX',654321,'A',88994,10,1930,840,'L'),
 ('CGTX',123456,'A',12900,5,1015,'A405','L'),
 ('CGTX',123456,'A',14523,6,1845,406,'L'),
 ('CGTX',123456,'A',17840,9,2130,'B598','E'),
 ('CGTX',123456,'D',17840,10,35,'A408','E'),
 ('CV  ',246810,'A',43335,8,2245,'A806','E'),
 ('MDT ',246810,'D',33338,10,330,310,'L');
INSERT INTO "Waybillfile" VALUES ('UTLX',654321,'K C IRVING','GASOLN',14790,'Z',93390,'S',9,935),
 ('CGTX',123456,'K C IRVING','OIL   ',14523,'L',12600,'R',5,13);
INSERT INTO "stations" VALUES (12600,'',NULL,'','',0),
 (12900,' ',NULL,'HULLABALOO,NB','CNR',0),
 (14523,' ',NULL,'MONCTON, NB','CNR',0),
 (14790,'N','BAR','ST. JOHN, NB','CNR',1),
 (17840,' ',NULL,'MY HOUSE,NB','CNR',0),
 (32520,' ',NULL,'SHAWINIGAN, QC','CNR',0),
 (33338,'',NULL,'','',0),
 (35100,'R','RUT','ALBURGH, Vt.','CVR',1),
 (35110,'N','NAJ','ROUSES POINT, N.Y.','CVR',1),
 (35130,'S',NULL,'SWANTON, Vt.','CVR',1),
 (35140,'P','CP','RICHFORD, Vt.','CVR',1),
 (35150,'S','SJLC','Sheldon Jct., Vt.','CVR',1),
 (35160,'R',NULL,'BURLINGTON, Vt.','CVR',1),
 (35180,'B',NULL,'WHITE RIVER JCT., Vt.','CVR',1),
 (35190,'B',NULL,'WINDSOR, Vt.','CVR',1),
 (35200,'B',NULL,'BRATLEBORO, Vt.','CVR',1),
 (35210,'B',NULL,'SOUTH VERNON, Vt.','CVR',1),
 (35220,'B',NULL,'Millers Falls, Mass.','CVR',1),
 (35230,'B','BM','BELCHERTON, Mass.','CVR',1),
 (35240,'B','BA','PALMER, Mass.','CVR',1),
 (35250,'N',NULL,'WILLIMANTIC, Conn.','CVR',1),
 (35260,'N',NULL,'NORWICH, Conn.','CVR',1),
 (35270,'N','NH','New London, Conn.','CVR',1),
 (41975,' ',NULL,'TORONTO, ON','TTR',0),
 (43335,' ',NULL,'NOGO, ON','CNR',0),
 (46170,' ',NULL,'GUELPH, ON','CNR',0),
 (46190,' ',NULL,'KITCHENER, ON','CNR',0),
 (87930,' ',NULL,'EDMONTON, AB','CNR',0),
 (88994,' ',NULL,'JASPER, AB','CNR',0),
 (93390,'N','GN','VANCOUVER, BC','CNR',1);
DROP VIEW IF EXISTS "CanonicalExceptions";
CREATE VIEW CanonicalExceptions AS SELECT Initial, Number, Text FROM
(SELECT *, row_number() OVER (
	PARTITION BY Initial, Number
	ORDER BY Day DESC, Time DESC
	) as rn
FROM ExceptionFile)
WHERE rn <= 3 ORDER BY Initial ASC, Number ASC;
DROP VIEW IF EXISTS "LastLocationComplete";
CREATE VIEW LastLocationComplete AS WITH LatestTraces AS (
    SELECT 
        rowid AS original_id, -- Explicitly carry the ID forward
        *, 
        ROW_NUMBER() OVER (
            PARTITION BY Initials, Number
            ORDER BY Day DESC, Time DESC
        ) as rn
    FROM Tracefile
),
WaybillEvents AS (
    SELECT 
        w.rowid AS wb_rowid,
        (SELECT t2.rowid 
         FROM Tracefile t2
         WHERE t2.Initials = w.Initial 
           AND t2.Number = w.Number
           AND (t2.Day > w.Day OR (t2.Day = w.Day AND t2.Time >= w.Time))
         ORDER BY t2.Day ASC, t2.Time ASC
         LIMIT 1) AS first_trace_match_id
    FROM Waybillfile w
)
SELECT 
    c.Initial, c.Number,
    t.ArrOrDep AS "ArrivalOrDeparture", t.Station AS "StationNumber", t.Day, t.Time, t.Train, t.LoadOrEmpty AS "LoadedOrEmpty",
    c.Type, c.Grade,
    w.OriginStation, w.OnJunction AS "OnComingJunction", w.Consignee, 
    SUBSTR(s.name, 1, 8) AS "FinalDestination", w.Destination AS "DestinationStation", 
    w.OffJunction AS "Off-GoingJunction", w.Contents
FROM LatestTraces AS t
JOIN Carfile AS c
    ON t.Initials = c.Initial
    AND t.Number = c.Number
LEFT JOIN WaybillEvents we
    ON t.original_id = we.first_trace_match_id
LEFT JOIN Waybillfile AS w
    ON we.wb_rowid = w.rowid
LEFT JOIN stations AS s
    ON w.Destination = s.number
WHERE t.rn = 1 
ORDER BY c.Initial ASC, c.Number ASC, t.Day DESC, t.Time DESC;
DROP VIEW IF EXISTS "RunningRecordsComplete";
CREATE VIEW RunningRecordsComplete AS WITH LatestTraces AS (
    SELECT 
        rowid AS original_id, -- Explicitly carry the ID forward
        *, 
        ROW_NUMBER() OVER (
            PARTITION BY Initials, Number
            ORDER BY Day DESC, Time DESC
        ) as rn
    FROM Tracefile
),
WaybillEvents AS (
    SELECT 
        w.rowid AS wb_rowid,
        (SELECT t2.rowid 
         FROM Tracefile t2
         WHERE t2.Initials = w.Initial 
           AND t2.Number = w.Number
           AND (t2.Day > w.Day OR (t2.Day = w.Day AND t2.Time >= w.Time))
         ORDER BY t2.Day ASC, t2.Time ASC
         LIMIT 1) AS first_trace_match_id
    FROM Waybillfile w
)
SELECT 
    c.Initial, c.Number,
    t.ArrOrDep AS "ArrivalOrDeparture", t.Station AS "StationNumber", t.Day, t.Time, t.Train, t.LoadOrEmpty AS "LoadedOrEmpty",
    c.Type, c.Grade,
    w.OriginStation, w.OnJunction AS "OnComingJunction", w.Consignee, 
    SUBSTR(s.name, 1, 8) AS "FinalDestination", w.Destination AS "DestinationStation", 
    w.OffJunction AS "Off-GoingJunction", w.Contents
FROM LatestTraces AS t
JOIN Carfile AS c
    ON t.Initials = c.Initial
    AND t.Number = c.Number
LEFT JOIN WaybillEvents we
    ON t.original_id = we.first_trace_match_id
LEFT JOIN Waybillfile AS w
    ON we.wb_rowid = w.rowid
LEFT JOIN stations AS s
    ON w.Destination = s.number
WHERE t.rn <= 4 
ORDER BY c.Initial ASC, c.Number ASC, t.Day ASC, t.Time ASC;
DROP VIEW IF EXISTS "StatusLine";
CREATE VIEW StatusLine AS
SELECT Number, Initial, strftime('%d', 'now', 'localtime') as Day, strftime('%H%M', 'now', 'localtime') as Time FROM Carfile ORDER BY Initial ASC, Number ASC;
COMMIT;
