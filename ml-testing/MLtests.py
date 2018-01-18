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

from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Normalizer
from sklearn.preprocessing import MinMaxScaler

from sklearn.model_selection import GridSearchCV

from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor

from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score

from ggplot import ggplot, aes, geom_point

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
searchName = searchNames[1]

# List columns we want to use as features (or to create features from) and build up cql query
colList = ['advertid', 'foundtime', 'year', 'plate', 'bodytype', 'mileage', 'transmission', 'enginesize', 'bhp', 'fueltype', 'price', 'sellertype', 'make', 'model', 'dealername', 'features', 'averagempg']
cql = 'SELECT ' + ','.join(colList) + ' FROM car_pricing.searchdata WHERE searchname = ? AND advertid = ? LIMIT 1;'

prepStatement = session.prepare(cql)

# Create data frame to store results
df_searchData = pd.DataFrame(columns = colList)

for adID in df_adIDs[df_adIDs['SearchName'] == searchName]['AdvertID']:     # Query to get the latest information (latest data gathering time) for each advert
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
ggplot(df_searchData, aes(x='mileage', y='price')) + geom_point()
ggplot(df_searchData, aes(x='advertage_days', y='price')) + geom_point()
plt = sns.swarmplot(x = 'make', y = 'price', data = df_searchData)      # No ggplot equivalent for this chart type that I can find
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

# Predictions using random forest regression
rf_params = {'n_estimators': [10, 50, 100, 500, 1000],
             'criterion': ['mse'],
             'max_features': [None, 'sqrt', 'log2'],
             'min_samples_split': [2, 5, 10, 20]}
rf = RandomForestRegressor()
rf_gscv = GridSearchCV(rf, rf_params)
rf_gscv = rf_gscv.fit(X_train, Y_train)
Y_pred_rf = rf_gscv.predict(X_test)
scores_rf = cross_val_score(rf_gscv, X_test, Y_test, cv = 3, scoring = 'r2')
r2_rf = r2_score(Y_test, Y_pred_rf)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_rf}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using gradient boosted regression
gbc_params = {'loss': ['huber'],
              'n_estimators': [500, 1000, 5000],
              'max_features': [None, 'sqrt', 'log2'],
              'min_samples_split': [2, 5, 10, 20],
              'alpha': [0.1, 0.5, 0.9]}
gbc = GradientBoostingRegressor()
gbc_gscv = GridSearchCV(gbc, gbc_params)
gbc_gscv = gbc_gscv.fit(X_train, Y_train)
Y_pred_gbc = gbc_gscv.predict(X_test)
scores_gbc = cross_val_score(gbc, X_test, Y_test, cv = 3, scoring = 'r2')
r2_gbc = r2_score(Y_test, Y_pred_gbc)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_gbc}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using k-Nearest Neighbours (no dimesnionality reduction or scaling)
knn_params = {'n_neighbors': [2, 5, 10],
              'weights': ['uniform', 'distance'],
              'algorithm': ['ball_tree', 'kd_tree', 'brute']}
knnr = KNeighborsRegressor()
knnr_gscv = GridSearchCV(knnr, knn_params)
knnr_nored_noscale_gscv = knnr_gscv.fit(X_train, Y_train)
Y_pred_knnr_nored_noscale = knnr_nored_noscale_gscv.predict(X_test)
scores_knnr_nored_noscale = cross_val_score(knnr, X_test, Y_test, cv = 3, scoring = 'r2')
r2_knnr_nored_noscale = r2_score(Y_test, Y_pred_knnr_nored_noscale)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_knnr_nored_noscale}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using k-Nearest Neighbours (no dimesnionality reduction but standard scaling)
x_scale_std = StandardScaler().fit(X)   # No need to scale Y values

knnr_nored_stdscale_gscv = knnr_gscv.fit(x_scale_std.transform(X_train), Y_train)
Y_pred_knnr_nored_stdscale = knnr_nored_stdscale_gscv.predict(x_scale_std.transform(X_test))
scores_knnr_nored_stdscale = cross_val_score(knnr, x_scale_std.transform(X_test), Y_test, cv = 3, scoring = 'r2')
r2_knnr_nored_stdscale = r2_score(Y_test, Y_pred_knnr_nored_stdscale)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_knnr_nored_stdscale}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using k-Nearest Neighbours (no dimesnionality reduction but normalised scaling)
x_scale_norm = Normalizer().fit(X)   # No need to scale Y values

knnr_nored_normscale_gscv = knnr_gscv.fit(x_scale_norm.transform(X_train), Y_train)
Y_pred_knnr_nored_normscale = knnr_nored_normscale_gscv.predict(x_scale_norm.transform(X_test))
scores_knnr_nored_normscale = cross_val_score(knnr, x_scale_norm.transform(X_test), Y_test, cv = 3, scoring = 'r2')
r2_knnr_nored_normscale = r2_score(Y_test, Y_pred_knnr_nored_normscale)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_knnr_nored_normscale}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using k-Nearest Neighbours (no dimesnionality reduction but MinMax scaling)
x_scale_minmax = MinMaxScaler().fit(X)   # No need to scale Y values

knnr_nored_minmaxscale_gscv = knnr_gscv.fit(x_scale_minmax.transform(X_train), Y_train)
Y_pred_knnr_nored_minmaxscale = knnr_nored_minmaxscale_gscv.predict(x_scale_minmax.transform(X_test))
scores_knnr_nored_minmaxscale = cross_val_score(knnr, x_scale_minmax.transform(X_test), Y_test, cv = 3, scoring = 'r2')
r2_knnr_nored_minmaxscale = r2_score(Y_test, Y_pred_knnr_nored_minmaxscale)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_knnr_nored_minmaxscale}), aes(x='actual', y='predicted')) + geom_point()

# Predictions using k-Nearest Neighbours (PCA dimesnionality reduction and MinMax scaling)
pca = PCA()

knnr_nored_minmaxscale_gscv = knnr_gscv.fit(x_scale_minmax.transform(X_train), Y_train)
Y_pred_knnr_nored_minmaxscale = knnr_nored_minmaxscale_gscv.predict(x_scale_minmax.transform(X_test))
scores_knnr_nored_minmaxscale = cross_val_score(knnr, x_scale_minmax.transform(X_test), Y_test, cv = 3, scoring = 'r2')
r2_knnr_nored_minmaxscale = r2_score(Y_test, Y_pred_knnr_nored_minmaxscale)
sns.regplot(x = Y_test, y = Y_pred_knnr_nored_minmaxscale, fit_reg = False)
ggplot(pd.DataFrame({'actual': Y_test, 'predicted': Y_pred_knnr_nored_minmaxscale}), aes(x='actual', y='predicted')) + geom_point()


























