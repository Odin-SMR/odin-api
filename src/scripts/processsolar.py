#!/usr/bin/env python3.8
from fortranformat import FortranRecordReader
import datetime as DT
import sqlite3 as sqlite
import numpy as np


def processsolar():

    solarfile = '/var/lib/odindata/' + 'sw.txt'
    solar = open(solarfile, 'r')
    line = solar.readline(-1)
    while line != "BEGIN OBSERVED\n":
        line = solar.readline(-1)

    res = FortranRecordReader(
        'I4,I3,I3,I5,I3,8I3,I4,8I4,I4,F4.1,I2,I4,F6.1,I2,5F6.1'
    )
    solardata = []
    line = solar.readline(-1)
    while line != "END OBSERVED\n":
        solardata.append(res.read(line))
        line = solar.readline(-1)

    solardata = np.array(solardata)
    dates = []
    for i in range(solardata.shape[0]):
        dates.append(
            DT.date(
                solardata[i, 0].astype(int),
                solardata[i, 1].astype(int),
                solardata[i, 2].astype(int),
            ),
        )

    # solardata 13=Kpsum 22=APavg 26=f10.7
    while line != "BEGIN DAILY_PREDICTED\n":
        line = solar.readline(-1)
    solardatapred = []
    line = solar.readline(-1)
    while line != "END DAILY_PREDICTED\n":
        solardatapred.append(res.read(line))
        line = solar.readline(-1)
    while line != "BEGIN MONTHLY_PREDICTED\n":
        line = solar.readline(-1)
    line = solar.readline(-1)
    while line != "END MONTHLY_PREDICTED\n":
        solardatapred.append(res.read(line))
        line = solar.readline(-1)
    solardatapred = np.array(solardatapred)

    datespred = []
    for i in range(solardatapred.shape[0]):
        datespred.append(DT.date(
            solardatapred[i, 0].astype(int),
            solardatapred[i, 1].astype(int),
            solardatapred[i, 2].astype(int),
        ))

    solar.close()
    dbfile = '/var/lib/odindata/' + 'Solardata2.db'
    db = sqlite.connect(dbfile)
    cur = db.cursor()

    # cur.execute('create table solardata (ID BIGINT, yy shortint, mm shortint,
    # dd shortint, BSRN shortint, ND shortint, Kp1 shortint, Kp2 shortint,
    # Kp3 shortint, Kp4 shortint, Kp5 shortint, Kp6 shortint, Kp7 short int,
    # Kp8 shortint, KpSum shortint, 	Ap1 shortint,  Ap2 shortint,
    # Ap3 shortint,  Ap4 shortint,  Ap5 shortint,  Ap6 shortint,
    # Ap7 shortint,  Ap8 shortint,  ApAvg shortint,	Cp float, C9 shortint,
    # ISN Integer,  AdjF10_7 float, Q shortint,  AdjCtr81 float,
    # AdjLst81 float, ObsF10_7 float, ObsCtr81 float, ObsLst81 float )')
    instr = 'insert or replace into solardata values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )'  # noqa
    for i in range(solardata.shape[0]):
        ids = (
            solardata[i, 0].astype(int) * 10000
            + solardata[i, 1].astype(int) * 100
            + solardata[i, 2].astype(int)
        )
        cur.execute(instr, np.r_[ids, solardata[i, :]])

    # cur.execute('create table solardatapred (ID BIGINT, pred_date bigint,
    # yy shortint, mm shortint, dd shortint, BSRN shortint, ND shortint,
    # Kp1 shortint, Kp2 shortint, Kp3 shortint, Kp4 shortint, Kp5 shortint
    # Kp6 shortint, Kp7 short int, Kp8 shortint, KpSum shortint, Ap1 shortint,
    # Ap2 shortint, Ap3 shortint,  Ap4 shortint,  Ap5 shortint,  Ap6 shortint,
    # Ap7 shortint,  Ap8 shortint,  ApAvg shortint,  Cp float, C9 shortint,
    # ISN Integer,  AdjF10_7 float, Q shortint, AdjCtr81 float,
    # AdjLst81 float, ObsF10_7 float, ObsCtr81 float, ObsLst81 float )')
    instr = 'insert or replace into solardatapred values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )'  # noqa
    idp = ids
    for i in range(solardatapred.shape[0]):
        ids = (
            idp * 100000000
            + solardatapred[i, 0].astype(int) * 10000
            + solardatapred[i, 1].astype(int) * 100
            + solardatapred[i, 2].astype(int)
        )
        cur.execute(instr, np.r_[ids, idp, solardatapred[i, :]])

    db.commit()
    db.close()


if __name__ == "__main__":
    processsolar()
