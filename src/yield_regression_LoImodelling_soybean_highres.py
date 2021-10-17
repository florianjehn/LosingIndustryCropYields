'''

File containing the code to explore data and perform a multiple regression
on yield for soyb
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
from src import stat_ut
import pandas as pd
import geopandas as gpd
import scipy
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from numpy import inf
#seaborn is just used for plotting, might be removed later
import seaborn as sb
import statsmodels.api as sm
from patsy import dmatrices
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

params.importAll()


'''
Import data, extract zeros and explore data statistic values and plots 
'''

#import yield geopandas data for soyb

soyb_yield=pd.read_csv(params.geopandasDataDir + 'SOYBCropYieldHighRes.csv')

#display first 5 rows of soyb yield dataset
soyb_yield.head()

#select all rows from soyb_yield for which the column growArea has a value greater than zero
soyb_nozero=soyb_yield.loc[soyb_yield['growArea'] > 100]
#compile yield data where area is greater 0 in a new array
soyb_kgha=soyb_nozero['yield_kgPerHa']


soyb_nozero['growArea'].min() #0.1 ha
soyb_nozero['growArea'].max() #9053.2 ha
soyb_nozero['growArea'].mean() #295.23 ha
tt3 = (soyb_nozero['yield_kgPerHa'] * soyb_nozero['growArea']).sum()
ar_t = soyb_nozero.loc[soyb_nozero['growArea'] < 10] #160924 cells ~46.66%
ar_t1 = soyb_nozero.loc[soyb_nozero['growArea'] > 1000] #34096 cells ~9.87% but ~78.21% of the yield...
tt = (ar_t1['yield_kgPerHa'] * ar_t1['growArea']).sum() #195623962690.36334 kg
ar_t2 = soyb_nozero.loc[soyb_nozero['growArea'] > 100] #97637 cells ~28.27% but ~97.39% of the yield...
tt2 = (ar_t2['yield_kgPerHa'] * ar_t2['growArea']).sum()
243598120402.9715/250114718599.569 #
ax = sb.boxplot(x=ar_t2["growArea"])
97637/345296

#calculate descriptive statistics values (mean, median, standard deviation and variance)
#for the yield data with a value greater 0
smean=soyb_kgha.mean()
smeadian=soyb_kgha.median()
ssd=soyb_kgha.std()
svar=soyb_kgha.var()
smax=soyb_kgha.max()
#calculate the mean with total production and area to check if the computed means align
smean_total = ( soyb_nozero['totalYield'].sum()) / (soyb_nozero['growArea'].sum())
#the means do not align, probably due to the rebinning process
#calculate weighted mean (by area) of the yield colum
smean_weighted = round(np.average(soyb_kgha, weights=soyb_nozero['growArea']),2)
#now they align!

#check the datatype of yield_kgPerHa and logarithmize the values
#logging is done to check the histogram and regoression fit of the transformed values
soyb_kgha.dtype
soyb_kgha_log=np.log(soyb_kgha)

#plot soyb yield distribution in a histogram
plt.hist(soyb_kgha, bins=50)
plt.title('soyb yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')

#plot log transformed values of yield_kgPerHa
plt.hist(soyb_kgha_log, bins=50)

#test if area without zeros aligns with FAOSTAT harvested area
soyb_area_ha = sum(soyb_nozero['growArea'])
print(soyb_area_ha)
#164569574.0937798
#164586904	#FAOSTAT area from 2010 for soyb

#subplot for all histograms
fig, axs = plt.subplots(1, 2, figsize=(5, 5))
axs[0].hist(soyb_kgha, bins=50)
axs[1].hist(soyb_kgha_log, bins=50)


#plots show that the raw values are right skewed so we try to fit a lognormal distribution and an exponentail distribution
#on the raw data and a normal distribution on the log transformed data

'''
Fitting of distributions to the data and comparing the fit
'''
#sets design aspects for the following plots
matplotlib.rcParams['figure.figsize'] = (16.0, 12.0)
matplotlib.style.use('ggplot')

#initialize a list for density functions, distribution names and estimated parameters
#the lists will later be used to calculate logLik, AIC and BIC of each distribution
#to compare the fits against each other
pdf_lists = []
dist_lists = []
param_dicts ={"Values":[]}
#set xs to bins in the range of the raw data
xs = np.linspace(0.01,
                12500, 100)

###################################################################################
#####Testing of multiple distributions visually and using logLik, AIC and BIC######
###################################################################################

#Exponential distribution
dist_lists.append('exponential')
#get parameters and store them in the dictionary
param1 = stats.expon.fit(soyb_kgha)
param_dicts["Values"].append(param1)
print(param1)
#calculate pdf
pdf_fitted1 = stats.expon.pdf(xs, *param1)
#calculate log pdf and store it in the list
pdf_fitted_log1 = stats.expon.logpdf(soyb_kgha, *param1)
pdf_lists.append(pdf_fitted_log1)
#plot data histogram and pdf curve
h = plt.hist(soyb_kgha, bins=50, density=True)
plt.plot(xs, pdf_fitted1, lw=2, label="Fitted Exponential distribution")
plt.legend()
plt.show()

#Normal distribution
dist_lists.append('normal')
#get parameters and store them in the dictionary
param2 = stats.norm.fit(soyb_kgha)
#param_list.append(param2)
param_dicts["Values"].append(param2)
print(param2)
#calculate pdf
pdf_fitted2 = stats.norm.pdf(xs, *param2)
#calculate log pdf and store it in the list
pdf_fitted_log2 = stats.norm.logpdf(soyb_kgha, *param2)
pdf_lists.append(pdf_fitted_log2)
#plot data histogram and pdf curve
h = plt.hist(soyb_kgha, bins=50, density=True)
plt.plot(xs, pdf_fitted2, lw=2, label="Fitted normal distribution")
plt.legend()
plt.show()

#Gamma distribution
dist_lists.append('Gamma')
#get parameters and store them in the dictionary
param3 = stats.gamma.fit(soyb_kgha)
#param_list.append(param3)
param_dicts["Values"].append(param3)
print(param3)
#calculate pdf
pdf_fitted3 = stats.gamma.pdf(xs, *param3)
#calculate log pdf and store it in the list
pdf_fitted_log3 = stats.gamma.logpdf(soyb_kgha, *param3)
pdf_lists.append(pdf_fitted_log3)
#plot data histogram and pdf curve
h = plt.hist(soyb_kgha, bins=50, density=True)
plt.plot(xs, pdf_fitted3, lw=2, label="Fitted Gamma distribution")
plt.legend()
plt.show()

#Inverse Gamma distribution
dist_lists.append('Inverse Gamma')
#get parameters and store them in the dictionary
param4 = stats.invgamma.fit(soyb_kgha)
#param_list.append(param4)
param_dicts["Values"].append(param4)
print(param4)
#calculate pdf
pdf_fitted4 = stats.invgamma.pdf(xs, *param4)
#calculate log pdf and store it in the list
pdf_fitted_log4 = stats.invgamma.logpdf(soyb_kgha, *param4)
pdf_lists.append(pdf_fitted_log4)
#plot data histogram and pdf curve
h = plt.hist(soyb_kgha, bins=50, density=True)
plt.plot(xs, pdf_fitted4, lw=2, label="Fitted Inverse Gamma distribution")
plt.legend()
plt.show()

xs1 = np.linspace(4,
                11, 100)
#Normal distribution on log values
dist_lists.append('normal on log')
#get parameters and store them in the dictionary
param5 = stats.norm.fit(soyb_kgha_log)
#param_list.append(param5)
param_dicts["Values"].append(param5)
print(param5)
#calculate pdf
pdf_fitted5 = stats.norm.pdf(xs1, *param5)
#calculate log pdf and store it in the list
pdf_fitted_log5 = stats.norm.logpdf(soyb_kgha_log, *param5)
pdf_lists.append(pdf_fitted_log5)
#plot data histogram and pdf curve
h = plt.hist(soyb_kgha_log, bins=50, density=True)
plt.plot(xs1, pdf_fitted5, lw=2, label="Fitted normal distribution on log")
plt.legend()
plt.title('log soyb yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')
plt.show()

#one in all plot
h = plt.hist(soyb_kgha, bins=50, density=True)
plt.plot(xs, pdf_fitted1, lw=2, label="Fitted Exponential distribution")
plt.plot(xs, pdf_fitted2, lw=2, label="Fitted Normal distribution")
plt.plot(xs, pdf_fitted3, lw=2, label="Fitted Gamma distribution")
plt.plot(xs, pdf_fitted4, lw=2, label="Fitted Inverse Gamma distribution")
plt.legend()
plt.title('soyb yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')
plt.xlim(right=20000)
plt.show()


#calculate loglik, AIC & BIC for each distribution
st = stat_ut.stat_overview(dist_lists, pdf_lists, param_dicts)
'''
    Distribution  loglikelihood           AIC           BIC
7  normal on log  -3.748763e+05  7.497686e+05  7.498546e+05
6  Inverse Gamma  -2.859205e+06  5.718427e+06  5.718513e+06
5          Gamma  -2.860227e+06  5.720469e+06  5.720555e+06
3         normal  -2.908569e+06  5.817154e+06  5.817240e+06
1    exponential  -2.910045e+06  5.820106e+06  5.820192e+06
0        lognorm  -3.587555e+06  7.175125e+06  7.175211e+06
2        weibull  -3.694327e+06  7.388671e+06  7.388757e+06
4     halfnormal           -inf           inf           inf
Best fit is normal on log by far, then inverse gamma on non-log
'''

'''
Load factor data and extract zeros
'''
s_pesticides=pd.read_csv(params.geopandasDataDir + 'SoybeanPesticidesHighRes.csv')
print(s_pesticides.columns)
print(s_pesticides.head())
fertilizer=pd.read_csv(params.geopandasDataDir + 'FertilizerHighRes.csv') #kg/m²
print(fertilizer.columns)
print(fertilizer.head())
fertilizer_man=pd.read_csv(params.geopandasDataDir + 'FertilizerManureHighRes.csv') #kg/km²
print(fertilizer_man.columns)
print(fertilizer_man.head())
irr_t=pd.read_csv(params.geopandasDataDir + 'FracIrrigationAreaHighRes.csv')
print(irr_t.columns)
print(irr_t.head())
crop = pd.read_csv(params.geopandasDataDir + 'FracCropAreaHighRes.csv')
irr_rel=pd.read_csv(params.geopandasDataDir + 'FracReliantHighRes.csv')
tillage=pd.read_csv(params.geopandasDataDir + 'TillageHighResAllCrops.csv')
print(tillage.columns)
print(tillage.head())
aez=pd.read_csv(params.geopandasDataDir + 'AEZHighRes.csv')
print(aez.columns)
print(aez.head())
print(aez.dtypes)

#fraction of irrigation total is of total cell area so I have to divide it by the
#fraction of crop area in a cell and set all values >1 to 1
irr_tot = irr_t['fraction']/crop['fraction']
irr_tot.loc[irr_tot > 1] = 1
#dividing by 0 leaves a NaN value, so I have them all back to 0
irr_tot.loc[irr_tot.isna()] = 0


#print the value of each variable at the same index to make sure that coordinates align (they do)
print(s_pesticides.loc[6040])
print(fertilizer.loc[6040])
print(fertilizer_man.loc[6040])
#print(irrigation.loc[6040])
print(tillage.loc[6040])
print(aez.loc[6040])
print(soyb_yield.loc[6040])

#fertilizer is in kg/m² and fertilizer_man is in kg/km² while yield and pesticides are in kg/ha
#I would like to have all continuous variables in kg/ha
n_new = fertilizer['n'] * 10000
p_new = fertilizer['p'] * 10000
fert_new = pd.concat([n_new, p_new], axis='columns')
fert_new.rename(columns={'n':'n_kgha', 'p':'p_kgha'}, inplace=True)
fertilizer = pd.concat([fertilizer, fert_new], axis='columns') #kg/ha

applied_new = fertilizer_man['applied'] / 100
produced_new = fertilizer_man['produced'] / 100
man_new = pd.concat([applied_new, produced_new], axis='columns')
man_new.rename(columns={'applied':'applied_kgha', 'produced':'produced_kgha'}, inplace=True)
fertilizer_man = pd.concat([fertilizer_man, man_new], axis='columns') #kg/ha

#compile a combined factor for N including both N from fertilizer and manure
N_total = fertilizer['n_kgha'] + fertilizer_man['applied_kgha'] #kg/ha

'''
I don't remember what this was for
print(soyb_yield.columns.tolist())
l = soyb_yield.loc[:,'lats']
'''

#################################################################################
##############Loading variables without log to test the effect###################
#################################################################################
datas_raw = {"lat": soyb_yield.loc[:,'lats'],
		"lon": soyb_yield.loc[:,'lons'],
		"area": soyb_yield.loc[:,'growArea'],
        "Y": soyb_yield.loc[:,'yield_kgPerHa'],
		"n_fertilizer": fertilizer.loc[:,'n_kgha'],
		"p_fertilizer": fertilizer.loc[:,'p_kgha'],
        "n_manure": fertilizer_man.loc[:,'applied_kgha'],
        "n_man_prod" : fertilizer_man.loc[:,'produced_kgha'],
        "n_total" : N_total,
        "pesticides_H": s_pesticides.loc[:,'total_H'],
        "mechanized": tillage.loc[:,'is_mech'],
        "irrigation_tot": irr_tot,
        "irrigation_rel": irr_rel.loc[:,'frac_reliant'],
        "thz_class" : aez.loc[:,'thz'],
        "mst_class" : aez.loc[:,'mst'],
        "soil_class": aez.loc[:,'soil']
		}

#arrange data_raw in a dataframe
dsoyb_raw = pd.DataFrame(data=datas_raw)
#select only the rows where the area of the cropland is larger than 0
ds0_raw=dsoyb_raw.loc[dsoyb_raw['area'] > 0]

ds0_raw['pesticides_H'] = ds0_raw['pesticides_H'].replace(np.nan, -9)
ds0_raw['irrigation_rel'] = ds0_raw['irrigation_rel'].replace(np.nan, -9)

#test if there are cells with 0s for the AEZ classes (there shouldn't be any)
s_testt = ds0_raw.loc[ds0_raw['thz_class'] == 0] #only 25 0s
s_testm = ds0_raw.loc[ds0_raw['mst_class'] == 0] #only 25 0s
s_tests = ds0_raw.loc[ds0_raw['soil_class'] == 0]
#1279 0s probably due to the original soil dataset being in 30 arcsec resolution:
    #land/ocean boundaries, especially of islands, don't always align perfectly

#test if certain classes of the AEZ aren't present in the dataset because they
#represent conditions which aren't beneficial for plant growth
#thz_class: test Arctic and Bor_cold_with_permafrost
s_test_t9 = ds0_raw.loc[ds0_raw['thz_class'] == 9]
#31 with Boreal and permafrost: reasonable
s_test_t10 = ds0_raw.loc[ds0_raw['thz_class'] == 10]
#60 with Arctic: is reasonable

#mst_class: test LPG<60days
s_test_m = ds0_raw.loc[ds0_raw['mst_class'] == 1]
#2676 in LPG<60 days class: probably due to irrigation

#soil class: test urban, water bodies and very steep class
s_test_s1 = ds0_raw.loc[ds0_raw['soil_class'] == 1]
#7852 in very steep class: makes sense, there is marginal agriculture in
#agricultural outskirts
s_test_s7 = ds0_raw.loc[ds0_raw['soil_class'] == 7]
#2280 in water class: this doesn't make sense but also due to resolution
#I think these should be substituted
s_test_s8 = ds0_raw.loc[ds0_raw['soil_class'] == 8]
#2372 in urban class: probably due to finer resolution in soil class, e.g. course of 
#the Nile is completely classified with yield estimates even though there are many urban areas
#Question: should the urban datapoints be taken out due to them being unreasonable? But then again
#the other datasets most likely contain values in these spots as well (equally unprecise), so I would
#just lose information
#I could substitute them like the water bodies

#test mech dataset values
s_test_mech0 = ds0_raw.loc[ds0_raw['mechanized'] == 0] #82541, now 95508
s_test_mech1 = ds0_raw.loc[ds0_raw['mechanized'] == 1] #172097, now 196854
s_test_mechn = ds0_raw.loc[ds0_raw['mechanized'] == -9] #90658, now 52934
#this is a problem: -9 is used as NaN value and there are way, way too many

s_test_f = ds0_raw.loc[ds0_raw['n_fertilizer'] < 0] #11074 0s, 4205 NaNs
s_test_pf = ds0_raw.loc[ds0_raw['p_fertilizer'] < 0] #11770 0s, 4205 NaNs
s_test_man = ds0_raw.loc[ds0_raw['n_manure'] < 0] #9794 0s, 0 NaNs
s_test_p = ds0_raw.loc[ds0_raw['pesticides_H'].isna()] #183822 NaNs but no 0s

#replace 0s in the moisture, climate and soil classes as well as 7 & 8 in the
#soil class with NaN values so they can be handled with the .fillna method
ds0_raw['thz_class'] = ds0_raw['thz_class'].replace(0,np.nan)
ds0_raw['mst_class'] = ds0_raw['mst_class'].replace(0,np.nan)
ds0_raw['soil_class'] = ds0_raw['soil_class'].replace([0,7,8],np.nan)
#replace 9 & 10 with 8 to combine all three classes into one Bor+Arctic class
ds0_raw['thz_class'] = ds0_raw['thz_class'].replace([9,10],8)

#fill in the NaN vlaues in the dataset with a forward filling method
#(replacing NaN with the value in the cell before)
ds0_raw = ds0_raw.fillna(method='ffill')

#Handle the data by eliminating the rows without data:
ds0_elim = ds0_raw.loc[ds0_raw['pesticides_H'] > -9]
ds0_elim = ds0_elim.loc[ds0_raw['mechanized'] > -9] 

#replace remaining no data values in the fertilizer datasets with NaN and then fill them
ds0_elim.loc[ds0_elim['n_fertilizer'] < 0, 'n_fertilizer'] = np.nan #only 2304 left, so ffill 
ds0_elim.loc[ds0_elim['p_fertilizer'] < 0, 'p_fertilizer'] = np.nan
ds0_elim = ds0_elim.fillna(method='ffill')
#replace no data values in n_total with the sum of the newly filled n_fertilizer and the
#n_manure values
ds0_elim.loc[ds0_elim['n_total'] < 0, 'n_total'] = ds0_elim['n_fertilizer'] + ds0_elim['n_manure']

plt.hist(ds0_elim['soil_class'])

##############################################################
############################Outliers##########################
##############################################################

s_out_f = ds0_elim.loc[ds0_elim['n_fertilizer'] > 400] #only 11 left
s_out_p = ds0_elim.loc[ds0_elim['p_fertilizer'] > 100] #11
s_out_man = ds0_elim.loc[ds0_elim['n_manure'] > 250] #1
s_out_prod = ds0_elim.loc[ds0_elim['n_man_prod'] > 1000] #3
s_out_n = ds0_elim.loc[(ds0_elim['n_manure'] > 250) | (ds0_elim['n_fertilizer'] > 400)] #has to be 78+35-1=112

s_mman = ds0_elim['n_manure'].mean() #5.66483615994264
s_medman = ds0_elim['n_manure'].median() #3.512859954833984

ds0_qt = ds0_elim.quantile([.1, .5, .75, .9, .95, .99, .999])

#Boxplot of all the variables
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

fig.suptitle('ds0_elim Boxplots for each variable')

sb.boxplot(ax=axes[0, 0], data=ds0_elim, x='n_fertilizer')
sb.boxplot(ax=axes[0, 1], data=ds0_elim, x='p_fertilizer')
sb.boxplot(ax=axes[0, 2], data=ds0_elim, x='n_manure')
sb.boxplot(ax=axes[1, 0], data=ds0_elim, x='n_total')
sb.boxplot(ax=axes[1, 1], data=ds0_elim, x='pesticides_H')
sb.boxplot(ax=axes[1, 2], data=ds0_elim, x='Y')

ax = sb.boxplot(x=ds0_elim["Y"], orient='v')
ax = sb.boxplot(x=ds0_elim["n_fertilizer"])
ax = sb.boxplot(x=ds0_elim["p_fertilizer"])
ax = sb.boxplot(x=ds0_elim["n_manure"])
ax = sb.boxplot(x=ds0_elim["n_total"])
ax = sb.boxplot(x=ds0_elim["pesticides_H"])
ax = sb.boxplot(x=ds0_elim["irrigation_tot"])
ax = sb.boxplot(x=ds0_elim["irrigation_rel"])
ax = sb.boxplot(x="mechanized", y='Y', data=ds0_elim)
ax = sb.boxplot(x="thz_class", y='Y', hue='mechanized', data=ds0_elim)
ax = sb.boxplot(x="mst_class", y='Y', data=ds0_elim)
ax = sb.boxplot(x="soil_class", y='Y', data=ds0_elim)

#replace nonsense values in fertilizer and manure datasets
ds0_elim.loc[ds0_elim['n_fertilizer'] > 400, 'n_fertilizer'] = np.nan
ds0_elim.loc[ds0_elim['p_fertilizer'] > 100, 'p_fertilizer'] = np.nan
ds0_elim.loc[ds0_elim['n_manure'] > 250, 'n_manure'] = np.nan
#ds0_elim.loc[ds0_elim['n_man_prod'] > 1000, 'n_man_prod'] = np.nan
ds0_elim = ds0_elim.fillna(method='ffill')
ds0_elim['n_total'] = ds0_elim['n_manure'] + ds0_elim['n_fertilizer']


###############################################################################
############Loading log transformed values for all variables##################
##############################################################################


#using log values for the input into the regression
#unfortunately the ln of 0 is not defined
#just keeping the 0 would skew the results as that would imply a 1 in the data when there is a 0
#could just use the smallest value of the dataset as a substitute?
data_log = {"lat": soyb_yield.loc[:,'lats'],
		"lon": soyb_yield.loc[:,'lons'],
		"area": soyb_yield.loc[:,'growArea'],
        "yield": np.log(soyb_yield.loc[:,'yield_kgPerHa']),
		"n_fertilizer": np.log(fertilizer.loc[:,'n_kgha']),
		"p_fertilizer": np.log(fertilizer.loc[:,'p_kgha']),
        "n_manure": np.log(fertilizer_man.loc[:,'applied_kgha']),
        "n_total" : np.log(N_total),
        "pesticides_H": np.log(s_pesticides.loc[:,'total_H']),
        "mechanized": tillage.loc[:,'is_mech'],
#        "irrigation": np.log(irrigation.loc[:,'area']),
        "thz_class" : aez.loc[:,'thz'],
        "mst_class" : aez.loc[:,'mst'],
        "soil_class": aez.loc[:,'soil']
		}


dsoyb_log = pd.DataFrame(data=data_log)
#select all rows from dsoyb_log for which the column growArea has a value greater than zero
ds0_log=dsoyb_log.loc[dsoyb_log['area'] > 0]
#the data contains -inf values because the n+p+pests+irrigation columns contain 0 values for which ln(x) is not defined 
#calculate the minimum values for each column disregarding -inf values to see which is the lowest value in the dataset (excluding lat & lon)
min_ds0_log=ds0_log[ds0_log.iloc[:,3:11]>-inf].min()
#replace the -inf values with the minimum of the dataset + 5 : this is done to achieve a distinction between very small
#values and actual zeros
ds0_log.replace(-inf, -30, inplace=True)
#check distribution of AEZ factors in the historgrams
matplotlib.rcParams['figure.figsize'] = (16.0, 12.0)
matplotlib.style.use('ggplot')

plt.hist(ds0_log['soil_class'], bins=50)
plt.hist(ds0_log['mst_class'], bins=50)
plt.hist(ds0_log['thz_class'], bins=50)
#ONLY RUN THIS BLOCK WHEN WORKING AT LOW RESOLUTION!
#AEZ factors contain unexpected 0s due to resolution rebinning
#urban class is missing in soil because of rebinning (urban class to small to dominant a large cell)
#convert 0s in the AEZ columns to NaN values so that they can be replaced by the ffill method
#0s make no sense in the dataset that is limited to soyb cropping area because the area is obviously on land
ds0_log['thz_class'] = ds0_log['thz_class'].replace(0,np.nan)
ds0_log['mst_class'] = ds0_log['mst_class'].replace(0,np.nan)
ds0_log['soil_class'] = ds0_log['soil_class'].replace(0,np.nan)
#NaN values throw errors in the regression, they need to be handled beforehand
#fill in the NaN vlaues in the dataset with a forward filling method (replacing NaN with the value in the cell before)
ds0_log = ds0_log.fillna(method='ffill')
#fill in the remaining couple of nans at the top of mechanized column
ds0_log['mechanized'] = ds0_log['mechanized'].fillna(1)

#Just some PLOTS

matplotlib.rcParams['figure.figsize'] = (16.0, 12.0)
matplotlib.style.use('ggplot')

#plot the continuous variables to get a sense of their distribution #RAW
plt.hist(ds0_raw['n_fertilizer'], bins=50)
plt.hist(ds0_raw['p_fertilizer'], bins=50)
plt.hist(ds0_raw['n_total'], bins=50)
plt.hist(ds0_raw['pesticides_H'], bins=100)
plt.hist(ds0_raw['irrigation'], bins=50)
'''
plt.ylim(0,5000)
plt.xlim(0, 0.04)
plt.title('soyb yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')
'''

#scatterplots for #RAW variables

ds0_raw.plot.scatter(x = 'n_fertilizer', y = 'yield')
ds0_raw.plot.scatter(x = 'p_fertilizer', y = 'yield')
ds0_raw.plot.scatter(x = 'pesticides_H', y = 'yield')
ds0_raw.plot.scatter(x = 'mechanized', y = 'yield')
ds0_raw.plot.scatter(x = 'non-mechanized', y = 'yield')
ds0_raw.plot.scatter(x = 'irrigation', y = 'yield')

#scatterplots and histograms for #LOG variables
ds0_log.plot.scatter(x = 'n_fertilizer', y = 'yield')
ds0_log.plot.scatter(x = 'p_fertilizer', y = 'yield')
ds0_log.plot.scatter(x = 'pesticides_H', y = 'yield')
ds0_log.plot.scatter(x = 'mechanized', y = 'yield')
ds0_log.plot.scatter(x = 'n_total', y = 'yield')
ds0_log.plot.scatter(x = 'irrigation', y = 'yield')
ds0_log.plot.scatter(x = 'thz_class', y = 'yield')
ds0_log.plot.scatter(x = 'mst_class', y = 'yield')
ds0_log.plot.scatter(x = 'soil_class', y = 'yield')

plt.hist(ds0_log['n_fertilizer'], bins=50)
plt.hist(ds0_log['p_fertilizer'], bins=50)
plt.hist(ds0_log['n_total'], bins=50)
plt.hist(ds0_log['pesticides_H'], bins=100)
plt.hist(ds0_log['irrigation'], bins=50)
plt.hist(ds0_log['mechanized'], bins=50)
plt.hist(ds0_log['thz_class'], bins=50)
plt.hist(ds0_log['mst_class'], bins=50)
plt.hist(ds0_log['soil_class'], bins=50)
plt.ylim(0,5000)
plt.title('soyb yield ha/kg')
plt.xlabel('yield kg/ha')
plt.ylabel('density')

#mst, thz and soil are categorical variables which need to be converted into dummy variables before running the regression
#####RAW##########
dus_mst_raw = pd.get_dummies(ds0_raw['mst_class'])
dus_thz_raw = pd.get_dummies(ds0_raw['thz_class'])
dus_soil_raw = pd.get_dummies(ds0_raw['soil_class'])
#####LOG##########
dus_mst_log = pd.get_dummies(ds0_log['mst_class'])
dus_thz_log = pd.get_dummies(ds0_log['thz_class'])
dus_soil_log = pd.get_dummies(ds0_log['soil_class'])
#rename the columns according to the classes
#####RAW##########
dus_mst_raw = dus_mst_raw.rename(columns={1:"LGP<60days", 2:"60-120days", 3:"120-180days", 4:"180-225days",
                                  5:"225-270days", 6:"270-365days", 7:"365+days"}, errors="raise")
dus_thz_raw = dus_thz_raw.rename(columns={1:"Trop_low", 2:"Trop_high", 3:"Sub-trop_warm", 4:"Sub-trop_mod_cool", 
                        5:"Sub-trop_cool", 6:"Temp_mod", 7:"Temp_cool", 8:"Bor_cold_noPFR", 
                        9:"Bor_cold_PFR", 10:"Arctic"}, errors="raise")
dus_soil_raw = dus_soil_raw.rename(columns={1:"S1_very_steep", 2:"S2_hydro_soil", 3:"S3_no-slight_lim", 4:"S4_moderate_lim", 
                        5:"S5_severe_lim", 6:"L1_irr", 7:"L2_water"}, errors="raise")
#######LOG#########
dus_mst_log = dus_mst_log.rename(columns={1:"LGP<60days", 2:"60-120days", 3:"120-180days", 4:"180-225days",
                                  5:"225-270days", 6:"270-365days", 7:"365+days"}, errors="raise")
dus_thz_log = dus_thz_log.rename(columns={1:"Trop_low", 2:"Trop_high", 3:"Sub-trop_warm", 4:"Sub-trop_mod_cool", 
                        5:"Sub-trop_cool", 6:"Temp_mod", 7:"Temp_cool", 8:"Bor_cold_noPFR", 
                        9:"Bor_cold_PFR", 10:"Arctic"}, errors="raise")
dus_soil_log = dus_soil_log.rename(columns={1:"S1_very_steep", 2:"S2_hydro_soil", 3:"S3_no-slight_lim", 4:"S4_moderate_lim", 
                        5:"S5_severe_lim", 6:"L1_irr", 7:"L2_water"}, errors="raise")
#merge the two dummy dataframes with the rest of the variables
####RAW#########
dsoyb_d_raw = pd.concat([ds0_raw, dus_mst_raw, dus_thz_raw, dus_soil_raw], axis='columns')
######LOG#########
dsoyb_d = pd.concat([ds0_log, dus_mst_log, dus_thz_log, dus_soil_log], axis='columns')
#drop the original mst and thz colums as well as one column of each dummy (this value will be encoded by 0 in all columns)
#####RAW#####
dsoyb_dus_raw = dsoyb_d_raw.drop(['mst_class', 'thz_class', 'soil_class', 'LGP<60days', 
                      'Arctic', 'L2_water'], axis='columns')
########LOG#######
dsoyb_dus_log = dsoyb_d.drop(['mst_class', 'thz_class', 'soil_class', 'LGP<60days', 
                      'Arctic', 'L2_water'], axis='columns')

#select a random sample of 20% from the dataset to set aside for later validation
#random_state argument ensures that the same sample is returned each time the code is run
dsoyb_val_raw = dsoyb_dus_raw.sample(frac=0.2, random_state=2705) #RAW
dsoyb_val_log = dsoyb_dus_log.sample(frac=0.2, random_state=2705) #LOG
#drop the validation sample rows from the dataframe, leaving 80% of the data for fitting the model
dsoyb_fit_raw = dsoyb_dus_raw.drop(dsoyb_val_raw.index) #RAW
dsoyb_fit_log = dsoyb_dus_log.drop(dsoyb_val_log.index) #LOG

##################Collinearity################################

###########RAW#################

grid = sb.PairGrid(data= dsoyb_fit_raw,
                    vars = ['n_fertilizer', 'p_fertilizer', 'n_total',
                    'pesticides_H', 'mechanized', 'irrigation'], height = 4)
grid = grid.map_upper(plt.scatter, color = 'darkred')
grid = grid.map_diag(plt.hist, bins = 10, color = 'darkred', 
                     edgecolor = 'k')
grid = grid.map_lower(sb.kdeplot, cmap = 'Reds')
#wanted to display the correlation coefficient in the lower triangle but don't know how
#grid = grid.map_lower(corr)

sb.pairplot(dsoyb_dus_raw)

#extract lat, lon, area and yield from the fit dataset to test the correlations among the
#independent variables
dsoyb_cor_raw = dsoyb_fit_raw.drop(['lat', 'lon', 'area', 'yield'], axis='columns')
#one method to calculate correlations but without the labels of the pertaining variables
#spearm = stats.spearmanr(dsoyb_cor_raw)
#calculates spearman (rank transformed) correlation coeficcients between the 
#independent variables and saves the values in a dataframe
sp = dsoyb_cor_raw.corr(method='spearman')
print(sp)
sp.iloc[0,1:5]
sp.iloc[1,2:5]
#very noticable correlations among the fertilizer variables (as expected)
#interestingly, also very high correlations between irrigation and fertilizer variables

############Variance inflation factor##########################

X = add_constant(dsoyb_cor_elim)
pd.Series([variance_inflation_factor(X.values, i) 
               for i in range(X.shape[1])], 
              index=X.columns)
'''
const                612.193929
p_fertilizer           7.363338
n_total                7.917247
pesticides_H           2.590643
mechanized             2.119105
irrigation_tot         1.957191
LGP<60days             1.198998
60-120days             7.563685
120-180days           32.774696
180-225days           27.607494
225-270days           34.432194
270-365days           48.825040
Trop_low              65.072167
Trop_high             10.020233
Sub-trop_warm         32.409264
Sub-trop_mod_cool     54.579184
Sub-trop_cool         22.285205
Temp_mod              72.864081
Temp_cool             57.230574
S1_very_steep          1.377248
S2_hydro_soil          1.305941
S3_no-slight_lim       3.779768
S4_moderate_lim        3.437620
S5_severe_lim          1.667338
dtype: float64
'''
######################TEST#########################

test_S = ds0_elim.drop(['lat', 'lon', 'area', 'Y',
                                        'n_fertilizer', 'n_manure', 'n_man_prod',
                                         'irrigation_rel'], axis='columns')
test_S['thz_class'] = test_S['thz_class'].replace([8],7)

test_S['mst_class'] = test_S['mst_class'].replace([2],1)
test_S['mst_class'] = test_S['mst_class'].replace([7],6)

plt.hist(ds0_elim['soil_class'])
bor_test = ds0_elim.loc[ds0_elim['thz_class'] == 8] #402

sd_mst = pd.get_dummies(test_S['mst_class'])
sd_thz = pd.get_dummies(test_S['thz_class'])

sd_mst = sd_mst.rename(columns={1:"LGP<120days", 3:"120-180days", 4:"180-225days",
                                  5:"225-270days", 6:"270+days"}, errors="raise")
sd_thz = sd_thz.rename(columns={1:"Trop_low", 2:"Trop_high", 3:"Sub-trop_warm", 4:"Sub-trop_mod_cool", 5:"Sub-trop_cool", 
                                6:"Temp_mod", 7:"Temp_cool+Bor+Arctic"}, errors="raise")
test_S = pd.concat([test_S, sd_mst, sd_thz, dus_soil_elim], axis='columns')
#drop the original mst and thz colums as well as one column of each dummy (this value will be encoded by 0 in all columns)
test_S.drop(['270+days','Temp_cool+Bor+Arctic', 'L1_irr'], axis='columns', inplace=True)

test_cor_elim = test_S.drop(['thz_class','mst_class', 'soil_class'], axis='columns')

#drop dummy variables
cor_test = test_cor_elim.loc[:,['n_manure', 'mechanized', 'thz_class', 'mst_class', 
                                   'soil_class']]
X2 = add_constant(test_cor_elim)
pd.Series([variance_inflation_factor(X2.values, i) 
               for i in range(X2.shape[1])], 
              index=X2.columns)

plt.hist(test_S['mst_class'], bins=50)
ax = sb.boxplot(x=test_S["mst_class"], y=ds0_elim['Y'])

'''
mst_test

const                419.487852
p_fertilizer           7.246404
n_total                7.926835
pesticides_H           2.617275
mechanized             2.163745
irrigation_tot         1.955850
LGP<120days            1.146611
120-180days            1.667726
180-225days            1.566184
225-270days            1.500514
Trop_low              65.318937
Trop_high             10.107534
Sub-trop_warm         32.421119
Sub-trop_mod_cool     54.508114
Sub-trop_cool         22.403122
Temp_mod              72.869393
Temp_cool             57.306265
S1_very_steep          1.379139
S2_hydro_soil          1.305177
S3_no-slight_lim       3.786238
S4_moderate_lim        3.442297
S5_severe_lim          1.671948
dtype: float64

thz_test

const                40.379846
p_fertilizer          7.244317
n_total               7.922601
pesticides_H          2.610407
mechanized            2.163687
irrigation_tot        1.955759
LGP<120days           1.146552
120-180days           1.667719
180-225days           1.558867
225-270days           1.500510
Trop_low              3.085479
Trop_high             1.246571
Sub-trop_warm         1.786493
Sub-trop_mod_cool     2.225860
Sub-trop_cool         1.586660
Temp_mod              1.935220
S1_very_steep         1.379096
S2_hydro_soil         1.305151
S3_no-slight_lim      3.785709
S4_moderate_lim       3.442216
S5_severe_lim         1.671891
dtype: float64
'''


######################Regression##############################

#R-style formula
#doesn't work for some reason... I always get parsing errors and I don't know why
mod = smf.ols(formula=' yield ~ n_total + pesticides_H + mechanized + irrigation', data=dsoyb_fit_raw)

mod = smf.ols(formula='yield ~ n_fertilizer + pesticides_H + mechanized + irrigation', data=dsoyb_fit_raw)

#use patsy to create endog and exog matrices in an Rlike style
y, X = dmatrices('yield ~ n_fertilizer + pesticides_H + mechanized + irrigation', data=dsoyb_fit_raw, return_type='dataframe')


#define x and y dataframes
#Y containing only yield
mop = ds0_raw.iloc[:,3]
m_endog_raw = dsoyb_fit_raw.iloc[:,3] #RAW
m_endog_log = dsoyb_fit_log.iloc[:,3] #LOG
#X containing all variables
m_exog = ds0_raw.iloc[:,4]
m_exog_alln_raw = dsoyb_fit_raw.drop(['yield', 'lat', 'lon', 'area', 'n_total'], axis='columns') #RAW
m_exog_alln_log = dsoyb_fit_log.drop(['yield', 'lat', 'lon', 'area', 'n_total'], axis='columns') #LOG
#test with n total and p
m_exog_np_raw = dsoyb_fit_raw.drop(['yield', 'lat', 'lon', 'area', 'n_fertilizer', 'n_manure'], axis='columns') #RAW
m_exog_np_log = dsoyb_fit_log.drop(['yield', 'lat', 'lon', 'area', 'n_fertilizer', 'n_manure'], axis='columns')  #LOG
#test with n total without p
m_exog_n_log = dsoyb_fit_raw.drop(['yield', 'lat', 'lon', 'area', 'n_fertilizer', 'n_manure', 'p_fertilizer'], axis='columns') #RAW
m_exog_n_raw = dsoyb_fit_log.drop(['yield', 'lat', 'lon', 'area', 'n_fertilizer', 'n_manure', 'p_fertilizer'], axis='columns') #LOG
#I will move forward with n_total and without p probably as they seem to be highly
#correlated

####testing regression
#determining the models
###RAW###
mod = sm.OLS(mop, m_exog)
mod_alln_raw = sm.OLS(m_endog_raw, m_exog_alln_raw)
mod_np_raw = sm.OLS(m_endog_raw, m_exog_np_raw)
mod_n_raw = sm.OLS(m_endog_raw, m_exog_n_log)
###LOG
mod_alln_log = sm.OLS(m_endog_log, m_exog_alln_log)
mod_np_log = sm.OLS(m_endog_log, m_exog_np_log)
mod_n_log = sm.OLS(m_endog_log, m_exog_n_raw)
####LOG DEPENDENT####
mod_alln_mix = sm.OLS(m_endog_log, m_exog_alln_raw)
mod_np_mix = sm.OLS(m_endog_log, m_exog_np_raw)
mod_n_mix = sm.OLS(m_endog_log, m_exog_n_log)

#fitting the models
#####RAW#####
mod_x = mod.fit()
mod_res_alln_raw = mod_alln_raw.fit(method='qr')
mod_res_np_raw = mod_np_raw.fit()
mod_res_n_raw = mod_n_raw.fit()
####LOG####
mod_res_alln_log = mod_alln_log.fit(method='qr')
mod_res_np_log = mod_np_log.fit()
mod_res_n_log = mod_n_log.fit()
####LOG DEPENDENT####
mod_res_alln_mix = mod_alln_mix.fit()
mod_res_np_mix = mod_np_mix.fit(method='qr')
mod_res_n_mix = mod_n_mix.fit()

#printing the results
print(mod_x.summary())
print(mod_res_alln_raw.summary())
print(mod_res_np_raw.summary())
print(mod_res_n_raw.summary())


print(mod_res_n_log.summary())

print(mod_res_alln_mix.summary())
print(mod_res_np_mix.summary())
print(mod_res_n_mix.summary())


##########RESIDUALS#############



plt.scatter(mod_res_n_raw.resid_pearson)
sb.residplot(x=m_exog_n_log, y=m_endog_log)





'''
#calculations on percentage of mechanized and non-mechanized, don't work anymore with the new tillage codification
mech = dsoyb_nozero['mechanized']
mech_total = mech.sum()
nonmech = dsoyb_nozero['non-mechanized']
non_mech_total = nonmech.sum()
total = mech_total + non_mech_total
mech_per = mech_total / total * 100
non_mech_per = non_mech_total / total * 100


#einfach nur für die iloc sachen drin
#drop lat, lon and area from the dataframe to only include relevant variables
dsoyb_rg = dsoyb_fit.iloc[:,[3,4,5,7,8,9,10]]
dsoyb_pl = dsoyb_fit.iloc[:,[4,5,7,8,9,10]]
dsoyb_yield = dsoyb_fit.iloc[:,3]

mod1 =sm.GLM(dsoyb_yield, dsoyb_pl, family=sm.families.Gamma())
#for some reason it works with Gaussian and Tweedie but not with Gamma or Inverse Gaussian... I really don't know why
mod_results = mod1.fit()
mod_res_alln_log = mod2.fit(method='qr')
    
'''
 


#use patsy to create endog and exog matrices in an Rlike style
y, X = dmatrices('yield ~ n_fertilizer + pesticides_H + mechanized + irrigation', data=dsoyb_rg, return_type='dataframe')


