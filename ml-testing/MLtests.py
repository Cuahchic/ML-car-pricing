# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 11:21:57 2017

@author: ColinParr

Testing the ML-components
"""
# Required libraries
from cassandra.cluster import Cluster
import pandas as pd
import datetime
import seaborn as sns

import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score

cluster = Cluster()                         # Connect to local host on default port 9042
session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace

# In this section get all unique searches and adverts so we can iterate through them
cql = 'SELECT DISTINCT searchname, advertid FROM car_pricing.searchdata;'

prepStatement = session.prepare(cql)
queryResults = session.execute(prepStatement)

df_adIDs = pd.DataFrame({'SearchName': [], 'AdvertID': []})

for qr in queryResults:
    df_adIDs = df_adIDs.append(pd.DataFrame({'SearchName': [str(qr[0])], 'AdvertID': [str(qr[1])]}))  # Put results into a Panda for manipulation

# Get unique searches so the user can filter this on the visualisation
searchNames = list(df_adIDs['SearchName'].unique())
searchName = searchNames[0]

# List columns we want to use as features (or to create features from) and build up cql query
colList = ['advertid', 'foundtime', 'year', 'plate', 'bodytype', 'mileage', 'transmission', 'enginesize', 'bhp', 'fueltype', 'price', 'sellertype', 'make', 'model', 'dealername', 'features', 'averagempg']
cql = 'SELECT ' + ','.join(colList) + ' FROM car_pricing.searchdata WHERE searchname = ? AND advertid = ? LIMIT 1;'

prepStatement = session.prepare(cql)

# Create data frame to store results
df_searchData = pd.DataFrame(columns = colList)

for adID in df_adIDs[df_adIDs['SearchName'] == 'Local automatics']['AdvertID']:     # Query to get the latest information (latest data gathering time) for each advert
    queryResults = session.execute(prepStatement, [searchName, adID])
    
    df_searchData = df_searchData.append(pd.DataFrame(data = [list(queryResults[0])], columns = colList))   # Note that list is embedded in another list
    

# Create additional features for ML work
# Calculate the age of the advert
def compare_dates(advertid):
    date = datetime.datetime.strptime(advertid[0:8], '%Y%m%d')    
    today = datetime.datetime.now()
    diff = today - date
    return diff.days
    
df_searchData['advertage_days'] = df_searchData['advertid'].apply(compare_dates)


# Let's do some initial data exploration
sns.regplot(x = 'mileage', y = 'price', data = df_searchData, fit_reg = False)
sns.regplot(x = 'advertage_days', y = 'price', data = df_searchData, fit_reg = False)
plt = sns.swarmplot(x = 'make', y = 'price', data = df_searchData)
plt.set_xticklabels(plt.get_xticklabels(), rotation = 90)


# Let's start doing some ML
# One hot encode categorical columns so we only have numbers
X = pd.get_dummies(df_searchData, dummy_na = False, columns = ['bodytype', 'fueltype', 'make', 'model', 'sellertype'])
X.drop(['advertid', 'foundtime', 'transmission', 'dealername', 'features'], axis = 1, inplace = True)   # Lose columns which are not good features (axis=1 is columns)
X = X[X.notnull().all(axis = 1)]        # Remove any adverts which have NaN, None or other non-numerical elements in their feature columns
Y = X['price']
X.drop(['price'], axis = 1, inplace = True)

X, Y = shuffle(X, Y)                    # Randomise the order of the rows

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = 0.05, random_state = 32)

rf = RandomForestRegressor(n_estimators = 500, max_features = 'sqrt')
rf = rf.fit(X_train, Y_train)
Y_pred_rf = rf.predict(X_test)
scores_rf = cross_val_score(rf, X_test, Y_test, cv = 3, scoring = 'r2')

gbc = GradientBoostingRegressor(loss = 'huber', n_estimators = 500, max_features = 'sqrt')
gbc = gbc.fit(X_train, Y_train)
Y_pred_gbc = gbc.predict(X_test)
scores_gbc = cross_val_score(gbc, X_test, Y_test, cv = 3)

sns.regplot(x = Y_test, y = Y_pred_rf, fit_reg = False)
sns.regplot(x = Y_test, y = Y_pred_gbc, fit_reg = False)











