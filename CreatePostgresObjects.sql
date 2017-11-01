-- Create user and user group manually to avoid putting passwords in SQL file!

-- Give access to user group
GRANT USAGE ON SCHEMA car TO carappprivileges;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA car TO carappprivileges;
GRANT SELECT ON ALL TABLES IN SCHEMA car to carappprivileges;
GRANT INSERT ON ALL TABLES IN SCHEMA car to carappprivileges;
GRANT UPDATE ON ALL TABLES IN SCHEMA car to carappprivileges;
GRANT carappprivileges TO carapp;

-- Create necessary tables
--DROP TABLE car.sessions
CREATE TABLE car.sessions (
    sessionID   		serial PRIMARY KEY,
    searchCriteriaID	INT NOT NULL,
	sessionCreatedTime  TIMESTAMP NOT NULL,
    hostName       		VARCHAR(100) NOT NULL,
    pythonVersion  		VARCHAR(10) NOT NULL,
    codeVersion			VARCHAR(10) NOT NULL
);

--DROP TABLE car.searchCriteria
CREATE TABLE car.searchCriteria (
    searchCriteriaID 	serial PRIMARY KEY,
    searchName			VARCHAR(50) NULL,
    milesFrom			INT NOT NULL,
    postCode			VARCHAR(10) NOT NULL,
    carTypes			VARCHAR(100) NOT NULL,
    make				VARCHAR(20) NULL,
    model				VARCHAR(20) NULL,
    modelVariant		VARCHAR(50) NULL,
    priceFrom			FLOAT NULL,
    priceTo				FLOAT NULL,
    yearFrom			INT NULL,
    yearTo				INT NULL,
    mileageFrom			INT NULL,
    mileageTo			INT NULL,
    bodyType			VARCHAR(20) NULL,
    fuelType			VARCHAR(20) NULL,
    engineSizeFrom		FLOAT NULL,
    engineSizeTo		FLOAT NULL,
    transmission		VARCHAR(20) NULL,
    keywords			VARCHAR(50) NULL
);

CREATE TABLE car.carDetails (
    carDetailsID		serial PRIMARY KEY,
    advertID			INT NOT NULL,
    sessionID			INT NOT NULL,
    foundTime			TIMESTAMP NOT NULL,
    adTitle				VARCHAR(100) NOT NULL,
    attentionGrab		VARCHAR(200) NULL,
    year				INT NULL,
    plate				INT NULL,
    bodyType			VARCHAR(20) NULL,
    mileage				INT NULL,
    transmission		VARCHAR(20) NULL,
    engineSize			FLOAT NULL,
    bhp					INT NULL,
    fuelType			VARCHAR(20) NULL,
    price				FLOAT NULL,
    sellerType			VARCHAR(20) NULL,
    distanceFromYou		INT NULL,
    location			VARCHAR(50) NULL,
    make				VARCHAR(20) NULL,
    model				VARCHAR(20) NULL,
    dealerName			VARCHAR(100) NULL,
    features			VARCHAR NULL,
    urbanMPG			FLOAT NULL,
    extraUrbanMPG		FLOAT NULL,
    averageMPG			FLOAT NULL,
    annualTax			FLOAT NULL
);







