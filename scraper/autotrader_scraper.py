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


# Create a class that we can use to track everything we want to save from each advert
class advert:
    def __init__(self):
        self.adTitle = ''
        self.adID = ''
        self.attentionGrab = ''
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
        
    def toList(self, sessionID, foundTime):   # Ensures that the list is always in the same order so when we pass it to a SQL query we know what order to specify the columns
        l = []
        
        l.append(self.adID)
        l.append(sessionID)
        l.append(foundTime)
        l.append(self.adTitle)
        l.append(self.attentionGrab)
        l.append(self.year)
        l.append(self.plate)
        l.append(self.bodyType)
        l.append(self.mileage)
        l.append(self.transmission)
        l.append(self.engineSize)
        l.append(self.bhp)
        l.append(self.fuelType)
        l.append(self.price)
        l.append(self.sellerType)
        l.append(self.distanceFromYou)
        l.append(self.location)
        l.append(self.make)
        l.append(self.model)
        l.append(self.dealerName)
        l.append(self.features)
        l.append(self.urbanMPG)
        l.append(self.extraUrbanMPG)
        l.append(self.averageMPG)
        l.append(self.annualTax)
        l.append(self.advertHTML)
        
        return l


# Create a class to store our search criteria so we can pass it around
class searchCriteria:
    def __init__(self):
        # Set up all the search parameters, note that many of these are case sensitive
        self.searchName = 'Local automatics'
        self.milesFrom = 200    # Set to 1500 to see national, can be set to any number (e.g. 157)
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
        self.bodyType = 'Saloon'
        self.fuelType = 'Diesel'
        self.engineSizeFrom = 0.0
        self.engineSizeTo = 0.0
        self.transmission = 'Automatic'
        self.keywords = ''        # Any spaces need replaced by %20
        self.searchURL = self.urlBuilder()
        
    def export(self):   # Ensures that the list is always in the same order so when we pass it to a SQL query we know what order to specify the columns
        e = {}
        
        e['Search Name'] = self.searchName
        e['Miles From'] = self.milesFrom
        e['Postcode'] = self.postCode
        e['Car Types'] = ','.join(self.carTypes).replace('%20', ' ')
        
        if (self.make != ''):
            e['Make'] = self.make
        
        if (self.model != ''):
            e['Model'] = self.model
        
        if (self.modelVariant != ''):
            e['Model Variant'] = self.modelVariant
        
        if (self.priceFrom != Decimal(0)):
            e['Price From'] = self.priceFrom
            
        if (self.priceTo != Decimal(0)):
            e['Price To'] = self.priceTo
            
        if (self.yearFrom != 1970):
            e['Year From'] = self.yearFrom
            
        if (self.yearTo != 1970):
            e['Year To'] = self.yearTo
        
        if (self.mileageFrom != 0):
            e['Mileage From'] = self.mileageFrom
        
        if (self.mileageTo != 0):
            e['Mileage To'] = self.mileageTo
        
        if (self.bodyType != ''):
            e['Body Type'] = self.bodyType
            
        if (self.fuelType != ''):
            e['Fuel Type'] = self.fuelType
            
        if (self.engineSizeFrom != 0.0):
            e['Engine Size From'] = self.engineSizeFrom
            
        if (self.engineSizeTo != 0.0):
            e['Engine Size To'] = self.engineSizeTo
            
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
        outputURL = outputURL + ('' if (self.bodyType == '') else ('&body-type=' + self.bodyType))
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
def parsePage(soup):
    resultsListToReturn = []
    
    pageResults = soup.findAll('li', attrs = {'class': 'search-page__result'})
    
    for j in range(0, len(pageResults)):
        if pageResults[j].find('span', attrs = {'class': 'listings-standout'}) == None: # Adverts with this span class are adverts and should not be included in our results
            ad = advert()
            
            ad.advertHTML = str(pageResults[j])
            
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
            rBodyType = re.compile(r'(convertible|coupe|estate|hatchback|mpv|other|suv|saloon|unlisted)')
            rMileage = re.compile(r'\d+(,\d+)? miles')
            rTransmission = re.compile(r'(manual|automatic)')
            rEngineSizeLitres = re.compile(r'\d+\.\d+l')
            rHorsepowerBHP = re.compile(r'\d+ bhp')
            rFuelType = re.compile(r'(petrol|diesel)')
            
            for li in liTags:
                if rYear.search(li.text.lower()) != None:
                    rYearMatches = rYear.match(li.text.lower())
                    
                    ad.year = int(rYearMatches.groups()[0])
                    
                    fullPlate = rYearMatches.groups()[1]    # This is the group that says ' (66 reg)' for example, we need to extract the number
                    if fullPlate == None:
                        ad.plate = -1
                    else:
                        rPlateMatches = rPlate.search(fullPlate)
                        
                        ad.plate = int(rPlateMatches[0])
                    
                elif rBodyType.search(li.text.lower()) != None:
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
            
            resultsListToReturn.append(ad)
        
    return resultsListToReturn


# This function gets all the possible manufacturers from the options on the side
def buildMakesRegex(soup):
    makesDiv = soup.find('div', attrs = {'data-temp': 'make-flyout'})
    
    makesList = [m.find('span', attrs = {'class': 'term'}).text for m in makesDiv]
    
    makesRegex = '|'.join(makesList)
    
    return makesRegex
    

# This function writes all the results we found into the postgres database
def writeResults(md, masterResultsList):
    """
    sql = "INSERT INTO car.carDetails (advertID, sessionID, foundTime, adTitle, attentionGrab, year, plate, bodyType, mileage, transmission, engineSize, bhp, fuelType, price, sellerType, distanceFromYou, location, make, model, dealerName, features, urbanMPG, extraUrbanMPG, averageMPG, annualTax, advertHTML) VALUES ("
    sql = sql + ('%s, ' * len(masterResultsList[0].toList(sessionID = md.sessionID, foundTime = datetime.datetime.now())))    # Add one %s for each item of the list
    sql = sql.rstrip(', ') + ')'        # Remove the last comma space                                              
    
    for i in range(0, len(masterResultsList)):
        values = masterResultsList[i].toList(sessionID = md.sessionID, foundTime = datetime.datetime.now())
        
        conn = psycopg2.connect(host = 'localhost', database = 'car-pricing', user = database_secrets.username, password = database_secrets.password)
        cur = conn.cursor()
        cur.execute(sql, values)
        conn.commit()        
        cur.close()
        conn.close()
    """
    return 'All done'


# The main code block we want to run
def main():    
    # Create a metadata object to use
    md = metadata()
    
    # Instantise the search criteria object
    sc = searchCriteria()
    
    # Initialise empty results list, this is the main output
    masterResultsList = []
    
    # Loop through all the pages and add the results to a list
    pgNum = 1
    while masterResultsList == [] or pgNum < md.maxPages:  # On the first run pgNum = 1 and md.maxPages = 1 but since the master list is empty this will still run first time
        # Make a random delay to confuse any bot detection algorithms
        if pgNum > 1:
            ri = random.randint(4, 12)
            print('Going for a ' + str(ri) + ' seconds sleep')
            time.sleep(ri)
        
        # Append the page number onto the URL to get subsequent pages
        currentSearchURL = sc.searchURL + '&page=' + str(pgNum)
    
        # Now run load webpage
        response = requests.get(currentSearchURL, headers = {'User-Agent': md.user_agent})
    
        # Create soup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Parse first page
        resultsList = parsePage(soup)
        
        # Adjust max pages if this is the first run
        if masterResultsList == []:
            md.maxPages = findMaxPages(soup)
        
        # Concatenate lists together
        masterResultsList = masterResultsList + resultsList
        
        pgNum += 1
    
    print(writeResults(md, masterResultsList))


main()
    
    
    
    

























