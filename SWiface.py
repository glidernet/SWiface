#!/usr/bin/python3
#
# Python code to show access to OGN Beacons
#
# Version for gathering all the records for Spain

#from libfap import *
from ctypes import *
from datetime import datetime
import socket
import time
import string
import ephem
import pytz
import sys
import os
import os.path
import atexit
import signal
import ksta                               # import the list on known gliders
import socket
from parserfuncs import *                 # the ogn/ham parser functions
from ognddbfuncs import getognreg         # the  get registration from FlarmID
from geopy.distance import geodesic       # use the Vincenty algorithm^M
# use the Nominatim as the geolocator^M
from geopy.geocoders import GeoNames
from time import sleep

#########################################################################


# shutdown routine, close files and report on activity
def shutdown(sock, datafile, tmaxa, tmaxt, tmid, tmstd):
                                        # shutdown before exit
    sock.shutdown(0)                    # shutdown the connection
    sock.close()                        # close the connection file
    datafile.close()                    # close the data file
    # report number of records read and IDs discovered
    print('Records read:', nrecs, ' Ids found: ', nids)
    k = list(fid.keys())                # list the IDs for debugging purposes
    print ("Keys:", len(k))
    k.sort()                            # sort the list
    for key in k:                       # report data
        gid = 'Noreg '                  # for unknown gliders
        if spanishsta(key) or frenchsta(key):
            if key in ksta.ksta:
                gid = ksta.ksta[key]   # report the station name
                if len(gid) > 20:
                    gid = gid[0:20]
            else:
                gid = "NOSTA"           # marked as no sta
        else:
                                        # if it is a known glider ???
            if key != None :
                gid = getognreg(key)    # report the registration
        if key in fsmax:
            maxd = fsmax[key]
        else:
            if key in fmaxd:
                maxd = fmaxd[key]
            else:
                maxd = -1.0
        if key != fsta[key]:
            if fmaxs[key] > 0:
                print(key, '=>', fsta[key], gid, fid[key], "Max alt:", fmaxa[
                    key], "Max speed:", fmaxs[key], "Max. distance:", maxd, "Init at:", fidtm[key])
                # report FLARM ID, station used, registration and record counter
            else:
                print(key, '=>', fsta[key], gid, fid[key], "Max alt:",
                      fmaxa[key], "Max. distance:", maxd, "Init at:", fidtm[key])

        # in case of an receiver station , update the database with the coordinates
        if key == fsta[key] and key != None and key != "NONE  " and key in fslod:
            lati = fslla[key] 		# latitude
            lon = fsllo[key] 		# longitude
            alti = fslal[key] 		# altitude
            if (MySQL):
                selcmd = "SELECT * FROM  RECEIVERS WHERE  idrec =  '"+key+"'"
                curs.execute(selcmd)
            else:
                # SQL command to execute: SELECT
                selcmd = "select idrec from RECEIVERS where idrec=?"
                curs.execute(selcmd, (key,))
            if curs.fetchone() == None:
                if (MySQL):
                    inscmd = "insert into RECEIVERS values ('%s', '%s', %f,  %f,  %f)" % (
                        key, gid, lati, lon, alti)
                    try:
                        curs.execute(inscmd)
                    except MySQLdb.Error as e:
                        try:
                            print(">>>MySQL Error [%d]: %s" % (
                                e.args[0], e.args[1]))
                        except IndexError:
                            print(">>>MySQL Error: %s" % str(e))
                        print(">>>MySQL error:", inscmd)
                else:
                    inscmd = "insert into RECEIVERS values (?, ?, ?, ?, ?)"
                    curs.execute(inscmd, (key, gid, lati, lon, alti))
            else:
                if (MySQL):
                    if len(gid) > 30:
                        descri = gid[0:30]
                    else:
                        descri = gid
                    updcmd = "update RECEIVERS SET idrec='%s', descri='%s', lati=%f, longi=%f, alti=%f where idrec='%s' " % (
                        key, descri, lati, lon, alti, key)  # SQL command to execute: UPDATE
                    try:
                        curs.execute(updcmd)
                    except MySQLdb.Error as e:
                        try:
                            print(">>>MySQL Error [%d]: %s" % (
                                e.args[0], e.args[1]))
                        except IndexError:
                            print(">>>MySQL Error: %s" % str(e))
                        print(">>>MySQL error:", updcmd)
                else:
                    # SQL command to execute: UPDATE
                    updcmd = "update RECEIVERS SET idrec=?, descri=?, lati=?, longi=?, alti=? where idrec=?"
                    curs.execute(updcmd, (key, gid, lati, lon, alti, key))

            print("Added STATION: ==> ", key, gid)

#	end of if (for stations)
#   end of for

    gid=getognreg(tmid)                 # report now the maximun altitude for the day
    if gid == "NOReg":                  # if it is NOT a known glider ???
        gid = tmid                      # use the ID instead
    for key in fsmax:                   # report data
        print("Station: ", key, fsmax[key], "Kms. and", fscnt[key], "fixes...")
    print("Maximun altitude for the day:", tmaxa, ' meters MSL at:', tmaxt,
          'by:', gid, 'Station:', tmsta, "Max. distance:", tmaxd, "by:", tmstd)
    print("Sources:", fsour, "stations:", len (fsta), "Gliders:", len(k))
    print("Aircraft types:", acfttype)
    conn.commit()			# commit the DB updates
    conn.close()			# close the database
    local_time = datetime.now() 	# report date and time now
    location.date = ephem.Date(datetime.utcnow())
    print("Local Time (server) now is:", local_time, " and UTC time at location ",
          config.location_name, "is:", location.date, "UTC.")
    try:
        os.remove(config.APP+".alive")	# delete the mark of alive
    except:
        print("No SW.live")
    return				# job done

#########################################################################

#########################################################################


def signal_term_handler(signal, frame):
    print('got SIGTERM ... shutdown orderly')
    shutdown(sock, datafile, tmaxa, tmaxt, tmid, tmstd)  # shutdown orderly
    print("Exit now ....\n\n")
    sys.exit(0)


#########################################################################
# ......................................................................#
signal.signal(signal.SIGTERM, signal_term_handler)
# ......................................................................#


def blackhole(lati, lon):

    latn = 42.72667
    lats = 42.57833
    lonw = -0.1025
    lone = +0.18333
    if (lati < lats or lati > latn or lon < lonw or lon > lone):
        return (False)
    else:
        return (True)
########################################################################
def oksta(station):
    if (station != "FLYMASTER" and station != "NAVITER"):
        return(True)
    else:
        return(False)
#####################


def chkfilati(latitude,  flatil, flatiu):
    if (flatil == 0.0):
        return (False)
    if (flatil > 0):			# northern hemisphere
        if (latitude < flatil or latitude > flatiu):
            return (True)
    else:                               	# southern hemisfere
        if (latitude > flatil or latitude < flatiu):
            return (True)
    return(False)
########################################################################


#----------------------ogn_SilentWingsInterface.py start-----------------------
pgmversion = 'V2.01'
print("Start OGN Silent Wings Interface "+pgmversion)
print("======================================")

print("Program Version:", time.ctime(os.path.getmtime(__file__)))
date = datetime.utcnow()       		  # get the date
dte = date.strftime("%y%m%d")             # today's date
hostname = socket.gethostname()
print("Date: ", date, " UTC at:", hostname, "Process ID:", os.getpid())

import config

# protection against running the same daemon at the same time
if os.path.exists(config.PIDfile):
    print("SWiface already running !!!")
    raise RuntimeError("SWiface already running !!!")
    exit(-1)			# exit with an error code
#
# --------------------------------------#
with open(config.PIDfile, "w") as f:  # protect against to running the daemon twice
    f.write(str(os.getpid()))
    f.close()
# remove the lock file at exit
atexit.register(lambda: os.remove(config.PIDfile))

# --------------------------------------#
location_latitude = config.location_latitude  # get the configuration parameters
location_longitude = config.location_longitude
DBpath 	= config.DBpath
DBhost 	= config.DBhost
DBuser 	= config.DBuser
DBpasswd = config.DBpasswd
DBname 	= config.DBname
MySQL 	= config.MySQL
OGNT 	= config.OGNT
# --------------------------------------#


if OGNT:				# check if we want to add the OGN trackers to be pair with the Flarm units
    from ogntfuncs import *


# --------------------------------------#

acfttype = []                           # aircraft types
fid = {}                                # FLARM ID list
fidtm = {'NONE  ': 0}                   # FLARM ID list time
fsta = {'NONE  ': 'NONE  '}             # STATION ID list
fmaxa = {'NONE  ': 0}                   # maximun altitude
fmaxd = {'NONE  ': 0}                   # maximun distance
fmaxs = {'NONE  ': 0}                   # maximun speed
nrecs = 0                               # output record counter
nids = 0                                # output ID counter
i = 0                                   # loop counter
nerr = 0
tmaxa = 0                               # maximun altitude for the day
tmaxt = 0                               # time at max altitude
tmaxd = 0                               # maximun distance
tmid = 'NONE     '                      # glider ID obtaining max altitude
tmsta = '         '                     # station capturing max altitude
tmstd = '         '                     # station capturing max distance

fsllo = {'NONE  ': 0.0}      		# station location longitude
fslla = {'NONE  ': 0.0}      		# station location latitude
fslal = {'NONE  ': 0.0}      		# station location altitude
fslod = {'NONE  ': (0.0, 0.0)}          # station location - tuple
fsmax = {'NONE  ': 0.0}                 # maximun coverage
fsalt = {'NONE  ': 0}                   # maximun altitude
fscnt = {'NONE  ': 0}                   # station counter

fsour = {}			 	# sources

# --------------------------------------#
if (MySQL):
    import MySQLdb                  	# the SQL data base routines^M
    conn = MySQLdb.connect(host=DBhost, user=DBuser,
                           passwd=DBpasswd, db=DBname)
    print("MySQL Database:", DBname, " at Host:", DBhost)
else:
    import sqlite3                  	# the SQL data base routines^M
    DBase = DBpath+'SWiface.db'		# Data base used
    conn = sqlite3.connect(DBase)  	# connect with the database
    print("SQLITE3 Database: ",  DBase)
# --------------------------------------#

curs = conn.cursor()                    # set the cursor
#
#-----------------------------------------------------------------
# Initialise API for computing sunrise and sunset
#-----------------------------------------------------------------
#
location = ephem.Observer()
location.pressure = 0
location.horizon = '-0:34'      	# Adjustments for angle to horizon

location.lat, location.lon = location_latitude, location_longitude
date = datetime.now()
next_sunrise = location.next_rising(ephem.Sun(), date)
next_sunset = location.next_setting(ephem.Sun(), date)
print("Sunrise today is at: ", next_sunrise, " UTC ")
print("Sunset  today is at: ", next_sunset,  " UTC ")
print("Time now is: ", date, " Local time")

prtreq = sys.argv[1:]
if prtreq and prtreq[0] == 'prt':
    prt = True
else:
    prt = False
if OGNT:				# if we need aggregation of FLARM and OGN trackers data
    ognttable = {}			# init the instance of the table
    					# build the table from the TRKDEVICES DB table
    ogntbuildtable(conn, ognttable, prt=True)
    print(ognttable)

					# create socket & connect to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((config.APRS_SERVER_HOST, config.APRS_SERVER_PORT))
print("Socket sock connected")

					# logon to OGN APRS network
compfile = config.cucFileLocation + "/competitiongliders.lst"
# if we have a COMP file with the list of flarm ids, pass that to the APRS at login time
if os.path.isfile(compfile):
    fd = open(compfile, 'r')  		# open and read the file
    j = fd.read()
    clist = json.loads(j)
    fd.close()				# close it
    filter = "filter b/"  		# prepare the fileter param of login
    for f in clist:			# explore the whole list
        filter += f  			# add the flarm id
        filter += "/"  			# separated by an slash

    if OGNT:
        for f in ognttable:
            filter += f  		# add the flarm id
            filter += "/"  		# separated by an slash

    if hostname == "CHILEOGN" or hostname == "OGNCHILE":
        filter += " p/SC/VITACURA/ROBLE/ELBOSQUE/TROCA/WBUX/COLORA/SANRA/OLMUE \n"
    else:
        filter += " p/LF/LE/ \n"  	# add all the station of france and Spain for control
    login = 'user %s pass %s vers Silent-Wings-Interface %s %s' % (config.APRS_USER, config.APRS_PASSCODE, pgmversion, filter)
else:
    login = 'user %s pass %s vers Silent-Wings-Interface %s %s' % (config.APRS_USER, config.APRS_PASSCODE, pgmversion, config.APRS_FILTER_DETAILS)
print("APRS login:", login)  		# print the login for control
login=login.encode(encoding='utf-8', errors='strict') 
sock.send(login)    			# login into the APRS server

					# Make the connection to the server
sock_file = sock.makefile(mode='rw')

print("APRS Version:", sock_file.readline())
sleep(2)
					# for control print the login sent and get the response
print("APRS Login request:", login)
print("APRS Login reply:  ", sock_file.readline())

start_time = time.time()  		# get the start and local times
local_time = datetime.now()
fl_date_time = local_time.strftime("%y%m%d")

if os.path.exists(DBpath):
   OGN_DATA = DBpath + "DATA" + fl_date_time+'.log'  # this is the LOG file
else:
   OGN_DATA = "DATA" + fl_date_time+'.log'  # this is the LOG file

print("OGN data file is: ", OGN_DATA)
datafile = open(OGN_DATA, 'a')		# append the data
keepalive_count = 1			# number of keep alive messages
					# every 3 minutees we send a keep alive message to the APRS server
keepalive_time = time.time()
					# and we create a SWS.alive file for control that we are alive as well
alive(config.APP, first="yes")
#
#-----------------------------------------------------------------
#-----------------------------------------------------------------
#
now = datetime.utcnow()			# get the UTC time
min5 = timedelta(seconds=300)		# 5 minutes ago
now = now-min5				# now less 5 minutes
# number of seconds until beginning of the day 1-1-1970
td = now-datetime(1970, 1, 1)
ts = int(td.total_seconds())		# Unix time - seconds from the epoch
spispotcount = 1				# loop counter
ttime = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # format required by SPIDER


date = datetime.now()

#
#-----------------------------------------------------------------
# Initialise API for computing sunrise and sunset
#-----------------------------------------------------------------
#
location = ephem.Observer()
location.pressure = 0
location.horizon = '-0:34'		# Adjustments for angle to horizon

try:

    while True:
        # check the localtime for this location...
        location.date = ephem.Date(datetime.utcnow())
        date = datetime.utcnow()	# time of the server
        localdate = datetime.now()	# time of the server
        # if it is past the sunset or 22:00h local time ??
        if location.date > next_sunset or localdate.hour > 21:

            print("At Sunset now ... Time is (server):", date, "UTC. Location time:",
                  location.date, "UTC ... Next sunset is: ", next_sunset,  " UTC")
            shutdown(sock, datafile, tmaxa, tmaxt, tmid, tmstd)
            print("At Sunset ... Exit\n\n", localdate)
            exit(0)

        # Loop for a long time with a count

        current_time = time.time()
        elapsed_time = current_time - keepalive_time
        if (current_time - keepalive_time) > 180:        # keepalives every 3 mins
            try:
                rtn = sock_file.write("# Python SWSiface App\n\n")
                # Make sure keepalive gets sent. If not flushed then buffered
                sock_file.flush()			# force to write the data
                datafile.flush()	 		# use this ocassion to flush as well the data file
                alive(config.APP)			# indicate that we are alive
                run_time = time.time() - start_time  	# get the run time
                if prt:
                    print("Send keepalive no#: ", keepalive_count, " After elapsed_time: ", int((current_time - keepalive_time)), " After runtime: ", int(run_time), " secs")
                keepalive_time = current_time
                keepalive_count += 1			# keep alive counter and shutdown indicator if -1

            except Exception as e:

                print(('Something\'s wrong with socket write. Exception type is %s' % (repr(e))))
                print("Socket error:", keepalive_count, current_time)
                if keepalive_count != -1:		# check if we are at shutdown now
                    keepalive_count = -1		# indicate shutdown now
                    shutdown(sock, datafile, tmaxa, tmaxt, tmid, tmstd)
                print("At socket error ... Exit\n\n")
                exit(-1)

            try:					

                if OGNT:				# if we need aggregation of FLARM and OGN trackers data
                    					# rebuild the table from the TRKDEVICES DB table
                    ogntbuildtable(conn, ognttable, prt)

            except Exception as e:			# if we have an error during the aggregation functions
                print(('Something\'s wrong with interface functions Exception type is %s \n\n' % (repr(e))))
                nerr += 1


# ------------------------------------------------------- main loop ------------------------------------- #

        if prt:
            print("In main loop. Count= ", i)
            i += 1
        try:
            # Read packet string from socket
            packet_str = sock_file.readline()

            if len(packet_str) > 0 and packet_str[0] != "#":
                datafile.write(packet_str)

        except socket.error:
            print("Socket error on readline")
            nerr += 1
            if nerr > 20:
                print("Socket error multiple  Failures.  Orderly closeout, keep alive count:", keepalive_count)
                date = datetime.now()
                print("UTC now is: ", date, "Bye ...\n\n")
                break
            else:
                sleep(5)				# sleep for 5 seconds and give it another chance
                continue
        # A zero length line should not be return if keepalives are being sent
        # A zero length line will only be returned after ~30m if keepalives are not sent
        if len(packet_str) == 0:
            nerr += 1
            if nerr > 20:
                print("Multiple Read returns zero length string. Failure.  Orderly closeout, keep alive count:", keepalive_count)
                date = datetime.now()
                print("UTC now is: ", date, "Bye ...\n\n")
                break
            else:
                sleep(5)				# sleep for 5 seconds and give it another chance
                continue
        if prt:
            print("DATA:", packet_str)			# print the data received
        ix = packet_str.find('>')			# convert to uppercase the ID
        cc = packet_str[0:ix]				# just the ID
        cc = cc.upper()
        packet_str = cc+packet_str[ix:]			# now with the ID in uppercase
        msg = {}					# create the dict
        # only in case that is data coming
        if len(packet_str) > 0 and packet_str[0] != "#":

            						# parse the message into the dict
            try:
            	msg = parseraprs(packet_str, msg)	# parse data using ogn_parser
            except exception as e:
                print ("Parser error: >>>", e, packet_str, "<<<")
                continue
            if msg == -1:
                print ("Parser error: >>>",  packet_str, "<<<")
                continue
            if prt:
                print("Parsed msg:>>>", msg)
            id = 	msg['id']                      	# id
            aprstype = 	msg['aprstype']			# aprs message type
            longitude = msg['longitude']		# and so on ...
            latitude = 	msg['latitude']
            altitude = 	msg['altitude']
            path = 	msg['path']			# beacon type flarm, trackers, aprs_receiver, etc, ...
            beacontype=path
            relay = 	msg['relay']			# relay type TCPIP, tracker
            station = 	msg['station']			# station name
            if not oksta(station):			# if not a real station
                continue
            otime = 	msg['otime']			# timestamp
            source = 	msg['source']			# source OGN/SPOT/FANET 
            if len(source) > 4:
                source = source[0:3]
            if 'acfttype' in msg:
               acftt=msg['acfttype']
               if not acftt in acfttype:
                  acfttype.append(acftt)

            # if std records
            if ( relay == 'RELAY*' or relay[0:3] == "OGN"):
                if relay[0:3] == "OGN" and prt:
                    print("RELAY:", beacontype, station)
            data = packet_str
            if not id in fid:                  		# if we did not see the FLARM ID
                fid[id] = 0                       	# init the counter
                fidtm[id] = otime                      	# init the time
                					# init the station receiver
                fsta[id] = station
                fmaxa[id] = altitude              	# maximun altitude
                fmaxs[id] = 0                     	# maximun speed
                fmaxd[id] = 0.0	                	# maximun distance
                nids += 1                       	# one more ID found
            else:
                fid[id] += 1				# increase the counter
            if not source in fsour:		    	# did we see this source before
                fsour[source] = 1		    	# init the counter
            else:
                fsour[source] += 1		    	# increase the counter

            if (beacontype == 'aprs_receiver' or relay == 'TCPIP')  and aprstype == 'position':	# handle the TCPIP
                ccchk=id[0:4]                           # just the first 4 chars
                if ccchk =="BSKY" or ccchk == "FNB1" or ccchk == "AIRS":    # useless stations
                    continue				# nothing to do

                if not id in fslod:			# do we have that staion before ?
                    fslla[id] = latitude		# save the location of the station
                    fsllo[id] = longitude		# save the location of the station
                    fslal[id] = altitude		# save the location of the station
                    					# save the location of the station
                    fslod[id] = (latitude, longitude)
                    					# initial coverage distance is zero
                    fsmax[id] = 0.0
                    					# initial coverage altitude is zero
                    fsalt[id] = 0
                    fscnt[id] = 0                  	# initial counter of fixes
                    status = msg['status']		# station status
                    if 'temp' in msg:			# in case of release < 0.2.6 
                        temp = msg['temp']		# station temperature
                    else:
                        temp=-1
                    if 'version' in msg:
                        version = msg['version']	# station SW version
                    else:
                        version = ' '
                    if 'cpu' in msg:                    # station CPU load
                        cpu = msg['cpu']	        # CPU load
                    else:
                        cpu = ' '
                    if 'rf' in msg:                     # 
                        rf = msg['rf']	                # RF sensitibity load
                    else:
                        rf = ' '
                    print("===>STA:", id, latitude, longitude, altitude, ":", version, cpu, rf, ":::", status, ":", aprstype,":")
                    if id[0:3] == "OGN":		# trap !!!
                        print ("===>MSG:", msg) 
                continue                        	# go for the next record
							# check for tracker status
            if aprstype == 'status' and beacontype== "tracker" :	# if tracker status report
                if prt:
                    print("OGN tracker Status report:", data)
                continue
							# check for the station status report ... ignore them
            if beacontype == 'aprs_receiver' or path == 'receiver' or relay =='TCPIP':
                continue				# the case of the TCPIP as well
            						# if std records
            if beacontype == 'tracker'  and ( relay == 'RELAY*' or relay[0:3] == "OGN"):
                station = msg['station']
                fsta[id] = station                	# init the station receiver
#
#							normal position records
#
            course = 	msg['course']			# heading
            speed = 	msg['speed']
            uniqueid = 	msg['uniqueid']
            if len(uniqueid) > 16:
                uniqueid = uniqueid[0:16]		# limit to 16 chars
            extpos = 	msg['extpos']
            roclimb = 	msg['roclimb']			# rate of climb
            rot = msg['rot']
            sensitivity = msg['sensitivity']
            gps = 	msg['gps']
            hora = 	msg['time']			# fix time
            altim = altitude                          	# the altitude in meters
            						# filter by latitude
            if config.FILTER_LATI1 > 0:			# if we are in the norther hemisfere
                if (chkfilati(latitude, config.FILTER_LATI1, config.FILTER_LATI2) and chkfilati(latitude, config.FILTER_LATI3, config.FILTER_LATI4)):
                    continue			        # if is not within our latitude ignore the data
            if (blackhole(longitude, latitude)):
                print("BH:", id, longitude, latitude, date)
                continue				# if is not within our latitude ignore the data

            try:
                if altitude >= fmaxa[id]:		# check for maximun altitude
                 fmaxa[id] = altitude
                 if altitude > tmaxa and (not spanishsta(id) and not frenchsta(id)):
                    tmaxa = altitude        	        # maximum altitude for the day
                    tmaxt = date            	        # and time
                    tmid = id              	        # who did it
                    tmsta = station         	        # station capturing the max altitude
            except:
                print ("TTTT>>>>", msg)                 # trap: check it out
                continue
            try:
                if speed >= fmaxs[id]:			# check for maximun speed
                     fmaxs[id] = speed
            except:
                print ("TTTT>>>>", msg)                 # trap: check it out
                continue
            if altim > 15000 or altim < 0:
                altim = 0
            alti = '%05d' % altim                 	# convert it to an string
            dist = -1					# -1 means station not found, that is the case of receiving fixes before station
            if station in fslod:                	# if we have the station yet
                					# distance to the station
                distance = geodesic((latitude, longitude), fslod[station]).km
                dist = distance
                if distance > 299.9:			# posible errors
                    print("===> Distcheck: ", distance, data)
                elif distance > fsmax[station]: 	# if higher distance
                    fsmax[station] = distance     	# save the new distance
                if altim > fsalt[station]:  		# if higher altitude
                    fsalt[station] = altim    		# save the new altitude
                if distance > tmaxd:			# if exceed maximun distance
                    tmaxd = distance			# maximun distance today
                    tmstd = station			# station with the maximun distance
                if distance > fmaxd[id]:		# if distance is higher
                    fmaxd[id] = distance		# save the new distance
                fscnt[station] += 1			# increase the counter of fixes
            if source != "OGN":				# if it is not OGN, we get the distance to the home base
                distance = geodesic((latitude, longitude), (config.location_latitude,config.location_longitude)).km    # distance to the base
                dist = distance
            if altim > tmaxa:				# if exceed the maximun altitude
                tmaxa = altim               		# maximum altitude for the day
                tmaxt = hora                		# and time
                tmid = id                  		# who did it
                tmsta = station             		# station capturing the max altitude
            if prt:
                print('Parsed data: POS: ', longitude, latitude, altitude, ' Speed:',
                      speed, ' Course: ', course, ' Path: ', beacontype, ' Type:', aprstype)
                print(roclimb, rot, sensitivity, gps, uniqueid, dist, extpos, source)
            if rot == ' ':
                rot = 0
            if sensitivity == ' ':
                sensitivity = 0
            						# if we have OGN tracker aggregation and is an OGN tracker
            if OGNT and id[0:3] == 'OGN':
                if id in ognttable:			# if the device is on the list
                    					# substitude the OGN tracker ID for the related FLARMID
                   id = ognttable[id]			# do the change before record on the DDBB
            						# write the DB record
            if source == "SPOT":			# if SPOT ignore it !!
                continue
#
#							Store the fix/location information on the DDBB
#
            if (MySQL):					# if using MySQL ???
                addcmd = "insert into OGNDATA values ('" + id + "','" + dte + "','" + hora + "','" + station + "'," + str(latitude) + "," +\
                         str(longitude) + "," + str(altim) + "," + str(speed) + "," + \
                         str(course) + "," + str(roclimb) + "," + str(rot) + "," + str(sensitivity) + \
                    ",'" + gps + "','" + uniqueid + "'," + \
                    str(dist) + ",'" + extpos + "','"+source+"')"
                try:
                    curs.execute(addcmd)            	# add the data to the DDBB
                except MySQLdb.Error as e:
                    try:
                        print(">>>MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                    except IndexError:
                        print(">>>MySQL Error: %s" % str(e))
                    print(">>>MySQL error:", nrecs, addcmd)
            else:					# using SQLite3
                addcmd = "insert into OGNDATA values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
                curs.execute(addcmd, (id, dte, hora, station, latitude, longitude, altim, speed,
                                      course, roclimb, rot, sensitivity, gps, uniqueid, dist, extpos, source))
            if prt:
                print(addcmd)
            conn.commit()                       	# commit the DB updates
            nrecs += 1                             	# one more record written
# end of while loop

except KeyboardInterrupt:
    print("Keyboard input received, ignore")
    pass
#							# if break of the while loop ... exit
							# report number of records read and files generated
print('Counters:', nrecs, nids)				# number of fix written and number of flarms seeing ...
shutdown(sock, datafile, tmaxa, tmaxt, tmid, tmstd)
location.date = ephem.Date(datetime.utcnow())
print("Exit now ...", location.date, "\n\n")
if nerr > 0:
    print("Number of errors:", nerr)
exit(1)
