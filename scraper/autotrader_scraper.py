# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 14:02:06 2017

@author: ColinParr

This is used to scrape car results from Autotrader and analyse them using ML
"""
# Required libraries
from bs4 import BeautifulSoup
import csv
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


# Create a class that we can use to track everything we want to save from each advert
class advert:
    def __init__(self):
        self.adTitle = ''
        self.adID = ''
        self.attentionGrab = ''
        self.foundTime = datetime.datetime(year = 1970, month = 1, day = 1)
        self.year = 1970
        self.plate = -1
        self.bodyType = ''
        self.mileage = 0
        self.transmission = ''
        self.engineSize = 0
        self.bhp = 0
        self.fuelType = ''
        self.price = Decimal(0)
        self.sellerType = ''
        self.distanceFromYou = 0
        self.location = ''
        self.make = ''
        self.model = ''
        self.modelfull = ''
        self.dealerName = ''
        self.features = ''
        self.urbanMPG = 0
        self.extraUrbanMPG = 0
        self.averageMPG = 0
        self.annualTax = Decimal(0)
        self.advertHTML = ''
        self.thumbnail = None


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
                             'Price From': 'price-from',
                             'Price To': 'price-to',
                             'Year From': 'year-from',
                             'Year To': 'year-to',
                             'Mileage From': 'minimum-mileage',
                             'Mileage To': 'maximum-mileage',
                             'Body Types': 'body-type',
                             'Fuel Type': 'fuel-type',
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
    userAgent = pickAgent()
    
    # Get response based on initial URL
    response = requests.get(startSearchURL, headers = {'User-Agent': userAgent})

    # Create soup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Adjust max pages and list of makes if this is the first run
    maxPages = findMaxPages(soup)
    
    if maxPages <= pagesLimit:
        refinedURLs.append(startSearchURL)
    else:
        if currentParams['Price From'] == None: # If no price from is specified then use the lowest in the drop down on the page
            sel = soup.find('select', attrs = {'name': 'price-from'})
            opt = sel.findAll('option')
            minPriceFrom = min([int(o['value']) for o in opt if o['value'] != ''])
        else:
            minPriceFrom = int(currentParams['Price From'])
        
        if currentParams['Price To'] == None: # If no price from is specified then use the highest in the drop down on the page
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
        self.user_agent = pickAgent()
        self.maxPages = 1   # Starts at 1 then is updated later using while loop
        
        pythVersionRegex = re.compile(r'[^|]*')
        pythVersion = pythVersionRegex.search(sys.version)[0].strip()
        self.pythonVersion = pythVersion
        
        self.codeVersion = '1.0.0'
        self.hostName = socket.gethostname()


# Randomly choose one of the previously defined user agents
def pickAgent():
    # Open file with lots of user agents to choose from, so we can confuse any bot detection algorithms
    with open('UserAgents.csv', 'r') as f:
        reader = csv.reader(f)
        user_agents = list(reader)      # Returns this as a list of lists (if the CSV had multiple columns these would be in sublist)
    
    return random.choice(user_agents)[0]


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
def parsePage(soup, md, makesRegex, log):
    resultsListToReturn = []
    
    pageResults = soup.findAll('li', attrs = {'class': 'search-page__result'})
    
    for j in range(0, len(pageResults)):
        if pageResults[j].find('span', attrs = {'class': 'listings-standout'}) == None: # Adverts with this span class are adverts and should not be included in our results
            # Make a random delay to confuse any bot detection algorithms now that we are loading sub pages from here
            msg = 'Advert: ' + str(j + 1) + ' of ' + str(len(pageResults)) + '.'
            if j > 0:
                ri = random.randint(1, 3)
                msg = msg + ' Having a wee ' + str(ri) + ' seconds rest while I load the advert page.'
                time.sleep(ri)
            log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
            print(msg)
            
            # Create advert object to store findings
            ad = advert()
            
            ad.advertHTML = str(pageResults[j])
            ad.foundTime = datetime.datetime.now()
            
            contentCol = pageResults[j].find('section', attrs = {'class': 'content-column'})
            priceCol = pageResults[j].find('section', attrs = {'class': 'price-column'})
            
            ad.adID = pageResults[j].get('id')
            ad.adTitle = contentCol.find('h2', attrs = {'class': 'listing-title title-wrap'}).text.strip()
            ad.attentionGrab = contentCol.find('p', attrs = {'class': 'listing-attention-grabber'}).text.strip()
            
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
                    ad.bodyType = li.text
                elif rMileage.search(li.text.lower()) != None:
                    ad.mileage = int(li.text.replace(' miles', '').replace(',', ''))
                elif rTransmission.search(li.text.lower()) != None:
                    ad.transmission = li.text
                elif rEngineSizeLitres.search(li.text.lower()) != None:
                    ad.engineSize = float(li.text.replace('L', ''))
                elif rHorsepowerBHP.search(li.text.lower()) != None:
                    ad.bhp = int(li.text.replace(' bhp', ''))
                elif rFuelType.search(li.text.lower()) != None:
                    ad.fuelType = li.text
                elif rYear.search(li.text.lower()) != None:
                    rYearMatches = rYear.match(li.text.lower())
                    
                    if int(rYearMatches.groups()[0]) > 1980:    # Have a sensible cutoff for year to prevent mismatching
                        ad.year = int(rYearMatches.groups()[0])
                        
                        fullPlate = rYearMatches.groups()[1]    # This is the group that says ' (66 reg)' for example, we need to extract the number
                        if fullPlate == None:
                            ad.plate = -1
                        else:
                            rPlateMatches = rPlate.search(fullPlate)
                            
                            ad.plate = int(rPlateMatches[0])
            
            # Get car price information
            currencyString = priceCol.find('div', attrs = {'class': 'vehicle-price'}).text
            ad.price = Decimal(sub(r'[^\d.]', '', currencyString))
            
            # Determine if trade or private seller
            sellerType = contentCol.find('div', attrs = {'class': 'seller-type'}).text.lower()
            rSellerType = re.compile(r'(trade|private)')
            ad.sellerType = rSellerType.search(sellerType)[0]
            
            # Get distance from specified postcode
            sellerLocation = contentCol.find('div', attrs = {'class': 'seller-location'})
            rSellerLocation = re.compile(r'\d+')
            ad.distanceFromYou = int(rSellerLocation.search(sellerLocation.text)[0])
            
            # Get seller town using same bs4 tag as distance above (note that .span finds the first span tag within the parent element, and is shorthand for using .find when there is only one element of that type)
            if sellerLocation.span != None:
                ad.location = sellerLocation.span.text           
            
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
                
                ad.thumbnail = thumbnail
            
            # Get the further detail from the actual advert page
            # NOTE: Python considers user defined classes mutable so ad is actually updated by this function call
            pageLevelInfo(md, ad, makesRegex)
            
            # Add the advert to the overall list to be returned
            resultsListToReturn.append(ad)
        
    return resultsListToReturn


# This function takes an advert ID and loads the page so we can scrape more information
# NOTE: Python considers user defined classes mutable (changeable) so passes a pointer to the class. This means functions can update the object within the parent.
def pageLevelInfo(md, ad, makesRegex):
    # Build up URL to load page
    baseURL = 'https://www.autotrader.co.uk/classified/advert/'
    advertURL = baseURL + ad.adID
    
    response = requests.get(advertURL, headers = {'User-Agent': md.user_agent})
    
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
                    ad.urbanMPG = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'extra urban mpg':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rMPGMatches = rMPG.match(desc)
                
                if rMPGMatches != None:
                    ad.extraUrbanMPG = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'average mpg':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rMPGMatches = rMPG.match(desc)
                
                if rMPGMatches != None:
                    ad.averageMPG = float(rMPGMatches[0])
                
            elif divTerm.text.lower() == 'annual tax':
                desc = fpaSection.find('div', attrs = {'class': 'fpaSpecifications__description'}).text
                
                rTaxMatches = rTax.match(desc)
                
                if rTaxMatches != None:
                    ad.annualTax = float(rTaxMatches.groups()[0])
    
    # Get the big comma separated list of deatures we can use with one-hot encoding later to predict the car price
    combinedFeatures = soup.find('section', attrs = {'class': 'combinedFeatures'})
    
    if combinedFeatures != None:
        featuresHeading = soup.find('h2', attrs = {'class': 'combinedFeatures__heading'}).text
        features = combinedFeatures.text
        ad.features = features.replace(featuresHeading, '').replace('\n', '')
    
    # Get the dealer name
    divDealer = soup.find('div', attrs = {'class': 'aboutDealer__name'})
    
    if divDealer != None:
        ad.dealerName = divDealer.text.replace('\n', '').strip()
    
    # Find the make and extended model name
    rMakes = re.compile(makesRegex)
    
    ad.make = rMakes.match(ad.adTitle.lower())[0]
    ad.modelfull = ad.adTitle.lower().replace(ad.make, '').strip()
    
    if ad.engineSize > 0:
        rModelShort = re.compile('^(.*?)' + str(ad.engineSize).replace('.', '\.'))  # Try looking for exact engine size in name
        rModelShort2 = re.compile('^(.*?)\d\.\d')                                    # Some cars say 2.1L but are actually 2.2L or whatever, so try generic engine size
        
        rModelMatches = rModelShort.match(ad.modelfull)
        
        if rModelMatches == None:
            rModelMatches = rModelShort2.match(ad.modelfull)
        
        if rModelMatches != None:
            ad.model = rModelMatches.groups()[0].strip()
            
    
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

    if ad.adID != '':
        columnList.append('advertid')
        valuesList.append(ad.adID)
        
    if ad.foundTime != datetime.datetime(year = 1970, month = 1, day = 1):
        columnList.append('foundtime')
        valuesList.append(ad.foundTime)
        
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
        
    if ad.adTitle != '':
        columnList.append('adtitle')
        valuesList.append(ad.adTitle)
    
    if ad.attentionGrab != '':
        columnList.append('attentiongrab')
        valuesList.append(ad.attentionGrab)
        
    if ad.year != 1970:
        columnList.append('year')
        valuesList.append(ad.year)
        
    if ad.plate != -1:
        columnList.append('plate')
        valuesList.append(ad.plate)
        
    if ad.bodyType != '':
        columnList.append('bodyType')
        valuesList.append(ad.bodyType)
        
    if ad.mileage != '':
        columnList.append('mileage')
        valuesList.append(ad.mileage)
        
    if ad.transmission != '':
        columnList.append('transmission')
        valuesList.append(ad.transmission)
        
    if ad.engineSize != 0:
        columnList.append('enginesize')
        valuesList.append(ad.engineSize)
        
    if ad.bhp != 0:
        columnList.append('bhp')
        valuesList.append(ad.bhp)
        
    if ad.fuelType != '':
        columnList.append('fueltype')
        valuesList.append(ad.fuelType)
        
    if ad.price != Decimal(0):
        columnList.append('price')
        valuesList.append(ad.price)
     
    if ad.sellerType != '':
        columnList.append('sellertype')
        valuesList.append(ad.sellerType)
        
    if ad.distanceFromYou != 0:
        columnList.append('distancefromyou')
        valuesList.append(ad.distanceFromYou)
        
    if ad.location != '':
        columnList.append('location')
        valuesList.append(ad.location)
        
    if ad.make != '':
        columnList.append('make')
        valuesList.append(ad.make)
        
    if ad.model != '':
        columnList.append('model')
        valuesList.append(ad.model)
        
    if ad.modelfull != '':
        columnList.append('modelfull')
        valuesList.append(ad.modelfull)
    
    if ad.dealerName != '':
        columnList.append('dealername')
        valuesList.append(ad.dealerName)
        
    if ad.features != '':
        columnList.append('features')
        valuesList.append(ad.features)
        
    if ad.urbanMPG != 0:
        columnList.append('urbanmpg')
        valuesList.append(ad.urbanMPG)
        
    if ad.extraUrbanMPG != 0:
        columnList.append('extraurbanmpg')
        valuesList.append(ad.extraUrbanMPG)

    if ad.averageMPG != 0:
        columnList.append('averagempg')
        valuesList.append(ad.averageMPG)

    if ad.annualTax != Decimal(0):
        columnList.append('annualtax')
        valuesList.append(ad.annualTax)

    if ad.advertHTML != '':
        columnList.append('adverthtml')
        valuesList.append(ad.advertHTML)
        
    if ad.thumbnail != None:
        columnList.append('thumbnail')
        valuesList.append(ad.thumbnail)
    
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


# This function gets the search criterias from the database and creates the search objects from them
def initialiseSearchCriterias():
    scs = []
    sc = None
    
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    cql = 'SELECT searchname, searchcriteria FROM car_pricing.searchqueries;'    
    prepStatement = session.prepare(cql)        # Prepared statement only needs sent to server once and be executed multiple times as below, better for performance
        
    queryResults = session.execute(prepStatement)
    
    for qr in queryResults:
        sc = searchCriteria(qr[0], qr[1])
        
        scs.append(sc)
        
    session.shutdown()
    cluster.shutdown()
    
    return scs


# The main code block we want to run
def main():    
    # Create a log object so we can log all the events and write them to the database
    log = []
    
    
    try:
        # Create a metadata object to use
        md = metadata()
        
        # Instantise the search criteria objects
        scs = initialiseSearchCriterias()
        
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
                    if pgNum > 1:
                        ri = random.randint(4, 12)
                        msg = msg + ' Going for a ' + str(ri) + ' seconds sleep.'
                        time.sleep(ri)
                    log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                    print(msg)
                    
                    # Append the page number onto the URL to get subsequent pages
                    currentSearchURL = sc.refinedURLs[j] + '&page=' + str(pgNum)
                
                    # Now run load webpage
                    response = requests.get(currentSearchURL, headers = {'User-Agent': md.user_agent})
                
                    # Create soup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Adjust max pages and list of makes if this is the first run
                    if masterResultsList == []:
                        md.maxPages = findMaxPages(soup)
                        makesRegex = buildMakesRegex(soup)
                    
                    # Parse first page
                    resultsList = parsePage(soup, md, makesRegex, log)
            
                    # Concatenate lists together
                    masterResultsList = masterResultsList + resultsList
                    
                    pgNum += 1
                
                msg = writeResults(md, sc, masterResultsList)
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
        
        
    except Exception as e:
        msg = ','.join(traceback.format_exception(*sys.exc_info()))
        log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
        
    
    writeLog(log)


# This is where any code runs
main()
    
    
    
    






