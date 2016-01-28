create table mipas_scan(
 species varchar,
 file varchar,
 file_index int,
 latitude real,
 longitude real,
 mjd double precision,
 created timestamp default current_timestamp,
 constraint pk_mipas_scan primary key (species, file, file_index)
);


create table mls_scan(
 species varchar,
 file varchar,
 file_index int,
 latitude real,
 longitude real,
 mjd double precision,
 created timestamp default current_timestamp,
 constraint pk_mls_scan primary key (species, file, file_index)
);


create table collocations(
 Date date,
 FreqMode int,
 Backend varchar,
 ScanID bigint,
 AltEnd real,
 AltStart real,
 LatEnd real,
 LatStart real,
 LonEnd real,
 LonStart real,
 MJDEnd double precision,
 MJDStart double precision,
 NumSpec int,
 SunZD real,
 DateTime timestamp,
 Latitude real,
 Longitude real,
 MJD double precision,
 Instrument varchar,
 Species varchar,
 File varchar,
 File_Index int,
 DMJD real,
 DTheta real,
 created timestamp default current_timestamp,
 constraint pk_collocations_scan primary key (Backend, Freqmode, ScanID, File, File_Index)
);



create table scans_cache(
 Date date,
 FreqMode int,
 Backend varchar,
 ScanID bigint,
 AltEnd real,
 AltStart real,
 LatEnd real,
 LatStart real,
 LonEnd real,
 LonStart real,
 MJDEnd double precision,
 MJDStart double precision,
 NumSpec int,
 SunZD real,
 DateTime timestamp,
 created timestamp default current_timestamp,
 constraint pk_scans_cache primary key (Date, Freqmode, ScanID)
);


