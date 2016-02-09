FTP_SERVER="ftp://acdisc.gsfc.nasa.gov"
USER="anonymous"
PASSWORD="bengt.rydberg@molflow.com"

LOCALSTORAGE="/odin/external/vds-data/Aura_MLS_Level2/ClO/v04/"

for year in {2004..2015..1}
do
  for month in {01..12..1}
  do
    for day in {01..31..1}
    do
      if [ "${year}" != "2016" ]    
      then
        doy=$(date -u -d "${year}-${month}-${day}" "+%j") 
        errorcode=$?
        if [ $errorcode == 0 ]
        then
          echo $doy $errorcode
          filepath="/data/s4pa/Aura_MLS_Level2/ML2CLO.004/${year}"
          file="MLS-Aura_L2GP-ClO_v04-20-c01_${year}d${doy}.he5"
          URL="${FTP_SERVER}:${filepath}/${file}"
          LOCALDIR="${LOCALSTORAGE}/${year}/${month}/"
          mkdir -p $LOCALDIR
          wget --user=$USER --password=$PASSWORD --directory-prefix=$LOCALDIR $URL 
        fi
      fi
    done
  done 
done




