#!/bin/bash 
cd /nfs/OGN/SWdata 
cp SWiface.db archive/SWiface.Y$(date +%y).db
sqlite3 -echo SWiface.db "vacuum;"
mkdir archive/Y$(date +%y)
cd

