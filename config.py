#-------------------------------------
# OGN-SWS Spain interface --- Settings
#-------------------------------------
#
#-------------------------------------
# Setting values
#-------------------------------------
#
import socket
from configparser import ConfigParser
configfile="/etc/local/SWSconfig.ini"
hostname=socket.gethostname()
cfg=ConfigParser()                                                              # get the configuration parameters
cfg.read(configfile)                                                            # reading it for the configuration file

APRS_SERVER_HOST        = cfg.get    ('APRS', 'APRS_SERVER_HOST').strip("'")
APRS_SERVER_PORT        = int(cfg.get('APRS', 'APRS_SERVER_PORT'))
APRS_USER               = cfg.get    ('APRS', 'APRS_USER').strip("'")
APRS_PASSCODE           = int(cfg.get('APRS', 'APRS_PASSCODE'))                 # See http://www.george-smart.co.uk/wiki/APRS_Callpass
APRS_FILTER_DETAILS     = cfg.get    ('APRS', 'APRS_FILTER_DETAILS').strip("'")
APRS_FILTER_DETAILS     = APRS_FILTER_DETAILS + '\n '

location_latitude       = cfg.get('location', 'location_latitude').strip("'")
location_longitude      = cfg.get('location', 'location_longitud').strip("'")
FLOGGER_LATITUDE        = cfg.get('location', 'location_latitude').strip("'").strip('"')
FLOGGER_LONGITUDE       = cfg.get('location', 'location_longitud').strip("'").strip('"')

FILTER_LATI1            = float(cfg.get('filter', 'FILTER_LATI1'))
FILTER_LATI2            = float(cfg.get('filter', 'FILTER_LATI2'))
FILTER_LATI3            = float(cfg.get('filter', 'FILTER_LATI3'))
FILTER_LATI4            = float(cfg.get('filter', 'FILTER_LATI4'))


try:
	location_name   = cfg.get('location', 'location_name').strip("'").strip('"')
except:
	location_name   = ' '
try:
	SPOTtext        = cfg.get('location', 'SPOT').strip("'").strip('"')
except:
	SPOTtext='False'
try:
	LT24text        = cfg.get('location', 'LT24').strip("'").strip('"')
	LT24username    = cfg.get('location', 'LT24username').strip("'").strip('"')
	LT24password    = cfg.get('location', 'LT24password').strip("'").strip('"')
except:
	LT24text='False'
try:
	SPIDERtext      = cfg.get('location', 'SPIDER').strip("'").strip('"')
	SPIuser         = cfg.get('location', 'SPIuser').strip("'").strip('"')
	SPIpassword     = cfg.get('location', 'SPIpassword').strip("'").strip('"')
except:
	SPIDERtext='False'
try:
	SKYLINEtext     = cfg.get('location', 'SKYLINE').strip("'").strip('"')
except:
	SKYLINEtext='False'

DBpath                  = cfg.get('server', 'DBpath').strip("'")
MySQLtext               = cfg.get('server', 'MySQL').strip("'")
DBhost                  = cfg.get('server', 'DBhost').strip("'")
DBuser                  = cfg.get('server', 'DBuser').strip("'")
DBpasswd                = cfg.get('server', 'DBpasswd').strip("'")
DBname                  = cfg.get('server', 'DBname').strip("'")
# -------------------------------------------------------------------------------#
APP='SWS'
if (MySQLtext == 'True'):
        MySQL = True
else:
        MySQL = False
if (SPIDERtext == 'True'):
        SPIDER = True
else:
        SPIDER = False
if (SPOTtext == 'True'):
        SPOT = True
else:
        SPOT = False
if (LT24text == 'True'):
        LT24 = True
else:
        LT24 = False
if (SKYLINEtext == 'True'):
        SKYLINE = True
else:
        SKYLINE = False
# --------------------------------------#
assert len(APRS_USER) > 3 and len(str(APRS_PASSCODE)) > 0, 'Please set APRS_USER and APRS_PASSCODE in settings.py.'
 
# --------------------------------------#
						# report the configuration paramenters
print "Config server values:",                  "MySQL=", MySQL, DBhost, DBuser, DBpasswd, DBname, DBpath
print "Config APRS values:",                    APRS_SERVER_HOST, APRS_SERVER_PORT, APRS_USER, APRS_PASSCODE, APRS_FILTER_DETAILS
print "Config location :",     			location_name, location_latitude, location_longitude, "SPIDER=", SPIDER, "SPOT=", SPOT, "LT24=", LT24, "SKYLINE=", SKYLINE
# --------------------------------------#

