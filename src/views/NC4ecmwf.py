'''
Created on Mar 12, 2009
New version Oct 2014 - dicovered that geometric height was in the files 
@author: donal
'''
from netCDF4 import Dataset
import numpy as np
from pylab import interp

class NCecmwf(dict):
    '''
    classdocs
    '''


    def __init__(self, filename):
        '''
        This routine will allow us to access 
        '''
        def readfield(fid,fieldname,lonsort):
            np.disp('Reading field')
            field=fid.groups[groupnames[fieldname][0]].variables[fieldname]
            #field=np.r_[field]*field.scale_factor+field.add_offset
            field=np.ma.filled(field,np.nan)[:,:,lonsort]
            return field
    
        fid=Dataset(filename, 'r')
        groups=fid.groups.keys()
        groupnames={}
        for gr in groups:
            vars=fid.groups[gr].variables.keys()
            for v in vars:
                groupnames[v]=[]
                groupnames[v].append(gr)
        self.groupnames=groupnames
       # print groupnames
        lats=fid.groups['Geolocation'].variables['lat']
        lats=np.r_[lats]
        lons=fid.groups['Geolocation'].variables['lon']
        #change longitudes from  0- 360 to -180 - 180
        lons=np.r_[lons]
        lons[lons>180]=lons[lons>180]-360
        lonsort=lons.argsort()
        lons=lons[lonsort]
        #print self.groupnames['P']
        gmh=readfield(fid,'GMH',lonsort)
        pres=readfield(fid,'P',lonsort)
        theta=readfield(fid,'PT',lonsort)
        cfn="Pressure Level"
        cf=pres
        self.update(dict({'fid':fid,'lats': lats, 'lons': lons, 'lonsort': lonsort,'pres': pres, 'gmh': gmh, 'theta':theta, 'CurrentFieldName':cfn,'CurrentField':cf}))
    

    def extractprofile_on_z(self,fieldname,latpt,longpt,newz):
        gmh=self['gmh']
        field=self.readfield(fieldname)
        z=gmh[:,latpt,longpt]
        #print z
        profile=np.interp(newz,z[-1::-1],field[-1::-1,latpt,longpt])
        return profile

    def readfield(self,fieldname):
        if self['CurrentFieldName']!=fieldname :
            np.disp('Reading field '+fieldname)
            field=self['fid'].groups[self.groupnames[fieldname][0]].variables[fieldname]
            #field=np.r_[field]*field.scale_factor+field.add_offset
            field=np.ma.filled(field,np.nan)[:,:,self['lonsort']]
            self['CurrentField']=field
            self['CurrentFieldName']=fieldname
        else:
            field=self['CurrentField']
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
                
        
            
        
