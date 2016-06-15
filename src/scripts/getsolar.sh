#! /bin/bash -ue
year=`date +%Y -d '-5 years'`
curl -o /var/lib/odindata/sw.txt http://www.celestrak.com/SpaceData/sw${year}0101.txt 
processsolar
