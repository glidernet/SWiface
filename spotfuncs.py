#!/bin/python
import urllib2
import json
import xml.etree.ElementTree as ET
from ctypes import *
from datetime import datetime, timedelta
import socket
import time
import string
import sys
import os
import signal
from   geopy.distance import vincenty       # use the Vincenty algorithm^M
import MySQLdb                              # the SQL data base routines^M
import config
import kglid


def spotgetapidata(url, prt=False):                      	# get the data from the API server

        req = urllib2.Request(url)		# buil the request
	req.add_header("Content-Type","application/json")
	req.add_header("Content-type", "application/x-www-form-urlencoded")
        r = urllib2.urlopen(req)                # open the url resource
	j_obj = json.load(r)                    # convert to JSON
	if prt:
		print json.dumps(j_obj, indent=4) 
        return j_obj                            # return the JSON object


def spotaddpos(msg, spotpos, ttime, regis, flarmid):	# extract the data from the JSON object

	unixtime=msg["unixTime"] 		# the time from the epoch
	if (unixtime < ttime):
		return (False)			# if is lower than the last time just ignore it
	reg=regis
	lat=msg["latitude"] 			# extract from the JSON object the data that we need
	lon=msg["longitude"] 
	alt=msg["altitude"] 
	id =msg["id"] 
	mid=msg["modelId"] 
	dte=msg["dateTime"] 
	extpos=msg["batteryState"] 
	date=dte[2:4]+dte[5:7]+dte[8:10]
        time=dte[11:13]+dte[14:16]+dte[17:19]
	if 'GOOD' not in msg.get('batteryState', 'GOOD'):
       		print "WARNING: spot battery is in state: %s ID=%s " % (msg.get('batteryState'), regis)
	vitlat   =config.FLOGGER_LATITUDE
	vitlon   =config.FLOGGER_LONGITUDE
	distance=vincenty((lat, lon),(vitlat,vitlon)).km    # distance to the statio
	pos={"registration": flarmid, "date": date, "time":time, "Lat":lat, "Long": lon, "altitude": alt, "UnitID":id, "GPS":mid, "dist":distance, "extpos":extpos}
	spotpos['spotpos'].append(pos)		# and store it on the dict
	print "SPOTPOS :", lat, lon, alt, id, distance, unixtime, dte, date, time, reg, flarmid, extpos
	return (True)				# indicate that we added an entry to the dict

def spotgetaircraftpos(data, spotpos, ttime, regis, flarmid, prt=False):	# return on a dictionary the position of all spidertracks
	response    =data['response']		# get the response entry
	if response.get('errors'):		# if error found
		return(False)			# return indicating errors

	feed        =response["feedMessageResponse"]	# get the message response
	msgcount    =feed['count']		# get the count of messages
	messages    =feed['messages']		# get the messages
	message     =messages['message']	# get the individual message
	found=False
	#print "M:", message
	if msgcount == 1:			# if only one message, that is the message
		if prt:
			print json.dumps(feed, indent=4)        # convert JSON to dictionary
		found=spotaddpos(message, spotpos, ttime, regis, flarmid)
	else:
		for msg in message:		# if not iterate the set of messages
			if prt:
				print json.dumps(msg, indent=4)        # convert JSON to dictionary
			found=spotaddpos(msg, spotpos, ttime, regis, flarmid)
	return (found)				# return if we found a message or not

def spotstoreitindb(datafix, curs, conn):	# store the fix into the database
	for fix in datafix['spotpos']:		# for each fix on the dict
		id=fix['registration'] 		# extract the information
		if len(id) > 9:
			id=id[0:9]
		dte=fix['date'] 
		hora=fix['time'] 
		station=config.location_name
		latitude=fix['Lat'] 
		longitude=fix['Long'] 
		altim=fix['altitude'] 
		speed=0
		course=0
		roclimb=0
		rot=0
		sensitivity=0
		gps=fix['GPS']
		gps=gps[0:6]
		uniqueid=str(fix["UnitID"])
		dist=fix['dist']
		extpos=fix['extpos']
		addcmd="insert into OGNDATA values ('" +id+ "','" + dte+ "','" + hora+ "','" + station+ "'," + str(latitude)+ "," + str(longitude)+ "," + str(altim)+ "," + str(speed)+ "," + \
               str(course)+ "," + str(roclimb)+ "," +str(rot) + "," +str(sensitivity) + \
               ",'" + gps+ "','" + uniqueid+ "'," + str(dist)+ ",'" + extpos+ "', 'SPOT' ) ON DUPLICATE KEY UPDATE extpos = '!ZZZ!' "
        	try:				# store it on the DDBB
              		curs.execute(addcmd)
        	except MySQLdb.Error, e:
              		try:
                     		print ">>>MySQL Error [%d]: %s" % (e.args[0], e.args[1])
              		except IndexError:
                     		print ">>>MySQL Error: %s" % str(e)
                     		print ">>>MySQL error:", cout, addcmd
                    		print ">>>MySQL data :",  data
			return (False)	# indicate that we have errors
        conn.commit()                   # commit the DB updates
	return(True)			# indicate that we have success


def spotfindpos(ttime, conn, prt=False):	# find all the fixes since TTIME

	curs=conn.cursor()              # set the cursor for storing the fixes
	cursG=conn.cursor()             # set the cursor for searching the devices
	cursG.execute("select id, spotid, spotpasswd, active, flarmid, registration from TRKDEVICES where devicetype = 'SPOT'; " ) 	# get all the devices with SPOT
        for rowg in cursG.fetchall(): 	# look for that registration on the OGN database
                                
        	reg=rowg[0]		# registration to report
        	spotID=rowg[1]		# SPOTID
        	spotpasswd=rowg[2]	# SPOTID password
        	active=rowg[3]		# if active or not
        	flarmid=rowg[4]		# Flamd id to be linked
        	registration=rowg[5]	# registration id to be linked
		if active == 0:
			continue	# if not active, just ignore it
		if flarmid == None or flarmid == '': 			# if flarmid is not provided 
			flarmid=spotgetflarmid(conn, registration)	# get it from the registration
		else:
			if flarmid[3:9] not in kglid.kglid: # check that the registration is on the table - sanity check
                		print "Warning: flarmid=", flarmid, "not on kglid table"

					# build the URL to call to the SPOT server
		if spotpasswd == '' or spotpasswd == None:
			url="https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/"+spotID+"/message.json"
		else:
			url="https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/"+spotID+"/message.json?feedPassword="+str(spotpasswd)
		spotpos={"spotpos":[]}				# init the dict
		jsondata=spotgetapidata(url)			# get the JSON data from the SPOT server
		if prt:						# if we require printing the raw data
			j=json.dumps(jsondata, indent=4)	# convert JSON to dictionary
			print j
		found=spotgetaircraftpos(jsondata, spotpos, ttime, reg, flarmid, prt=False)	# find the gliders since TTIME
		spotstoreitindb(spotpos, curs, conn)			# and store it on the DDBB
	
	now=datetime.utcnow()
	td=now-datetime(1970,1,1)       # number of second until beginning of the day of 1-1-1970
	ts=int(td.total_seconds())	# as an integer
	return (ts)			# return TTIME for next call

#-------------------------------------------------------------------------------------------------------------------#

def spotgetflarmid(conn, registration):

	cursG=conn.cursor()             # set the cursor for searching the devices
	try:
		cursG.execute("select idglider, flarmtype from GLIDERS where registration = '"+registration+"' ;")
       	except MySQLdb.Error, e:
           	try:
                   	print ">>>MySQL Error [%d]: %s" % (e.args[0], e.args[1])
              	except IndexError:
                   	print ">>>MySQL Error: %s" % str(e)
                     	print ">>>MySQL error:", "select idglider, flarmtype from GLIDERS where registration = '"+registration+"' ;"
                    	print ">>>MySQL data :",  registration
		return("NOREG") 
        rowg = cursG.fetchone() 	# look for that registration on the OGN database
	if rowg == None:
		return("NOREG") 
       	idglider=rowg[0]		# flarmid to report
       	flarmtype=rowg[1]		# flarmtype flarm/ica/ogn
	if idglider not in kglid.kglid:	# check that the registration is on the table - sanity check
		print "Warning: flarmid=", idglider, "not on kglid table"
	if flarmtype == 'F':
		flarmid="FLR"+idglider 	# flarm 
	elif flarmtype == 'I':
		flarmid="ICA"+idglider 	# ICA
	elif flarmtype == 'O':
		flarmid="OGN"+idglider 	# ogn tracker
	else: 
		flarmid="RND"+idglider 	# undefined
	#print "GGG:", registration, rowg, flarmid
	return (flarmid)
