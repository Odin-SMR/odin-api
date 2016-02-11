#! /bin/bash
FTP_SERVER="ftp://l5eil01.larc.nasa.gov"
USER="anonymous"
PASSWORD="bengt.rydberg@molflow.com"

LOCALSTORAGE="/odin/external/vds-data/Meteor3M_SAGEIII_Level2/v04"

for year in {2002..2005..1}
do
  for month in {00..12..1}
  do
    for day in {01..31..1}
    do
      LOCALDIR="${LOCALSTORAGE}/${year}/${month}/"
      echo ${LOCALDIR}
      mkdir -p $LOCALDIR

      filepath="/SAGE_III/g3assp.004/${year}.${month}.${day}"
      file="g3a.ssp.*v04.00"
      URL="${FTP_SERVER}:${filepath}/${file}"
      echo ${URL}
      wget --user=$USER --password=$PASSWORD --backups=0 \
           --directory-prefix=$LOCALDIR $URL

      filepath="/SAGE_III/g3alsp.004/${year}.${month}.${day}"
      file="g3a.lsp.*v04.00"
      URL="${FTP_SERVER}:${filepath}/${file}"
      echo ${URL}
      wget --user=$USER --password=$PASSWORD --backups=0 \
           --directory-prefix=$LOCALDIR $URL
    done
    for f in ${LOCALDIR}/*.00
    do
      h4toh5 $f
    done
  done
done




