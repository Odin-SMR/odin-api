FTP_SERVER="ftp://acdisc.gsfc.nasa.gov"
USER="anonymous"
PASSWORD="bengt.rydberg@molflow.com"

LOCALSTORAGE="/home/bengt/work/odin_reprocessing/vds/data/mls/O3/v04/"


for year in {2006..2015..1}
do
  for month in {00..12..1}
  do
    for day in {01..31..1}
    do
      if [ "${year}" == "2015" ] && [ "${month}" == "01" ]  
      then
        doy=$(date -u -d "${year}-${month}-${day}" "+%j")
        filepath="/data/s4pa/Aura_MLS_Level2/ML2O3.004/${year}"
        file="MLS-Aura_L2GP-O3_v04-20-c01_2015d${doy}.he5"
        URL="${FTP_SERVER}:${filepath}/${file}"
        LOCALDIR="${LOCALSTORAGE}/${year}/${month}/"
        mkdir -p $LOCALDIR
        wget --user=$USER --password=$PASSWORD --directory-prefix=$LOCALDIR $URL 
      fi
    done
  done 
done




