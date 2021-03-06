#!/bin/bash 
echo								#
echo " "							#
echo "Installing the Silent Wings Studio interface ...." 	#
echo "========================================================" #
echo " "							#
echo								#
if [ $# = 0 ]; then						
	sql='NO'
else
	sql=$1
fi
bash commoninstall.sh $sql					#
sudo cat /etc/apache2/apache2.conf html.dir 	>>temp.conf	#
sudo echo "ServerName SWserver  " >>temp.conf			#
sudo mv temp.conf /etc/apache2/apache2.conf			#
sudo service apache2 restart					#
echo "  -------------------- APACHE restarted ---------------"	#
cd /var/www/html/main						#
echo								#
echo " "							#
echo "========================================================" #
echo " "							#
echo								#
if [ $sql = 'MySQL' ]			
then	
   echo "Type ROOT old password: "				#
   echo " "							#
   echo "========================================================" #
   echo "ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'ognognogn';" | sudo mysql -u root -p #
   echo "Type ROOT new password: "				#
   echo " "							#
   echo "========================================================" #
   echo "SELECT user,authentication_string,plugin,host FROM mysql.user; " | sudo mysql -u root -p #
   echo								#
   echo " "							#
   mysql_config_editor print --all				#
fi
if [ ! -d /etc/local ]						#
then								#
    sudo mkdir /etc/local					#
fi								#
if [ ! -d ~/src  ]						#
then								#
	mkdir ~/src   						#
	ln -s $(pwd) ~/src/SWsrc				#
fi								#
echo " "							#
echo " DIR: /src ..."						#
echo "================================================" 	#
ls -la ~/src							#
echo " DIR: /src/SWsrc ..."					#
echo "================================================" 	#
ls -la ~/src/SWsrc						#
echo " DIR: /src/SWsrc/sh ..."					#
echo "================================================" 	#
ls -la ~/src/SWsrc/sh						#
echo "================================================" 	#
echo " "							#
echo "Installing the templates needed  ...." 			#
echo "========================================================" #
echo " "							#
echo								#
cd /var/www/html/main						#
sudo cp config.template /etc/local/SWSconfig.ini		#
cd /var/www/html/						#
cp configtail.template configtail.txt				#
python3 genconfig.py						#
ls -la								#
echo								#
echo " "							#
echo "Setting the data bases       ...." 			#
echo "========================================================" #
echo " "							#
echo								#
if [ -f SWiface.db ]						#
then								#
	rm      SWiface.db					#
fi								#
if [ ! -d cuc    ]						#
then								#
	mkdir cuc     						#
	chmod 777 cuc     					#
	mkdir cuc/TSKF  					#
	chmod 777 cuc/TSKF  					#
fi								#
cd /var/www/html/						#
sqlite3 SWiface.db         < main/DBschema.sqlite3		#
if [ -d /nfs/OGN/SWdata  ]					#
then								#
	mv      SWiface.db  	/nfs/OGN/SWdata			#
fi								#
echo " "							#
echo "========================================================" #
echo "Create the MySQL database SWIFACE "			#
echo "========================================================" #
echo "Running msqladmin .... assign root password ... "		#
sudo mysqladmin -u root password ogn				#
if [ $sql = 'MySQL' ]	
then			
        echo "Create the APRSogn login-path: Type assigned password"	#
	mysql_config_editor set --login-path=APRSogn --user=ogn --password
fi
cd /var/www/html/main						#
cp doc/.my.cnf ~/						#
echo "Create user ogn ..."					#
echo "========================================================" #
sudo mysql  <doc/adduser.sql					#
if [ $sql = 'MySQL' ]			
then								#
	echo "CREATE DATABASE if not exists SWIFACE" | mysql --login-path=APRSogn	#
else
	echo "CREATE DATABASE if not exists SWIFACE" | mysql -u ogn -pogn	
fi
if [ $sql = 'MySQL' ]			
then								#
    mysql --login-path=APRSogn --database SWIFACE <DBschema.sql #
else
    mysql -u ogn -pogn --database SWIFACE <DBschema.sql   	#
fi
cd /tmp
wget acasado.es:60080/files/GLIDERS.sql
mysql -u ogn -pogn  SWIFACE </tmp/GLIDERS.sql
cd /var/www/html/main						#
if [ $sql = 'docker' ]			
then			
   echo "Create DB in docker ogn ..."				#
   echo "========================================================" #
   echo "CREATE DATABASE if not exists SWIFACE" | sudo mysql -u ogn -pogn -h MARIADB
   echo "SET GLOBAL log_bin_trust_function_creators = 1; " | sudo mysql -u ogn -pogn -h MARIADB
   sudo mysql -u ogn -pogn -h MARIADB --database SWIFACE <DBschema.sql 
   sudo mysql -u ogn -pogn -h MARIADB --database SWIFACE </tmp/GLIDERS.sql
fi
rm /tmp/GLIDERS.sql
echo " "							#
echo "Optional steps ... "					#
echo "========================================================" #
echo " "							#
echo								#
cd /var/www/html/main						#
cp aliases ~/.bash_aliases					#
cd sh	 							#
crontab <crontab.data						#
crontab -l 							#
if [ ! -d ~/src  ]						#
then								#
	mkdir ~/src   						#
	mkdir ~/src/SWsrc					#
	ln -s /var/www/html/main ~/src/SWsrc			#
fi								#
ls  -la ~/src 							#
if [ ! -d /nfs  ]						#
then								#
	echo							#
	echo "Adding user ogn ...	"			#
	echo "=============== ...	"			#
	sudo adduser ogn 					#
	sudo mkdir /nfs						#
	sudo mkdir /nfs/OGN					#
	sudo mkdir /nfs/OGN/SWdata				#
	sudo chown ogn:ogn /nfs/OGN/SWdata			#
	sudo chmod 777 /nfs/OGN/SWdata				#
	cd /var/www/html/					#
	mv SWiface.db /nfs/OGN/SWdata				#
	sudo chown ogn:ogn *					# 
	sudo chmod 777 *					#
	sudo chown ogn:ogn */*					# 
	sudo chmod 777 */*					#
fi								#
echo " "							#
echo "========================================================" #
echo " "							#
cd /var/www/html 						#
if [ ! -f /usr/local/bin/calcelestial ]				#
then								#
	cd main/sh						#
	sh calcelestial.sh					#
	calcelestial -h 					#
fi								#
cd								#
sudo chmod 755 /var/log/syslog					#
touch SWinstallation.done					#
echo " "							#
echo								#
echo "========================================================================================================"	#
echo "Installation done ..."											#
echo "Review the configuration file on /etc/local and the config tail file configtail.txt  ..."			#
echo "Review the configuration of the crontab and the shell scripts on ~/src " 					#
echo "In order to execute the Silent Wings data crawler execute:  bash ~/src/SWlive.sh " 			#
echo "Check the placement of the RootDocument on APACHE2 ... needs to be /var/www/html"				#
echo "If running in Windows under Virtual Box, run dos2unix on /var/www/html & ./main & ~/src"			#
echo "Run the utilities soa2sws.py and/or sgp2sws.py in order to extract the data from SoaringSpot.com or SGP"  #
echo "Install phpmyadmin if needed !!! "                                                                        #
echo "========================================================================================================"	#
echo								#
echo " "							#
tail /var/log/syslog						#
sudo apt-get -y dist-upgrade					#
sudo apt-get -y autoremove					#
