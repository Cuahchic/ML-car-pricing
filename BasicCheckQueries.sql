/*
TRUNCATE TABLE car.cardetails;
TRUNCATE TABLE car.searchcriteria;
TRUNCATE TABLE car.sessions;
*/

SELECT * FROM car.cardetails;
SELECT * FROM car.searchcriteria;
SELECT * FROM car.sessions;

SELECT searchURL FROM car.searchcriteria;
SELECT * FROM car.cardetails WHERE price = 26995;