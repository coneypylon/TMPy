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
	PRIMARY KEY("Initial","Number","Consignee"),
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
DROP VIEW IF EXISTS "TracesToDelete";
CREATE VIEW TracesToDelete AS WITH LatestTraces AS (
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
     t.Day, t.Time
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
WHERE t.rn > 4 
ORDER BY c.Initial ASC, c.Number ASC, t.Day ASC, t.Time ASC;
COMMIT;
