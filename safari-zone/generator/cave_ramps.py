"""Broad rock descents: continuous height field joined to chamber floors."""
import numpy as np
from scipy.ndimage import minimum_filter

def apply(a,entries,passages,origin,ymin,block):
    N=a.shape[1];field=np.full((N,N),30000,np.int16)
    for entry in entries:
        p=np.array(entry['staircase'],float);distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p[:,[0,2]],axis=0),axis=1))]
        fraction=distance/max(1,distance[-1]);start=entry['entrance'][1];end=entry['chamber'][1]-2
        heights=start+(end-start)*fraction
        for (x,_,z),y,t in zip(p,heights,fraction):
            ix=int(x)-origin;iz=int(z)-origin;radius=3.4+1.2*np.sin(t*np.pi)**2
            for dx in range(-5,6):
                for dz in range(-5,6):
                    if dx*dx+dz*dz>radius*radius:continue
                    # The whole slope is supported rock, not a separate walkway.
                    iy=int(round(y))-ymin
                    field[iz+dz,ix+dx]=min(field[iz+dz,ix+dx],iy)
    valid=field<30000
    for _ in range(24):
        updated=np.where(valid,np.minimum(field,minimum_filter(field,3,mode='constant',cval=30000)+1),30000).astype(np.int16)
        if np.array_equal(field,updated):break
        field=updated
    air=block('air');water=block('water[level=0]');stone=block('stone')
    for iy in np.unique(field[valid]):
        mask=valid&(field==iy);a[iy:iy+4,mask]=air
    zz,xx=np.nonzero(valid)
    for iz,ix in zip(zz,xx):
        iy=int(field[iz,ix]);a[iy-1,iz,ix]=stone;a[iy-2,iz,ix]=stone;j=iy-3
        while j>0 and a[j,iz,ix] in [air,water]:a[j,iz,ix]=stone;j-=1

    return field
