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
    def __init__(self):
        # Set up all the search parameters, note that many of these are case sensitive
        self.searchName = 'Local automatics'
        self.milesFrom = 100    # Set to 1500 to see national, can be set to any number (e.g. 157)
        self.postCode = 'fk27ga'  # No spaces
        self.carTypes = ['Nearly%20New']  # If multiple are specified here then add each with it's own API parameter. Can choose from New, Used or Nearly New
        self.make = ''
        self.model = ''
        self.modelVariant = ''
        self.priceFrom = 0
        self.priceTo = 40000
        self.yearFrom = 2016
        self.yearTo = 1970
        self.mileageFrom = 0
        self.mileageTo = 5000
        self.bodyTypes = ['Saloon', 'Estate', 'Coupe', 'Convertible']
        self.fuelType = ''
        self.engineSizeFrom = 0.0
        self.engineSizeTo = 0.0
        self.transmission = 'Automatic'
        self.keywords = ''        # Any spaces need replaced by %20
        self.searchURL = self.urlBuilder()
        
    def export(self):   # Creates dictionary for passing to Cassandra map, all values MUST BE TEXT
        e = {}
        
        e['Search Name'] = self.searchName
        e['Miles From'] = str(self.milesFrom)
        e['Postcode'] = self.postCode
        e['Car Types'] = ','.join(self.carTypes).replace('%20', ' ')
        
        if (self.make != ''):
            e['Make'] = self.make
        
        if (self.model != ''):
            e['Model'] = self.model
        
        if (self.modelVariant != ''):
            e['Model Variant'] = self.modelVariant
        
        if (self.priceFrom != Decimal(0)):
            e['Price From'] = str(self.priceFrom)
            
        if (self.priceTo != Decimal(0)):
            e['Price To'] = str(self.priceTo)
            
        if (self.yearFrom != 1970):
            e['Year From'] = str(self.yearFrom)
            
        if (self.yearTo != 1970):
            e['Year To'] = str(self.yearTo)
        
        if (self.mileageFrom != 0):
            e['Mileage From'] = str(self.mileageFrom)
        
        if (self.mileageTo != 0):
            e['Mileage To'] = str(self.mileageTo)
               
        if type(self.bodyTypes) is list and len(self.bodyTypes) > 0:
            e['Body Types'] = ','.join(self.bodyTypes)
        elif type(self.bodyTypes) is str and len(self.bodyTypes) > 0:
            e['Body Types'] = self.bodyTypes
        
        if (self.fuelType != ''):
            e['Fuel Type'] = self.fuelType
            
        if (self.engineSizeFrom != 0.0):
            e['Engine Size From'] = str(self.engineSizeFrom)
            
        if (self.engineSizeTo != 0.0):
            e['Engine Size To'] = str(self.engineSizeTo)
            
        if (self.transmission != ''):
            e['Transmission'] = self.transmission
            
        if (self.keywords != ''):
            e['Keywords'] = self.keywords
            
        e['Search URL'] = self.searchURL
        
        return e
    
    
    # Takes the search criteria selected by the user and builds the Autotrader URL to scrape
    def urlBuilder(self):
        outputURL = 'https://www.autotrader.co.uk/car-search?sort=price-asc'   # Always sort ascending order in price
        
        outputURL = outputURL + '&radius=' + str(self.milesFrom)
        outputURL = outputURL + '&postcode=' + self.postCode
        for carType in self.carTypes:
            outputURL = outputURL + '&onesearchad=' + carType
        outputURL = outputURL + ('' if (self.make == '') else ('&make=' + self.make))       # If expression (true_output if boolean_condition else false_output)
        outputURL = outputURL + ('' if (self.model == '') else ('&model=' + self.model))
        outputURL = outputURL + ('' if (self.modelVariant == '') else ('&aggregatedtrim=' + self.modelVariant))
        outputURL = outputURL + ('' if (self.priceFrom == Decimal(0)) else ('&price-from=' + str(self.priceFrom)))
        outputURL = outputURL + ('' if (self.priceTo == Decimal(0)) else ('&price-to=' + str(self.priceTo)))
        outputURL = outputURL + ('' if (self.yearFrom == 1970) else ('&year-from=' + str(self.yearFrom)))
        outputURL = outputURL + ('' if (self.yearTo == 1970) else ('&year-to=' + str(self.yearTo)))
        outputURL = outputURL + ('' if (self.mileageFrom == 0) else ('&minimum-mileage=' + str(self.mileageFrom)))
        outputURL = outputURL + ('' if (self.mileageTo == 0) else ('&maximum-mileage=' + str(self.mileageTo)))
        
        if type(self.bodyTypes) is list and len(self.bodyTypes) > 0:
            for bodyType in self.bodyTypes:
                outputURL = outputURL + '&body-type=' + bodyType
        elif type(self.bodyTypes) is str and len(self.bodyTypes) > 0:
            outputURL = outputURL + '&body-type=' + self.bodyTypes
        
        outputURL = outputURL + ('' if (self.fuelType == '') else ('&fuel-type=' + self.fuelType))
        outputURL = outputURL + ('' if (self.engineSizeFrom == 0.0) else ('&minimum-badge-engine-size=' + str(self.engineSizeFrom)))
        outputURL = outputURL + ('' if (self.engineSizeTo == 0.0) else ('&maximum-badge-engine-size=' + str(self.engineSizeTo)))
        outputURL = outputURL + ('' if (self.transmission == '') else ('&transmission=' + self.transmission))
        outputURL = outputURL + ('' if (self.keywords == '') else ('&keywords=' + self.keywords))
    
        return outputURL


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
            if j > 0:
                ri = random.randint(1, 3)
                msg = 'Advert: ' + str(j + 1) + ' of ' + str(len(pageResults)) + '. Having a wee ' + str(ri) + ' seconds rest while I load the advert page.'
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                print(msg)
                time.sleep(ri)
            
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
    ad.model = ad.adTitle.lower().replace(ad.make, '').strip()


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
        
    if sc.export() != {}:
        columnList.append('searchcriteria')
        valuesList.append(sc.export())
        
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
        
        cql = 'INSERT INTO visualisation (' + cols + ') VALUES (' + placeholders2 + ');'
        
        prepStatement = session.prepare(cql)
        session.execute(prepStatement, valuesList)    # Need a loop here to handle each advert inside 
        
        rows += 1
    
    session.shutdown()
    
    return 'Inserted ' + str(rows) + ' rows into the database'


# This function writes the log to the database so we can debug any errors
def writeLog(log):
    cluster = Cluster()                         # Connect to local host on default port 9042
    session = cluster.connect('car_pricing')    # Connect to car_pricing keyspace
    
    for l in log:
        cql = 'INSERT INTO log (sessioncreatedtime, logtime, message) VALUES (?, ?, ?);'
        
        prepStatement = session.prepare(cql)
        session.execute(prepStatement, l)


# The main code block we want to run
def main():    
    # Create a log object so we can log all the events and write them to the database
    log = []
    
    
    try:
        # Create a metadata object to use
        md = metadata()
        
        # Instantise the search criteria object
        sc = searchCriteria()
        
        # Initialise empty results list, this is the main output
        masterResultsList = []
        
        # Loop through all the pages and add the results to a list
        pgNum = 1
        makesRegex = ''
        while masterResultsList == [] or pgNum <= md.maxPages:  # On the first run pgNum = 1 and md.maxPages = 1 but since the master list is empty this will still run first time
            # Make a random delay to confuse any bot detection algorithms
            if pgNum > 1:
                ri = random.randint(4, 12)
                msg = 'Search results page: ' + str(pgNum) + ' of ' + str(md.maxPages) + '. Going for a ' + str(ri) + ' seconds sleep.'
                log.append([md.sessionCreatedTime, datetime.datetime.now(), msg])
                print(msg)
                time.sleep(ri)
            
            # Append the page number onto the URL to get subsequent pages
            currentSearchURL = sc.searchURL + '&page=' + str(pgNum)
        
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
    
    
    
    






