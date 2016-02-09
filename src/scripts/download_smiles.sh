FTP_SERVER="http://darts.isas.jaxa.jp"
USER="anonymous"
PASSWORD="bengt.rydberg@molflow.com"


for species in {"O3","ClO","HNO3"}
do
  for year in {2009..2010..1}
  do
    for month in {01..04..1}
    do
      for day in {01..31..1}
      do
        LOCALSTORAGE="/odin/external/vds-data/ISS_SMILES_Level2/${species}/v2.4/"
        if [ "${year}" != "2009" ]  
        then
          for band in {"A","B","C"}
          do
            filepath="/iss/smiles/data/l2/L2Product/008-11-0502/${band}/${year}${month}/${day}"
            file="SMILES_L2_${species}_${band}_008-11-0502_${year}${month}${day}.he5"
            URL="${FTP_SERVER}:${filepath}/${file}"
            LOCALDIR="${LOCALSTORAGE}${year}/${month}/"
            mkdir -p $LOCALDIR
            wget --user=$USER --password=$PASSWORD --directory-prefix=$LOCALDIR $URL 
          done
        fi
      done
    done 
  done
done


