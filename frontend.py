# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 14:24:51 2018

@author: colin
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:32:43 2017

@author: ColinParr
"""

from flask import Flask, jsonify, render_template, send_file, request
from cassandra.cluster import Cluster
from cassandra.util import OrderedMapSerializedKey
from urllib import parse
import pandas as pd
import datetime
import io

app = Flask(__name__)


@app.route('/cars')
def homepage():
    return render_template('carprices.html', title = 'Car prices')


# This API lists all the unique searches that are available
@app.route('/api/listsearches', methods=['GET'])
def listsearches():
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    
    cql = 'SELECT DISTINCT searchname, advertid FROM car_pricing.searchdata;'

    prepStatement = session.prepare(cql)
    queryResults = session.execute(prepStatement) 
    
    searches = set()
    for qr in queryResults:
        searches.add(qr[0])
    
    session.shutdown()
    cluster.shutdown()
    
    response = jsonify({"searches": sorted(list(searches))})
    
    return response


# This API gets all the data required in the front end
@app.route('/api/getdata/<string:searchname>', methods=['GET'])
def getdata(searchname):
    searchname = parse.unquote(searchname)      # Decode URL, e.g. turn %20 into space etc
    
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    
    # Get adIDs into list related to our search name
    cql = 'SELECT DISTINCT searchname, advertid FROM car_pricing.searchdata;'

    prepStatement = session.prepare(cql)
    queryResults = session.execute(prepStatement)
    
    adIDs = []
    for qr in queryResults:
        if qr[0] == searchname:     # If this is a result from our desired search then add it to the list
            adIDs.append(qr[1])
    
    # List columns we want to use as features (or to create features from) and build up cql query
    colListOther = ['advertid', 'plate', 'bodytype', 'transmission', 'fueltype', 'sellertype', 'make', 'model', 'dealername', 'location', 'searchcriteria', 'distancefromyou', 'features', 'adtitle', 'foundtime']
    colListPlottable = ['year', 'mileage', 'enginesize', 'bhp', 'price', 'averagempg']
    colListPlottableFriendly = ['Registration Year', 'Mileage (miles)', 'Engine Size (L)', 'Engine Power (BHP)', 'Price (£)', 'Avg. Fuel Consumpt. (mpg)']
    cql = 'SELECT ' + ','.join(colListPlottable + colListOther) + ' FROM car_pricing.searchdata WHERE searchname = ? AND advertid = ? LIMIT 1;'
    
    prepStatement = session.prepare(cql)
    
    # Create data frame to store results
    df_D3data = pd.DataFrame(columns = (colListPlottable + colListOther))
    
    for adID in adIDs:     # Query to get the latest information (latest data gathering time) for each advert
        queryResults = session.execute(prepStatement, [searchname, adID])
        
        #df_D3data = df_D3data.append(pd.DataFrame(data = [list(queryResults[0])], columns = (colListPlottable + colListOther)))   # Note that list is embedded in another list
        df_D3data = df_D3data.append(pandas_factory((colListPlottable + colListOther), queryResults))
        
    # Add advert age to the data frame
    df_D3data['advertage_days'] = df_D3data['advertid'].apply(compare_dates)
    colListPlottable += ['advertage_days']
    colListPlottableFriendly += ['Advert Age (days)']
    
    session.shutdown()
    cluster.shutdown()
    
    # Remove any points which are not valid, i.e. NaN, None, etc
    df_D3data = df_D3data[df_D3data.notnull().all(axis = 1)]
    
    df_D3data = df_D3data.reset_index()     # Required to generate index for DF so that it can be turned into JSON
    
    # Prepare columns for output by sorting in alphabetical order and putting into dictionary for output
    colListPlottableFriendly, colListPlottable = (list(x) for x in zip(*sorted(zip(colListPlottableFriendly, colListPlottable), key = lambda pair: pair[0]))) # Taken from https://stackoverflow.com/questions/13668393/python-sorting-two-lists    
    colOutputList = [{'name': n, 'friendly_name': fn} for n, fn in zip(colListPlottable, colListPlottableFriendly)]
    
    response = jsonify({'data': df_D3data.to_dict(orient = 'records'),
                        'plottable_columns': colOutputList})
    
    return response    


# Calculate the age of the advert
def compare_dates(advertid):
    date = datetime.datetime.strptime(advertid[0:8], '%Y%m%d')    
    today = datetime.datetime.now()
    diff = today - date
    return diff.days


# This API returns an image from a specified advert
@app.route('/api/adimage', methods=['GET'])
def getimage():
    # See https://stackoverflow.com/questions/15182696/multiple-parameters-in-in-flask-approute to understand the requests logic below
    searchname = request.args.get('searchname', None)
    adID = request.args.get('adid', None)
    
    searchname = parse.unquote(searchname)      # Decode URL, e.g. turn %20 into space etc
    
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    
    # Get adIDs into list related to our search name
    cql = 'SELECT thumbnail FROM car_pricing.searchdata WHERE searchname = ? AND advertid = ?;'

    prepStatement = session.prepare(cql)
    queryResults = session.execute(prepStatement, [searchname, adID])
    
    image_binary = None
    for qr in queryResults:
        image_binary = qr[0]
    
    session.shutdown()
    cluster.shutdown()
    
    return send_file(io.BytesIO(image_binary),
                     attachment_filename = 'car.jpg',
                     mimetype = 'image/jpg')
    

# Convert results into data frame including any maps (stolen from https://stackoverflow.com/questions/42420260/how-to-convert-cassandra-map-to-pandas-dataframe)
def pandas_factory(colnames, rows):
    # Convert tuple items of 'rows' into list (elements of tuples cannot be replaced)
    rows = [list(i) for i in rows]

    # Convert only 'OrderedMapSerializedKey' type list elements into dict
    for idx_row, i_row in enumerate(rows):

        for idx_value, i_value in enumerate(i_row):

            if type(i_value) is OrderedMapSerializedKey:

                rows[idx_row][idx_value] = dict(rows[idx_row][idx_value])

    return pd.DataFrame(rows, columns=colnames)


# Main code
if __name__ == '__main__':
     app.run(threaded=True, port=65010, debug=True)
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     