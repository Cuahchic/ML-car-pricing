# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 11:21:57 2017

@author: ColinParr

Testing the ML-components
"""
# Required libraries
from cassandra.cluster import Cluster
import pandas as pd

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
    
    df_searchData = df_searchData.append(pd.DataFrame(data = list(queryResults[0]), columns = colList))
    
