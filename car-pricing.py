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
import psycopg2
from re import sub
from decimal import Decimal
import socket
import sys
import os
# Ensure we are in the correct directory
os.chdir("C:/GitWorkspace/ML-car-pricing")
import database_secrets


# Create a class that we can use to track everything we want to save from each advert
class advert:
    def __init__(self):
        self.adTitle = ''
        self.adID = ''
        self.attentionGrab = ''
        self.year = 1970
        self.plate = 70
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
        self.milesFrom = 100    # Set to 1500 to see national, can be set to any number (e.g. 157)
        self.postCode = 'fk27ga'  # No spaces
        self.carTypes = ['Nearly%20New']  # If multiple are specified here then add each with it's own API parameter. Can choose from New, Used or Nearly New
        self.make = ''
        self.model = ''
        self.modelVariant = ''
        self.priceFrom = 0
        self.priceTo = 30000
        self.yearFrom = 2016
        self.yearTo = 1970
        self.mileageFrom = 0
        self.mileageTo = 5000
        self.bodyType = 'Saloon'
        self.fuelType = 'Diesel'
        self.engineSizeFrom = 0.0
        self.engineSizeTo = 2.2
        self.transmission = 'Automatic'
        self.keywords = ''        # Any spaces need replaced by %20
        self.searchURL = self.urlBuilder()
        
    def toList(self):   # Ensures that the list is always in the same order so when we pass it to a SQL query we know what order to specify the columns
        l = []
        
        l.append(self.searchName)
        l.append(self.milesFrom)
        l.append(self.postCode)
        l.append(','.join(self.carTypes).replace('%20', ' '))
        l.append(self.make)
        l.append(self.model)
        l.append(self.modelVariant)
        l.append(self.priceFrom)
        l.append(self.priceTo)
        l.append(self.yearFrom)
        l.append(self.yearTo)
        l.append(self.mileageFrom)
        l.append(self.mileageTo)
        l.append(self.bodyType)
        l.append(self.fuelType)
        l.append(self.engineSizeFrom)
        l.append(self.engineSizeTo)
        l.append(self.transmission)
        l.append(self.keywords)
        l.append(self.searchURL)
        
        return l
    
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
        self.sessionCreatedTime = ''
        self.sessionID = 0
        self.searchCriteriaID = 0
        self.user_agent = ''
        self.maxPages = 0


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
        rYear = re.compile(r'(\d+) \((\d+) reg\)')
        rBodyType = re.compile(r'(convertible|coupe|estate|hatchback|mpv|other|suv|saloon|unlisted)')
        rMileage = re.compile(r'\d+,\d+ miles')
        rTransmission = re.compile(r'(manual|automatic)')
        rEngineSizeLitres = re.compile(r'\d+\.\d+l')
        rHorsepowerBHP = re.compile(r'\d+ bhp')
        rFuelType = re.compile(r'(petrol|diesel)')
        
        for li in liTags:
            if rYear.search(li.text.lower()) != None:
                rYearMatches = rYear.match(li.text.lower())
                
                ad.year = rYearMatches.groups()[0]
                ad.plate = rYearMatches.groups()[1]
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
        
        currencyString = priceCol.find('div', attrs = {'class': 'vehicle-price'}).text
        ad.price = Decimal(sub(r'[^\d.]', '', currencyString))
        
        resultsListToReturn.append(ad)
        
    return resultsListToReturn


# This begins a new session and saves the session ID for later use
def initiateSession(md):
    # Use seconds of current time to seed random package, and return datetime for later use
    currentTime = datetime.datetime.now()
    seed = currentTime.second
    random.seed(seed)
    
    sql = 'INSERT INTO car.sessions (searchCriteriaID, sessionCreatedTime, hostName, pythonVersion, codeVersion) VALUES (%s, %s, %s, %s, %s) RETURNING sessionID'
    
    pythVersionRegex = re.compile(r'[^|]*')
    pythVersion = pythVersionRegex.search(sys.version)[0].strip()
    
    values = [md.searchCriteriaID, currentTime, socket.gethostname(), pythVersion, '1.0.0']
    
    conn = psycopg2.connect(host = 'localhost', database = 'car-pricing', user = database_secrets.username, password = database_secrets.password)
    cur = conn.cursor()
    cur.execute(sql, values)
    sessionID = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    md.sessionID = sessionID
    md.sessionCreatedTime = currentTime
    
    return md


# This function starts the process of checking the search criteria and so on
def initiateSearch():
    sc = searchCriteria()
    
    sql = 'SELECT searchCriteriaID FROM car.searchcriteria WHERE searchName = %s AND milesFrom = %s AND postCode = %s AND carTypes = %s AND make = %s AND model = %s AND modelVariant = %s AND priceFrom = %s AND priceTo = %s AND yearFrom = %s AND yearTo = %s AND mileageFrom = %s AND mileageTo = %s AND bodyType = %s AND fuelType = %s AND engineSizeFrom = %s AND engineSizeTo = %s AND transmission = %s AND keywords = %s AND searchURL = %s'
    conn = psycopg2.connect(host = 'localhost', database = 'car-pricing', user = database_secrets.username, password = database_secrets.password)
    cur = conn.cursor()
    cur.execute(sql, sc.toList())
    result = cur.fetchone()
    cur.close()
    conn.close()    
    
    if result == None:  # This means the search hasn't previously been run so we need to add it to the database
        sql = 'INSERT INTO car.searchcriteria (searchName, milesFrom, postCode, carTypes, make, model, modelVariant, priceFrom, priceTo, yearFrom, yearTo, mileageFrom, mileageTo, bodyType, fuelType, engineSizeFrom, engineSizeTo, transmission, keywords, searchURL) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING searchCriteriaID'
        conn = psycopg2.connect(host = 'localhost', database = 'car-pricing', user = database_secrets.username, password = database_secrets.password)
        cur = conn.cursor()
        cur.execute(sql, sc.toList())
        conn.commit()
        searchCriteriaID = cur.fetchone()[0]
        cur.close()
        conn.close()    
    else:
        searchCriteriaID = result[0]
    
    return (sc, searchCriteriaID)


# This function writes all the results we found into the postgres database
def writeResults(md, masterResultsList):
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


# The main code block we want to run
def main():    
    # Create a metadata object to use
    md = metadata()
    
    # Instantise the search criteria object
    (sc, md.searchCriteriaID) = initiateSearch()
    
    # Initiate a session
    md = initiateSession(md)
    
    # Firstly get a user agent
    md.user_agent = pickAgent()
    
    # Now run load webpage
    response = requests.get(sc.searchURL, headers = {'User-Agent': md.user_agent})

    # Create soup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find pagination results so we know how many pages to iterate through
    md.maxPages = findMaxPages(soup)
    
    # Parse first page
    resultsList = parsePage(soup)
    
    # Initialise empty results list, this is the main output
    masterResultsList = []
    
    # Concatenate lists together
    masterResultsList = masterResultsList + resultsList
    
    if md.maxPages > 1:
        # Loop through all the pages and add the results to a list
        for pgNum in range(2, md.maxPages + 1):     # Since Python only goes to less than the latter number
            # Make a random delay to confuse any bot detection algorithms
            time.sleep(random.randint(4, 12))
            
            # Append the page number onto the URL to get subsequent pages
            currentSearchURL = sc.searchURL + '&page=' + str(pgNum)
        
            # Now run load webpage
            response = requests.get(currentSearchURL, headers = {'User-Agent': md.user_agent})
        
            # Create soup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Parse first page
            resultsList = parsePage(soup)
            
            # Concatenate lists together
            masterResultsList = masterResultsList + resultsList
    
    writeResults(md, masterResultsList)


main()
    
    
    
    

























