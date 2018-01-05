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

from flask import Flask, jsonify, render_template
from cassandra.cluster import Cluster

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
    
    response = jsonify({"searches": list(searches)})
    
    return response


# This API gets all the data required in the front end
@app.route('/api/getdata/<string:searchname>', methods=['GET'])
def getdata(searchname):
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
    
    response = jsonify({"searches": list(searches)})
    
    return response    


# Main code
if __name__ == '__main__':
     app.run(threaded=True, port=65010, debug=True)
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     