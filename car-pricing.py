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
from re import sub
from decimal import Decimal


# Set up all the search parameters, note that many of these are case sensitive
milesFrom = '100'    # Set to 1500 to see national, can be set to any number (e.g. 157)
postCode = 'fk27ga'  # No spaces
carTypes = ['Nearly%20New']  # If multiple are specified here then add each with it's own API parameter. Can choose from New, Used or Nearly New
make = ''
model = ''
modelVariant = ''
priceFrom = ''
priceTo = '30000'
yearFrom = '2016'
yearTo = ''
mileageFrom = ''
mileageTo = '5000'
bodyType = 'Saloon'
fuelType = 'Diesel'
engineSizeFrom = ''
engineSizeTo = '2.2'
gearbox = 'Automatic'
keywords = ''        # Any spaces need replaced by %20

# Other parameters useful to us
seed = datetime.datetime.now().second
random.seed(seed)


# Open file with lots of user agents to choose from, so we can confuse any bot detection algorithms
with open('UserAgents.csv', 'r') as f:
    reader = csv.reader(f)
    user_agents = list(reader)      # Returns this as a list of lists (if the CSV had multiple columns these would be in sublist)


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
        self.Location = ''



# Takes the search criteria selected by the user and builds the Autotrader URL to scrape
def urlBuilder():
    outputURL = 'https://www.autotrader.co.uk/car-search?sort=price-asc'   # Always sort ascending order in price
    
    outputURL = outputURL + '&radius=' + milesFrom
    outputURL = outputURL + '&postcode=' + postCode
    for carType in carTypes:
        outputURL = outputURL + '&onesearchad=' + carType
    outputURL = outputURL + ('' if (make == '') else ('&make=' + make))       # If expression (true_output if boolean_condition else false_output)
    outputURL = outputURL + ('' if (model == '') else ('&model=' + model))
    outputURL = outputURL + ('' if (modelVariant == '') else ('&aggregatedtrim=' + modelVariant))
    outputURL = outputURL + ('' if (priceFrom == '') else ('&price-from=' + priceFrom))
    outputURL = outputURL + ('' if (priceTo == '') else ('&price-to=' + priceTo))
    outputURL = outputURL + ('' if (yearFrom == '') else ('&year-from=' + yearFrom))
    outputURL = outputURL + ('' if (yearTo == '') else ('&year-to=' + yearTo))
    outputURL = outputURL + ('' if (mileageFrom == '') else ('&minimum-mileage=' + mileageFrom))
    outputURL = outputURL + ('' if (mileageTo == '') else ('&maximum-mileage=' + mileageTo))
    outputURL = outputURL + ('' if (bodyType == '') else ('&body-type=' + bodyType))
    outputURL = outputURL + ('' if (fuelType == '') else ('&fuel-type=' + fuelType))
    outputURL = outputURL + ('' if (engineSizeFrom == '') else ('&minimum-badge-engine-size=' + engineSizeFrom))
    outputURL = outputURL + ('' if (engineSizeTo == '') else ('&maximum-badge-engine-size=' + engineSizeTo))
    outputURL = outputURL + ('' if (gearbox == '') else ('&transmission=' + gearbox))
    outputURL = outputURL + ('' if (keywords == '') else ('&keywords=' + keywords))

    return outputURL


# Randomly choose one of the previously defined user agents
def pickAgent():
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


# The main code block we want to run
def main():
    # Firstly get a user agent
    user_agent = pickAgent()
    
    # Next get URL to query
    searchURL = urlBuilder()
    
    # Now run load webpage
    response = requests.get(searchURL, headers = {'User-Agent': user_agent})

    # Create soup
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find pagination results so we know how many pages to iterate through
    maxPages = findMaxPages(soup)
    
    # Initialise empty results list
    masterResultsList = []
    
    # Parse first page
    resultsList = parsePage(soup)
    
    # Concatenate lists together
    masterResultsList = masterResultsList + resultsList
    
    if maxPages > 1:
        # Loop through all the pages and add the results to a list
        for pgNum in range(2, maxPages + 1):     # Since Python only goes to less than the latter number
            # Append the page number onto the URL to get subsequent pages
            currentSearchURL = searchURL + '&page=' + pgNum
        
            # Now run load webpage
            response = requests.get(searchURL, headers = {'User-Agent': user_agent})
        
            # Create soup
            soup = BeautifulSoup(response.text, "html.parser")




main()
    
    
    
    

























