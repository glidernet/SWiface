#!/bin/sh
cd /nfs/OGN/SWdata
date >>SWproc.log
echo $(hostname)" running SWlive:"		>>SWproc.log
python3 ~/src/SWsrc/SWcalsunrisesunset.py 	>>SWproc.log 
python3 ~/src/SWsrc/SWiface.py   	 	>>SWproc.log &
