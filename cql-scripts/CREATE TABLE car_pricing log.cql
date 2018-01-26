CREATE TABLE car_pricing.log (
	logtime				timestamp,
	sessioncreatedtime	timestamp,
	message				text,
	
	PRIMARY KEY (sessioncreatedtime, logtime)
) WITH CLUSTERING ORDER BY (logtime DESC);