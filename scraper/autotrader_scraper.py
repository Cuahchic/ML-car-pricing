# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 14:02:06 2017

@author: ColinParr

This is used to scrape car results from Autotrader and analyse them using ML
"""
# Required libraries
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random
import datetime
import requests
import re
import time
from re import sub
from decimal import Decimal
import socket
import sys
from urllib.parse import urlparse, parse_qs
from cassandra.cluster import Cluster
import traceback
import copy
import pandas as pd


# Create a class that we can use to track everything we want to save from each advert
class advert:
    def __init__(self):
        self.features = {}
        self.colList = ['year', 'plate', 'bodytype', 'mileage', 'enginesize', 'bhp', 'fueltype', 'sellertype', 'make', 'model', 'averagempg']
    
    def dataFrame(self):
        d = {}
        for c in self.colList:
            d[c] = self.features[c]
        
        return pd.DataFrame([d])


# Create a class to store our search criteria so we can pass it around
class searchCriteria:
    def __init__(self, name, params):
        # Set up all the search parameters, note that many of these are case sensitive
        self.searchName = name
        self.params = params
        self.translations = {'Miles From': 'radius',
                             'Postcode': 'postcode',
                             'Car Types': 'onesearchad',
                             'Make': 'make',
                             'Model': 'model',
                             'Model Variant': 'aggregatedTrim',
                             'Price From': 'price-from',
                             'Price To': 'price-to',
                             'Year From': 'year-from',
                             'Year To': 'year-to',
                             'Mileage From': 'minimum-mileage',
                             'Mileage To': 'maximum-mileage',
                             'Body Types': 'body-type',
                             'Fuel Type': 'fuel-type',
                             'Fuel Consumption': 'fuel-consumption',
                             'Engine Size From': 'minimum-badge-engine-size',
                             'Engine Size To': 'maximum-badge-engine-size',
                             'Transmission': 'transmission',
                             'Keywords': 'keywords'}   
        self.searchURL = urlBuilder(self.params, self.translations)
        self.refinedURLs = urlRefiner(self.searchURL, self.params, self.translations)
    
    
# Takes the search criteria selected by the user and builds the Autotrader URL to scrape
def urlBuilder(params, translations):
    outputURL = 'https://www.autotrader.co.uk/car-search?sort=price-asc'   # Always sort ascending order in price
    
    for p in params.keys():
        APIparam = translations[p]
        APIparam = '&' + APIparam + '='
        val = params[p]
        vals = val.split(',')
        
        for v in vals:
            outputURL = outputURL + APIparam + v

    return outputURL


# Takes the URL created and splits it down so that all the results are able to be displayed, Autotrader limits you to about 100 pages of results
def urlRefiner(startSearchURL, params, translations):
    refinedURLs = []
    
    # Start with the basic URL, this might work
    currentParams = copy.deepcopy(params)   # By default dictionaries are only copied as pointers so the original is modified
    pagesLimit = 95
    splitSize = 2
    ua = UserAgent()
    
    # Get response based on initial URL
    response = requests.get(startSearchURL, headers = {'User-Agent': ua.random})

    # Create soup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust max pages and list of makes if this is the first run
    maxPages = findMaxPages(soup)
    
    if maxPages <= pagesLimit:
        refinedURLs.append(startSearchURL)
    else:
        if 'Price From' not in currentParams: # If no price from is specified then use the lowest in the drop down on the page
            sel = soup.find('select', attrs = {'name': 'price-from'})
            opt = sel.findAll('option')
            minPriceFrom = min([int(o['value']) for o in opt if o['value'] != ''])
        else:
            minPriceFrom = int(currentParams['Price From'])
        
        if 'Price To' not in currentParams: # If no price from is specified then use the highest in the drop down on the page
            sel = soup.find('select', attrs = {'name': 'price-to'})
            opt = sel.findAll('option')
            maxPriceFrom = max([int(o['value']) for o in opt if o['value'] != ''])
        else:
            maxPriceFrom = int(currentParams['Price To'])
            
        step = (maxPriceFrom - minPriceFrom) / splitSize
        
        for i in range(0, splitSize):
            currentParams['Price From'] = str(int(minPriceFrom + (step * i)) + (1 if i > 0 else 0))
            currentParams['Price To'] = str(int(minPriceFrom + (step * (i + 1))))
            
            ri = random.randint(2, 6)
            print('Figuring out the refined URLs, going for a ' + str(ri) + ' seconds sleep.')
            time.sleep(ri)
            
            refinedURLs = refinedURLs + urlRefiner(urlBuilder(currentParams, translations), currentParams, translations)
            
    return refinedURLs                


# This class stores all the metadata we need for running the program
class metadata:
    def __init__(self):
        self.sessionCreatedTime = datetime.datetime.now()
        self.user_agent = None #pickAgent()
        self.maxPages = 1   # Starts at 1 then is updated later using while loop
        
        pythVersionRegex = re.compile(r'[^|]*')
        pythVersion = pythVersionRegex.search(sys.version)[0].strip()
        self.pythonVersion = pythVersion
        
        self.codeVersion = '1.0.0'
        self.hostName = socket.gethostname()


# Find the maximum number of pages from a search result page
def findMaxPages(soup):
    pagination = soup.find('li', attrs = {'class': 'paginationMini__count'})
    
    maxPages = 0
    
    if len(pagination) > 0:
        rPag = re.compile(r'\d+$')
        rPagResult = rPag.search(pagination.text.strip())
        
        if rPagResult != None:
            maxPages = int(rPagResult[0])
    
    return maxPages


# Take a single results page and scrape it for the relevant information we want to get back, returns a list of objects
def parsePage(soup, md, ua, makesRegex, log):
    resultsListToReturn = []
    
    pageResults = soup.findAll('li', attrs = {'class': 'search-page__result'})
    
    for j in range(0, len(pageResults)):
        if pageResults[j].find('span', attrs = {'class': 'listings-standout'}) == None: # Adverts with this span class are adverts and should not be included in our results
            # Make a random delay to confuse any bot detection algorithms now that we are loading sub pages from here
            msg = 'Advert: ' + str(j + 1) + ' of ' + str(len(pageResults)) + '.'
            log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
            print(msg)
            if j > 0:
                ri = random.randint(6, 12)
                msg = 'Having a wee ' + str(ri) + ' seconds rest while I load the advert page.'
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                print(msg)
                time.sleep(ri)
            
            
            
            # Create advert object to store findings
            ad = advert()
            
            ad.features['adverthtml'] = str(pageResults[j])
            ad.features['foundtime'] = datetime.datetime.now()
            
            contentCol = pageResults[j].find('section', attrs = {'class': 'content-column'})
            priceCol = pageResults[j].find('section', attrs = {'class': 'price-column'})
            
            ad.features['advertid']= pageResults[j].get('id')
            ad.features['adtitle'] = contentCol.find('h2', attrs = {'class': 'listing-title title-wrap'}).text.strip()
            ad.features['attentiongrab'] = contentCol.find('p', attrs = {'class': 'listing-attention-grabber'}).text.strip()
            
            # Get unnamed list of attributes
            liTags = contentCol.find('ul', attrs = {'class': 'listing-key-specs'}).findAll('li')
            
            # Regexii for sanity checking the list
            rYear = re.compile(r'(\d+)( \(\d+ reg\))?')
            rPlate = re.compile(r'\d+')
            rBodyTypes = re.compile(r'(convertible|coupe|estate|hatchback|mpv|other|suv|saloon|unlisted)')
            rMileage = re.compile(r'\d+(,\d+)? miles')
            rTransmission = re.compile(r'(manual|automatic)')
            rEngineSizeLitres = re.compile(r'\d+\.\d+l')
            rHorsepowerBHP = re.compile(r'\d+ bhp')
            rFuelType = re.compile(r'(petrol|diesel|electric|hybrid)')
            
            for li in liTags:                   
                if rBodyTypes.search(li.text.lower()) != None:
                    ad.features['bodytype'] = li.text
                elif rMileage.search(li.text.lower()) != None:
                    ad.features['mileage'] = int(li.text.replace(' miles', '').replace(',', ''))
                elif rTransmission.search(li.text.lower()) != None:
                    ad.features['transmission'] = li.text
                elif rEngineSizeLitres.search(li.text.lower()) != None:
                    ad.features['enginesize'] = float(li.text.replace('L', ''))
                elif rHorsepowerBHP.search(li.text.lower()) != None:
                    ad.features['bhp'] = int(li.text.replace(' bhp', ''))
                elif rFuelType.search(li.text.lower()) != None:
                    ad.features['fueltype'] = li.text
                elif rYear.search(li.text.lower()) != None:
                    rYearMatches = rYear.match(li.text.lower())
                    
                    if int(rYearMatches.groups()[0]) > 1980:    # Have a sensible cutoff for year to prevent mismatching
                        ad.features['year'] = int(rYearMatches.groups()[0])
                        
                        fullPlate = rYearMatches.groups()[1]    # This is the group that says ' (66 reg)' for example, we need to extract the number
                        if fullPlate != None:
                            rPlateMatches = rPlate.search(fullPlate)                            
                            ad.features['plate'] = int(rPlateMatches[0])
            
            # Get car price information
            currencyString = priceCol.find('div', attrs = {'class': 'vehicle-price'}).text
            ad.features['price'] = Decimal(sub(r'[^\d.]', '', currencyString))
            
            # Determine if trade or private seller
            sellerType = contentCol.find('div', attrs = {'class': 'seller-type'}).text.lower()
            rSellerType = re.compile(r'(trade|private)')
            ad.features['sellertype'] = rSellerType.search(sellerType)[0]
            
            # Get distance from specified postcode
            sellerLocation = contentCol.find('div', attrs = {'class': 'seller-location'})
            rSellerLocation = re.compile(r'\d+')
            ad.features['distancefromyou'] = int(rSellerLocation.search(sellerLocation.text)[0])
            
            # Get seller town using same bs4 tag as distance above (note that .span finds the first span tag within the parent element, and is shorthand for using .find when there is only one element of that type)
            if sellerLocation.span != None:
                ad.features['location'] = sellerLocation.span.text           
            
            # Get the thumbnail image of the car
            fig = contentCol.find('figure', attrs = {'class': 'listing-main-image'})
            
            imgSrc = fig.img['src']     # Get image url, but this contains resizing parameters
            
            urpa = urlparse(imgSrc)
            
            if parse_qs(urpa.query) != {}:      # Required because if an advert doesn't have a picture then there is a default "noimage" png returned which doesn't have the resizing parameters, we don't want to save this image
                imgID = parse_qs(urpa.query)['id'][0]   # Find the image id so that we can query that without the resizing nonsense
                
                imgSrc = imgSrc.replace(urpa.query, '')
                
                imgSrc = imgSrc + 'id=' + imgID
                
                imgReq = requests.get(imgSrc)
                
                thumbnail = None
                if imgReq.status_code == 200:
                    thumbnail = imgReq.content
                
                ad.features['thumbnail'] = thumbnail
            
            # Get the further detail from the actual advert page
            # NOTE: Python considers user defined classes mutable so ad is actually updated by this function call
            pageLevelInfo(md, ua, ad, makesRegex)
            
            # Add the advert to the overall list to be returned
            resultsListToReturn.append(ad)
        
    return resultsListToReturn


# This function takes an advert ID and loads the page so we can scrape more information
# NOTE: Python considers user defined classes mutable (changeable) so passes a pointer to the class. This means functions can update the object within the parent.
def pageLevelInfo(md, ua, ad, makesRegex):
    # Build up URL to load page
    baseURL = 'https://www.autotrader.co.uk/classified/advert/'
    advertURL = baseURL + ad.features['advertid']
    
    response = requests.get(advertURL, headers = {'User-Agent': ua.random})
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all the elements which could contain the information we want, need to validate with regex
    fpaSections = soup.findAll('div', attrs = {'class': 'fpaSpecifications__listItem'})
    
    # Get the regex ready to validate the list elements
    rMPG = re.compile(r'\d+\.\d+')
    rTax = re.compile(r'£(\d+)')
    
    for fpaSection in fpaSections:
        # Find the term which is effectively the key in the key-value pair
        divTerm = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__term'})
        
        if divTerm != None:
            if divTerm.text.lower() == 'urban mpg':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rMPGMatches = rMPG.match(desc)
                
                if rMPGMatches != None:
                    ad.features['urbanmpg'] = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'extra urban mpg':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rMPGMatches = rMPG.match(desc)
                
                if rMPGMatches != None:
                    ad.features['extraurbanmpg'] = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'average mpg':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rMPGMatches = rMPG.match(desc)
                
                if rMPGMatches != None:
                    ad.features['averagempg'] = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'annual tax':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rTaxMatches = rTax.match(desc)
                
                if rTaxMatches != None:
                    ad.features['annualtax'] = float(rTaxMatches.groups()[0])
    
    # Get the big comma separated list of deatures we can use with one-hot encoding later to predict the car price
    combinedFeatures = soup.find('section', attrs = {'class': 'combinedFeatures'})
    
    if combinedFeatures != None:
        featuresHeading = soup.find('h2', attrs = {'class': 'combinedFeatures__heading'}).text
        features = combinedFeatures.text
        ad.features['features'] = features.replace(featuresHeading, '').replace('\n', '')
    
    # Get the dealer name
    divDealer = soup.find('div', attrs = {'class': 'aboutDealer__name'})
    
    if divDealer != None:
        ad.features['dealername'] = divDealer.text.replace('\n', '').strip()
    
    # Find the make and extended model name
    rMakes = re.compile(makesRegex)
    
    ad.features['make'] = rMakes.match(ad.features['adtitle'].lower())[0]
    ad.features['modelfull'] = ad.features['adtitle'].lower().replace(ad.features['make'], '').strip()
    
    if 'enginesize' in ad.features:     # An electric car doesn't have an engine size
        if ad.features['enginesize'] > 0:
            rModelShort = re.compile('^(.*?)' + str(ad.features['enginesize']).replace('.', '\.'))  # Try looking for exact engine size in name
            rModelShort2 = re.compile('^(.*?)\d\.\d')                                    # Some cars say 2.1L but are actually 2.2L or whatever, so try generic engine size
            
            rModelMatches = rModelShort.match(ad.features['modelfull'])
            
            if rModelMatches == None:
                rModelMatches = rModelShort2.match(ad.features['modelfull'])
            
            if rModelMatches != None:
                ad.features['model'] = rModelMatches.groups()[0].strip()
            
    
# This function gets all the possible manufacturers from the options on the side
def buildMakesRegex(soup):
    makesDiv = soup.find('div', attrs = {'data-temp': 'make-flyout'})
    
    makesDivValueButtons = makesDiv.findAll('div', attrs = {'class': 'value-button'})
    
    makesList = [m.find('span', attrs = {'class': 'term'}).text.lower() for m in makesDivValueButtons]
    
    makesRegex = '|'.join(makesList)
    
    return makesRegex


# This function takes the results and puts it into a format that can be insetred into Cassandra
def buildOutputs(md, sc, ad):
    columnList = []
    valuesList = []
       
    if sc.searchName != '':
        columnList.append('searchname')
        valuesList.append(sc.searchName)
        
    if sc.params != {}:
        columnList.append('searchcriteria')
        valuesList.append(sc.params)
        
    if md.sessionCreatedTime != datetime.datetime(year = 1970, month = 1, day = 1):
        columnList.append('sessioncreatedtime')
        valuesList.append(md.sessionCreatedTime)
        
    if md.hostName != '':
        columnList.append('hostname')
        valuesList.append(md.hostName)
    
    if md.pythonVersion != '':
        columnList.append('pythonversion')
        valuesList.append(md.pythonVersion)
        
    if md.codeVersion != '':
        columnList.append('codeversion')
        valuesList.append(md.codeVersion)
    
    for k in ad.features.keys():
        columnList.append(k)
        valuesList.append(ad.features[k])
    
    return (columnList, valuesList)
    

# This function writes all the results we found into the postgres database
def writeResults(md, sc, masterResultsList):
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    
    rows = 0
    for ad in masterResultsList:
        (columnList, valuesList) = buildOutputs(md, sc, ad)
        
        cols = ','.join(columnList)
        placeholders = ['?' for x in columnList]    # List comprehension and string join is a tidy way to repeat a string the same number of times as another list
        placeholders2 = ','.join(placeholders)
        
        cql = 'INSERT INTO searchdata (' + cols + ') VALUES (' + placeholders2 + ');'
        
        prepStatement = session.prepare(cql)            # Prepared statement needs to stay inside of the loop as each advert has different available data so will be of differring length
        session.execute(prepStatement, valuesList)      # Need a loop here to handle each advert inside 
        
        rows += 1
    
    # Update the searchqueries table so we know when they were last run
    cql = 'UPDATE car_pricing.searchqueries SET lastruntime = ? WHERE searchname = ?;'
    prepStatement = session.prepare(cql)
    session.execute(prepStatement, [datetime.datetime.now(), sc.searchName])
    
    # Shut down connection
    session.shutdown()
    cluster.shutdown()
    
    return 'Inserted ' + str(rows) + ' rows into the database'


# This function writes the log to the database so we can debug any errors
def writeLog(log):
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    cql = 'INSERT INTO log (sessioncreatedtime, logtime, message) VALUES (?, ?, ?);'    
    prepStatement = session.prepare(cql)        # Prepared statement only needs sent to server once and be executed multiple times as below, better for performance
        
    for l in log:
        session.execute(prepStatement, l)
        
    session.shutdown()
    cluster.shutdown()
    
    log = []    # Clear the log to prevetn writing duplicates (since Python only passes lists by reference this also clears the external list)


# This function gets the search criterias from the database and creates the search objects from them
def initialiseSearchCriterias():
    scs = []
    sc = None
    
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    cql = 'SELECT searchname, searchcriteria, lastruntime FROM car_pricing.searchqueries;'    
    prepStatement = session.prepare(cql)        # Prepared statement only needs sent to server once and be executed multiple times as below, better for performance
        
    queryResults = session.execute(prepStatement)
    
    for qr in queryResults:
        if qr[2] != None:
            lastruntime = qr[2]
        else:
            lastruntime = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d')
        
        # Only include search if run more than 7 days ago
        if (lastruntime + datetime.timedelta(days = 7) < datetime.datetime.now()):
            sc = searchCriteria(qr[0], qr[1])
            
            scs.append(sc)
        
    session.shutdown()
    cluster.shutdown()
    
    return scs
    

# The main code block we want to run
def main():  
    try:
        # Get a user agent each call
        ua = UserAgent()
        
        # Create a metadata object to use
        md = metadata()
        
        # Instantise the search criteria objects
        scs = initialiseSearchCriterias()
        
        # Create a log object so we can log all the events and write them to the database
        log = []
        
        # Write to log
        msg = 'Found ' + str(len(scs)) + ' searches in database.'
        log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
        print(msg)
        
        # Iterate through each search and get the results
        for sc in scs:
            # Write to log
            msg = 'Starting search = ' + sc.searchName + '.'
            log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
            print(msg)
            
            # Have a longer sleep between named searches to reduce changes of being detected
            ri = random.randint(120, 360)
            msg = 'Starting a new search so off for a ' + str(ri) + ' seconds sleep.'
            log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
            print(msg)
            time.sleep(ri)
            
            for j in range(0, len(sc.refinedURLs)):
                # Write to log
                msg = 'On refined URL ' + str(j + 1) + ' of ' + str(len(sc.refinedURLs)) + '.'
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                print(msg)
                
                # Initialise empty results list, this is the main output
                masterResultsList = []
                
                # Loop through all the pages and add the results to a list
                pgNum = 1
                makesRegex = ''
                while masterResultsList == [] or pgNum <= md.maxPages:  # On the first run pgNum = 1 and md.maxPages = 1 but since the master list is empty this will still run first time
                    # Make a random delay to confuse any bot detection algorithms 
                    msg = 'Search results page: ' + str(pgNum) + ' of ' + ('unknown' if (masterResultsList == []) else (str(md.maxPages))) + '.'
                    log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                    print(msg)
                    if pgNum > 1:
                        ri = random.randint(15, 30)
                        msg = 'Going for a ' + str(ri) + ' seconds sleep.'
                        log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                        print(msg)
                        time.sleep(ri)
                    
                    
                    # Append the page number onto the URL to get subsequent pages
                    currentSearchURL = sc.refinedURLs[j] + '&page=' + str(pgNum)
                
                    # Now run load webpage
                    response = requests.get(currentSearchURL, headers = {'User-Agent': ua.random})
                
                    # Create soup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Adjust max pages and list of makes if this is the first run
                    if masterResultsList == []:
                        md.maxPages = findMaxPages(soup)
                        makesRegex = buildMakesRegex(soup)
                    
                    # Parse first page
                    resultsList = parsePage(soup, md, ua, makesRegex, log)
            
                    # Concatenate lists together
                    masterResultsList = masterResultsList + resultsList
                    
                    pgNum += 1
                
                msg = writeResults(md, sc, masterResultsList)
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                writeLog(log)
        
    except Exception as e:
        msg = ','.join(traceback.format_exception(*sys.exc_info()))
        log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
        writeLog(log)
    
    


# This is where any code runs
main()
    
    
    
    






