import ctypes
import numpy as np

# struct ap_array {
# double a[7];
# };


class ap_array(ctypes.Structure):
    _fields_ = [("a", ctypes.c_double * 7)]


aph = ap_array()

# struct nrlmsise_input {
# int year;      /* year, currently ignored */
# int doy;       /* day of year */
# double sec;    /* seconds in day (UT) */
# double alt;    /* altitude in kilometes */
# double g_lat;  /* geodetic latitude */
# double g_long; /* geodetic longitude */
# double lst;    /* local apparent solar time (hours), see note below */
# double f107A;  /* 81 day average of F10.7 flux (centered on doy) */
# double f107;   /* daily F10.7 flux for previous day */
# double ap;     /* magnetic index(daily) */
# struct ap_array *ap_a; /* see above */
# }:


class nrlmsise_input(ctypes.Structure):
    _fields_ = [
        ("year", ctypes.c_int),
        ("doy", ctypes.c_int),
        ("sec", ctypes.c_double),
        ("alt", ctypes.c_double),
        ("g_lat", ctypes.c_double),
        ("g_long", ctypes.c_double),
        ("lst", ctypes.c_double),
        ("f107A", ctypes.c_double),
        ("f107", ctypes.c_double),
        ("ap", ctypes.c_double),
        ("ap_a", ctypes.POINTER(ap_array)),
    ]


# struct nrlmsise_flags {
# int switches[24];
# double sw[24];
# double swc[24];
# };


class nrlmsise_flags(ctypes.Structure):
    _fields_ = [
        ("switches", ctypes.c_int * 24),
        ("sw", ctypes.c_double * 24),
        ("swc", ctypes.c_double * 24),
    ]


# struct nrlmsise_output {
# double d[9];   /* densities */
# double t[2];   /* temperatures */
# };


class nrlmsise_output(ctypes.Structure):
    _fields_ = [("d", ctypes.c_double * 9), ("t", ctypes.c_double * 2)]


flags = nrlmsise_flags()
flags.switches[0] = 0

# for i in np.arange(24):
# 	flags.sw[i]=1.
# 	flags.swc[i]=1.

for i in np.arange(23) + 1:
    flags.switches[i] = 1
flags.switches[9] = -1
print(flags)
print(flags.switches[:])

# aph=ap_array()
for i in range(7):
    aph.a[i] = 100.0


inputt = nrlmsise_input()
outputt = nrlmsise_output()
inputt.doy = 172
inputt.year = 0
inputt.sec = 29000
inputt.alt = 400
inputt.g_lat = 60.0
inputt.g_long = -70.0
inputt.lst = 16.0
inputt.f107A = 150.0
inputt.f107 = 150.0
inputt.ap = 4.0
inputt.ap_a = ctypes.pointer(aph)
print(inputt)

msis = ctypes.CDLL("./nrlmsis.so")
msis.gtd7.argtypes = [
    ctypes.POINTER(nrlmsise_input),
    ctypes.POINTER(nrlmsise_flags),
    ctypes.POINTER(nrlmsise_output),
]
msis.gtd7(ctypes.byref(inputt), ctypes.byref(flags), ctypes.byref(outputt))
print(flags.sw[:])
print(flags.swc[:])
print(outputt.d[:])
print(outputt.t[:])
print(inputt.ap)
print(inputt.ap_a)
