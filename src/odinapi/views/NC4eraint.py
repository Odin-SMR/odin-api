'''
Created on Mar 12, 2009
New version Oct 2014 - dicovered that geometric height was in the files
new version April 2015 - to use ERA interim files retreived using the ECMWF API
@author: donal
'''
from netCDF4 import Dataset
import numpy as np
from pylab import interp
#import pdb
class NCeraint(dict):
	'''
	classdocs
	'''


	def __init__(self, filename, ind):
		'''
		This routine will allow us to access
		'''
		def readfield(fid,fieldname,lonsort,ind=0):
			np.disp('''Reading field {0}, index {1}'''.format(*[fieldname,ind]))
			field=np.array(fid.variables[fieldname])[ind,:,:,:]
			#field=np.r_[field]*field.scale_factor+field.add_offset
			field=np.ma.filled(field,np.nan)[:,:,lonsort]
			return field

		def geoid_radius(latitude):
			'''
			Function from GEOS5 class.
			GEOID_RADIUS calculates the radius of the geoid at the given latitude
			[Re] = geoid_radius(latitude) calculates the radius of the geoid (km)
			at the given latitude (degrees).
			----------------------------------------------------------------
				 Craig Haley 11-06-04
			---------------------------------------------------------------
			'''
			DEGREE = np.pi / 180.0
			EQRAD = 6378.14 * 1000
			FLAT = 1.0 / 298.257
			Rmax = EQRAD
			Rmin = Rmax * (1.0 - FLAT)
			Re = np.sqrt(1./(np.cos(latitude*DEGREE)**2/Rmax**2
						+ np.sin(latitude*DEGREE)**2/Rmin**2)) / 1000
			return Re

		def g(z,lat):
			#Re=6372;
			#g=9.81*(1-2.*z/Re)
			return 9.80616 *(1 - 0.0026373*np.cos(2*lat*np.pi/180.) + \
						 0.0000059*np.cos(2*lat*np.pi/180.)**2)*(1-2.*z/geoid_radius(lat))

		fid=Dataset(filename, 'r')

		lats=fid.variables['latitude']
		lats=np.r_[lats]
		lons=fid.variables['longitude']
		#change longitudes from  0- 360 to -180 - 180
		lons=np.r_[lons]
		lons[lons>180]=lons[lons>180]-360
		lonsort=lons.argsort()
		lons=lons[lonsort]
		pres=fid.variables['level'][:].astype(float)*100 #millibar to Pa 
		pres=np.tile(pres,[480,241,1]).T # make it 3d to match the old files
		gp=readfield(fid,'z',lonsort,ind)
		gmh=np.zeros(gp.shape)

		#Calculate gmh
		G0=9.80665 #ms**-2
		for ilat,lat in enumerate (lats):
			Re=geoid_radius(lat)*1000 #to m 
			#print Re
			for ip,pp in  enumerate (pres) :
				glat=g(gp[ip,ilat,:]/G0/1000,lat)
				#print glat
				#pdb.set_trace()
				hr=gp[ip,ilat,:]/G0
				gmh[ip,ilat,:] =hr*Re/(glat*Re/G0 - hr)/1000 #to km


		t=readfield(fid,'t',lonsort,ind)
		#Calculate  potential temperature
		theta=t*(1e5/pres)**0.286
		cfn="t"
		cf=t
		self.update(dict({'fid':fid,'lats': lats, 'lons': lons, 'lonsort': lonsort,'pres': pres, 'gmh': gmh, 'theta':theta, 'CurrentFieldName':cfn,'CurrentField':cf}))


	def extractprofile_on_z(self,fieldname,latpt,longpt,newz,ind=0):
		gmh=self['gmh']
                z=gmh[:,latpt,longpt]
                if fieldname == 'p':
                    profile = np.interp(newz,z[-1::-1],self['pres'][-1::-1,latpt,longpt])                   
                else: 
		    field = self.readfield(fieldname,ind)
                    profile = np.interp(newz/1e3,z[-1::-1],field[-1::-1,latpt,longpt])
		return profile

	def readfield(self,fieldname,ind=0):
	        np.disp('''Reading field {0}, index {1}'''.format(*[fieldname,ind]))
		field=np.array(self['fid'].variables[fieldname])[ind,:,:,:]
		field=np.ma.filled(field,np.nan)[:,:,self['lonsort']]
		self['CurrentField']=field
		self['CurrentFieldName']=fieldname
		return field

	def extractfield_on_p (self,fieldname,plevels):
		'''
		This routine will extract a field on given pressure levels
		'''
		#get the pressures on the model levels
		pres=self['pres']
		field=self.readfield(fieldname)
		logpres=np.log(pres)
		newfield=np.zeros((len(plevels),len(self['lats']),len(self['lons'])))
		for i in range(len(self['lats'])):
			for j in range(len(self['lons'])):
				#f=interpolate.interp1d(np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
				#newfield[:,i,j]=np.interp(np.log(plevels),np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
				newfield[:,i,j]=np.interp(np.log(plevels),logpres[:,i,j],field[:,i,j])
		return newfield

	def extractfield_on_theta (self,fieldname,thlevels):
		'''
		This routine will extract a field on given pressure levels
		'''
		#get the pressures on the model levels
		theta=self['theta']
		field=self.readfield(fieldname)
		newfield=np.zeros((len(thlevels),len(self['lats']),len(self['lons'])))
		for i in range(len(self['lats'])):
			for j in range(len(self['lons'])):
				#f=interpolate.interp1d(np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
				#newfield[:,i,j]=np.interp(np.log(plevels),np.flipud(logpres[:,i,j]),np.flipud(field[:,i,j]))
				newfield[:,i,j]=np.flipud(np.interp(np.flipud(thlevels),np.flipud(theta[:,i,j]),np.flipud(field[:,i,j])))
		newfield=newfield[:,:,self['lonsort']]       #sort longitudes
		return newfield

	def fileclose (self):
		self['fid'].close()




