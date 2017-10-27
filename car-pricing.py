# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 14:02:06 2017

@author: ColinParr

This is used to scrape car results from Autotrader and analyse them using ML
"""

from bs4 import BeautifulSoup
import csv
import random
import datetime

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

def pickHeader():
    return random.choice(user_agents)[0]
    
    
    
    
    
    