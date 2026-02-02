## CNR Interim Car Tracing System

In the mid 1960s, the Canadian National Railway decided to implement an IBM System 360-based system to track where all of their freight cars were. It built upon their previous system that used stacks of punch cards to enter car movements into the system, expanding it to allow agents at CNR offices to directly query the current status, rather than waiting until they could get the daily report.

This is a Python reimplementation of that system, starting first with the reporting side, and eventually expanding to include the Traffic Master Plan card-based entry system.

If you want to try this, use the included SQL file to set up a DB, make sure that main.py points at it, and try some of the following commands:

python main.py 12123456

python main.py 24654321

These should return:
--123456CGTX 01/2010
D17840 10/0035 A408E

--654321UTLX 01/2010
A88994 10/1930  840L TA93390S K C IRVING ST. JOHN14790Z GASOLN
BAD ORDERED AT JASPER        WHEELS          0110220088994
CARE MR J A LAJEUNESSE OR MR JEAN MAURICE USEREAU

Finally, if you know anything about any of these CNR systems, [please reach out to me!](http://nboyko.com/contact)