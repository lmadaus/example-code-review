import numpy as np
import xarray as xr

lat = 43.07
lon = 360-89.40

# ERA5
dset = xr.open_dataset('https://ds.nccs.nasa.gov/thredds/dodsC/bypass/CREATE-IP/reanalysis/ECMWF/IFS-Cy41r2/ERA5/mon/atmos/tas.ncml')
era5 = dset['tas'].sel(lat=lat, lon=lon, method='nearest').compute() - 273.14

# CMIP6
#import pandas as pd
#invdf = pd.read_csv('s3://cmip6-pds/pangeo-cmip6.csv')
#use = invdf[
#    (invdf['source_id'].isin(['CESM2','GFDL-ESM4','MIROC6'])) &
#    (invdf['experiment_id'].isin(['historical','ssp585'])) &
#    (invdf['member_id']=='r1i1p1f1') &
#    (invdf['variable_id']=='pr') &
#    (invdf['table_id']=='Amon')
#]
#use.to_csv('use_files.csv')
#print(use)

# MIROC6
import s3fs
fs = s3fs.S3FileSystem(anon=True)
hist = xr.open_zarr(s3fs.S3Map('s3://cmip6-pds/CMIP6/CMIP/MIROC/MIROC6/historical/r1i1p1f1/Amon/tas/gn/v20181212', s3=fs), consolidated=True)['tas'] - 273.14
future = xr.open_zarr(s3fs.S3Map('s3://cmip6-pds/CMIP6/ScenarioMIP/MIROC/MIROC6/ssp585/r1i1p1f1/Amon/tas/gn/v20190627', s3=fs), consolidated=True)['tas'] - 273.14
miroc6 = xr.concat([hist,future], dim='time').sel(lat=lat, lon=lon, method='nearest').compute()

# GFDL
hist = xr.open_zarr(s3fs.S3Map('s3://cmip6-pds/CMIP6/CMIP/NOAA-GFDL/GFDL-ESM4/historical/r1i1p1f1/Amon/tas/gr1/v20190726', s3=fs), consolidated=True)['tas'] - 273.14
future = xr.open_zarr(s3fs.S3Map('s3://cmip6-pds/CMIP6/ScenarioMIP/NOAA-GFDL/GFDL-ESM4/ssp585/r1i1p1f1/Amon/tas/gr1/v20180701', s3=fs), consolidated=True)['tas'] - 273.14
gfdl = xr.concat([hist,future], dim='time').sel(lat=lat, lon=lon, method='nearest').compute()

# BC
era5_climo = era5.sel(time=slice('1980','2010')).groupby('time.month').mean()
miroc6_climo = miroc6.sel(time=slice('1980','2010')).groupby('time.month').mean()
miroc6_ratios = miroc6.groupby('time.month') - miroc6_climo
miroc6_bc = miroc6_ratios.groupby('time.month') + era5_climo
era5_climo = era5.sel(time=slice('1980','2010')).groupby('time.month').mean()
gfdl_climo = gfdl.sel(time=slice('1980','2010')).groupby('time.month').mean()
gfdl_ratios = gfdl.groupby('time.month') - gfdl_climo
gfdl_bc = gfdl_ratios.groupby('time.month') + era5_climo
miroc6_annual_mean = miroc6_bc.groupby('time.year').mean()
miroc6_raw_mean = miroc6.groupby('time.year').mean()
gfdl_annual_mean = gfdl_bc.groupby('time.year').mean()
gfdl_raw_mean = gfdl.groupby('time.year').mean()
era5_raw_mean = era5.groupby('time.year').mean()
 


# plot
import matplotlib.pyplot as plt
plt.figure(figsize=(12,5))
plt.plot(gfdl_raw_mean.year, gfdl_raw_mean, c='b', linestyle='dashed', label='GFDL-ESM4 (raw)', alpha=0.5)
plt.plot(gfdl_annual_mean.year, gfdl_annual_mean, c='b', linestyle='solid', label='GFDL-ESM4 (bc)')
plt.plot(miroc6_raw_mean.year, miroc6_raw_mean, c='r', linestyle='dashed', label='MIROC6 (raw)', alpha=0.5)
plt.plot(miroc6_annual_mean.year, miroc6_annual_mean, c='r', linestyle='solid', label='MIROC6 (bc)')
plt.plot(era5_raw_mean.year, era5_raw_mean, c='k', lw=2, label='ERA5')
plt.legend(loc=0)
plt.grid()
plt.xlabel('Year')
plt.ylabel('Temperature')
plt.title('CMIP6/SSP585')
plt.tight_layout()
plt.savefig('bc.png', bbox_inches='tight')

