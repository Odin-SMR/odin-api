% This script demonstrates how the SMR Acquired Nitric Oxide Model Atmosphere (SANOMA) can be used.

% First, load the coefficients from SANOMA_indices.mat
% (which contains the coefficients for each altitude-magnetic latitude bin)
load('SANOMA_indices.mat')
% These coefficient are also available in text format.

% In order to calculate a global magnetic latitude - altitude grid of NO,
% three indices are required:

% 1. Kp index, which is an indicator for geomagnetic activity.
%    Note! One should use the daily mean Kp corresponding to one day prior to the simulation day.
%    In addition, the daily mean Kp corresponding to the 22 previous days are also needed
%    in order to calculate the additional indices com 1 and com2, as described in the script
%    called SANOMA_extraindices.m.
% 2. Solar declination, to account for the seasonal variation of solar incoming radiation.
%    It can be calculated as follows:
theta0 = 2*pi*(doy-1)/365;
dec    = 0.006918-0.399912*cos(theta0)+0.070257*sin(theta0)-0.006758*cos(2*theta0)+0.000907*sin(2*theta0) - 0.002697*cos(3*theta0)+0.001480*sin(3*theta0);
dec    = dec*180./pi;
%    In which doy is the day of year for the day under consideration.
% 3. F10.7cm radio flux, which is a proxy for solar activity.
%    Note! One should use the daily mean F10.7cm flux corresponding to one day prior to the simulation day.

% The daily mean NO number density for the day under consideration is then calculated as follows:
NO = kpinds*Kp + seasoninds*dec + log10inds*log10(F107cm) + com1inds*com1 + com2inds*com2 + constants;

% This results in a NO zonal map given for 33 magnetic latitude bins ([-82.5:5:82.5] degrees),
% and for 5 altitude bins ([85000:6667:118333] m).








