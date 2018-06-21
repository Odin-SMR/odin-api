% This script calculates the two additional indices, called com1 and com2.

% For this purpose, the daily mean Kp-indices from 22 to 2 days (in that order)
% prior to the considered day are needed. For example, if to calculate
% the NO number density on 23.01.2016, the Kp-index from 01.01.2016 to
% 21.01.2016 is needed.

% wf is a vector containing the indices 20 to 0, which is used to give each Kp
% index a weighted value. It is defined as the number of days before the day into
% consideration minus 2. For example, if we consider the Kp index corresponding
% to 2 days before the simulation day, wf = 0 and the weigthing factor is equal to:
% e^(-wf/5) = e^(-0/5) = 1.
% The further away in time, the closer to zero this term becomes.
wf = 20:-1:0;

% The two following inputs are needed to calculate com1 and com2:
% allKps: 21-element long vector containing the Kp indices
% dec:    solar declination on the simulation day, calculated as follows:
theta0 = 2*pi*(doy-1)/365;
% where doy is the day of year for the day under consideration.
dec    = 0.006918-0.399912*cos(theta0)+0.070257*sin(theta0)-0.006758*cos(2*theta0)+0.000907*sin(2*theta0) - 0.002697*cos(3*theta0)+0.001480*sin(3*theta0);
dec    = dec*180./pi;

% Create a vector consisting of the Kp index of the prior days multiplied
% by their weighting factor (exp(-wf/5)) and the solar declination term,
% as prerequisites for the calculation of com1 (wKps1) and com2 (wKps2):
wKps1 = allKps.*exp(-wf/5)*(-dec+23.4)/46.8;
wKps2 = allKps.*exp(-wf/5)*(dec+23.4)/46.8;

% According to the solar declination, assign different
% integration times for com1 (sumover1) and com2 (sumover2)
if dec>0
    sumover1=1;
elseif dec<=0 && dec>-5
    sumover1=2;
elseif dec<=-5 && dec>-10
    sumover1=4;
elseif dec<=-10 && dec>-15
    sumover1=6;
elseif dec<=-15 && dec>-20
    sumover1=10;
elseif dec<=-20
    sumover1=20;
end

if dec<0
    sumover2=1;
  elseif dec>=0 && dec<5
    sumover2=2;
  elseif dec>=5 && dec<10
    sumover2=4;
  elseif dec>=10 && dec<15
    sumover2=6;
  elseif dec>=15 && dec<20
    sumover2=10;
  elseif dec>=20
    sumover2=20;
end

% Sum over the terms in wKps according to the above scheme.
com1 = sum(wKps1(end-sumover1:end));
com2 = sum(wKps2(end-sumover2:end));





