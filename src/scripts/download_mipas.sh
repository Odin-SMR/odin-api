FTP_SERVER="http://share.lsdf.kit.edu"
USER="rydberg"
PASSWORD="work8smi"


for species in {"CO","H2O","HNO3","N2O","NO"}
do
  for year in {2002..2012..1}
  do
    for month in {01..12..1}
    do
      if [ "${year}" != "2015" ]  
      then
        LOCALSTORAGE="/odin/external/vds-data/Envisat_MIPAS_Level2/${species}/V5"
        month_str=$(date -u -d "${year}-${month}-01" "+%b")
        month_str="${month_str^}"
        for i in {"V5H","V5R"}
        do
          for j in {"20","21","22","220","221","222","223","224","225"}
          do
            filepath="imk/asf/sat/mipas-export/Data_by_Target/${species}/${year}/${month}_${month_str}"
            file="MIPAS-E_IMK.${year}${month}.${i}_${species}_${j}.nc"
            URL="${FTP_SERVER}/${filepath}/${file}"
            LOCALDIR="${LOCALSTORAGE}/${year}/${month}/"
            echo ${URL}
            mkdir -p $LOCALDIR
            wget --user=$USER --password=$PASSWORD --directory-prefix=$LOCALDIR $URL
          done
        done 
      fi
    done 
  done
done

