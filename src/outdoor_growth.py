'''

This module performs all the operations necessary to estimate outdoor growth 
for losing industry.

'''
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
	sys.path.append(module_path)

from src import params
from src import utilities
from src.plotter import Plotter

import csv
from scipy import interpolate
import numpy as np
import pandas as pd
import geopandas as gpd
from src import utilities

#import resource
from sys import platform
if platform == "linux" or platform == "linux2":
	#this is to ensure Morgan's computer doesn't crash
	import resource
	rsrc = resource.RLIMIT_AS
	resource.setrlimit(rsrc, (3e9, 3e9))#no more than 3 gb



class OutdoorGrowth:

	def __init__(self):
		params.importIfNotAlready()

	def correctForFertilizer(self,yields,fertilizer):

		nbins=params.growAreaBins
		#start out making empty geodataframe
		lats = np.linspace(-90, 90 - params.latdiff, \
						   np.floor(180 / params.latdiff).astype('int'))
		lons = np.linspace(-180, 180 - params.londiff, \
						   np.floor(360 / params.londiff).astype('int'))

		result=np.zeros((nbins*len(lats),nbins*len(lons)))

		lats2d, lons2d = np.meshgrid(lats, lons)
		data = {"lats": pd.Series(lats2d.ravel()),
				"lons": pd.Series(lons2d.ravel())}
		
		df = pd.DataFrame(data=data)
		# geometry = gpd.points_from_xy(df.lons, df.lats)
		# gdf = gpd.GeoDataFrame(df, crs={'init':'epsg:4326'}, geometry=geometry)
		# grid= utilities.makeGrid(gdf)


		#now operate rows together and calculate values for each grid cell

		# # this is SUPER slow!!
		# corrected=[0]*len(fertilizer)
		# for index,row in fertilizer.iterrows():
			
		# 	irr_val_tot = irrigation.iloc[index]['area']
		# 	fer_nit_val = row['n']
		# 	yield_val = yields.iloc[index]['totalYield']

		# 	corrected[index]=yield_val*irr_val_tot*fer_nit_val


		# # this is VERY fast
		# df['corrected'] = fertilizer['n']
		df['corrected'] = yields['totalYield']
		# df['corrected'] = fertilizer['n']*yields['totalYield']
		# utilities.create5minASCII(df,'corrected',params.asciiDir+'example')
		utilities.create5minASCII(df,'corrected',params.asciiDir+'tillage')


		# title="Multiply some variables as example"
		# label="arbitrary"
		# Plotter.plotMap(grid,'corrected',title,label,'example',True)

		

		# growing season
		# radiation
		# soil water

		#thermal regime (classed according to tropics, subtropical, etc), 
		# moisture regime (rain, humidity)
		#soil terrain class
