'''

An example file to deal with variables from different pkl files.
'''

import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
	sys.path.append(module_path)

from src import params
from src.plotter import Plotter
from src import outdoor_growth
from src.outdoor_growth import OutdoorGrowth
import pandas as pd
import geopandas as gpd
import scipy
import matplotlib.pyplot as plt
import numpy as np


params.importAll()

#import yield geopandas data for rice

rice_yield=pd.read_pickle(params.geopandasDataDir + 'RICECropYield.pkl')

#display first 5 rows of rice yield dataset
rice_yield.head()

#select all rows from rice_yield for which the column growArea has a value greater than zero
rice_nozero=rice_yield.loc[rice_yield['growArea'] > 0]
#compile yield data where area is greater 0 in a new array
rice_kgha=rice_nozero['yieldPerArea']
#calculate descriptive statistics values (mean, median, standard deviation and variance)
#for the yield data with a value greater 0
rmean=rice_kgha.mean()
rmeadian=rice_kgha.median()
rsd=rice_kgha.std()
rvar=rice_kgha.var()
#logarithmize the values
rice_kgha_log=np.log(rice_kgha)

#plot rice yield distribution in a histogram
plt.hist(rice_kgha, bins=[1,50, 100, 175, 250,500,1000,1500,2000,2500,3000,3500,4000,5000,6000,7000,8000,9000,10000])
plt.title('Rice yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')

#plot log transformed values of yieldPerArea
plt.hist(rice_kgha_log, bins=[0,1,2,3,4,5,6,7,8,9,10,11])

#test if area without zeros aligns with FAOSTAT harvested area
rice_area_ha = sum(rice_nozero['growArea'])
print(rice_area_ha)
#160732191.87618524
#160256712 FAOSTAT data for year 2010

'''
#subplot for all histograms
fig, axs = plt.subplots(2, 2, figsize=(5, 5))
axs[0, 0].hist(maize_yield['yieldPerArea'], bins=[1,250,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000])
axs[1, 0].hist(maize_kgha, bins=[1,250,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000])
axs[0, 1].hist(maize_kgha_area, bins=[1,50, 100, 175, 250,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000])
axs[1, 1].hist(maize_kgha_yield, bins=[1,50, 100, 175, 250,500,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000])








fertilizer=pd.read_pickle(params.geopandasDataDir + 'Fertilizer.pkl')
irrigation=pd.read_pickle(params.geopandasDataDir + 'Irrigation.pkl')

print(fertilizer.columns)
print(fertilizer.head())
# print(irrigation.columns)
# print(fertilizer.columns)
outdoorGrowth=OutdoorGrowth()
outdoorGrowth.correctForFertilizerAndIrrigation(maize_yield,fertilizer,irrigation)
'''