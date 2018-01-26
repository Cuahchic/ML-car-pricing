DROP TABLE car_pricing.searchqueries;

CREATE TABLE car_pricing.searchqueries (
    // We will store the search criteria in a map that way we only need to worry about what things were actually chosen (no NULL columns etc)
    searchname			text,
    searchcriteria		map<text, text>,
    
    PRIMARY KEY (searchname)
);




