FTP_SERVER="http://share.lsdf.kit.edu"
USER="rydberg"
PASSWORD="work8smi"

LOCALSTORAGE="/home/bengt/work/odin_reprocessing/vds/data/mipas/O3/V5R"


for year in {2006..2015..1}
do
  for month in {00..12..1}
  do
    if [ "${year}" == "2012" ] && [ "${month}" == "01" ]  
    then
      month_str=$(date -u -d "${year}-${month}-01" "+%b")
      month_str="${month_str^}"
      filepath="imk/asf/sat/mipas-export/Data_by_Target/O3/${year}/${month}_${month_str}"
      file="MIPAS-E_IMK.${year}${month}.V5R_O3_225.nc"
      URL="${FTP_SERVER}/${filepath}/${file}"
      LOCALDIR="${LOCALSTORAGE}/${year}/${month}/"
      echo ${URL}
      mkdir -p $LOCALDIR
      wget --user=$USER --password=$PASSWORD --directory-prefix=$LOCALDIR $URL 
    fi
  done 
done




