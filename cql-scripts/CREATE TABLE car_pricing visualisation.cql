DROP TABLE car_pricing.searchdata;

CREATE TABLE car_pricing.searchdata (
    // The partition key will be advertid and the clustering key will be foundtime as our most common query will be finding stats around each advert
    advertid			text,
    foundtime			timestamp,
    
    // We will store the search criteria in a map that way we only need to worry about what things were actually chosen (no NULL columns etc)
    searchname			text,
    searchcriteria		map<text, text>,
    
    // Information about the group of adverts found that this advert relates to (i.e. each run of the scraping program)
	sessioncreatedtime  timestamp,
    hostname       		text,
    pythonversion  		text,
    codeversion			text,
    
    // This is the information about an advert
    adtitle				text,
    attentiongrab		text,
    year				int,
    plate				int,
    bodytype			text,
    mileage				int,
    transmission		text,
    enginesize			float,
    bhp					int,
    fueltype			text,
    price				float,
    predictedprice		float,
    sellertype			text,
    distancefromyou		int,
    location			text,
    make				text,
    model				text,
    modelfull			text,
    dealername			text,
    features			text,
    urbanmpg			float,
    extraurbanmpg		float,
    averagempg			float,
    annualtax			float,
    adverthtml			text,
    thumbnail			blob,
    
    PRIMARY KEY ((searchname, advertid), foundtime)
) WITH CLUSTERING ORDER BY (foundtime DESC);




