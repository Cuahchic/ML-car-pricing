# ML-car-pricing
Scrape car listings from Autotrader and store them in a Cassandra database, undertake machine learning on the results and visualise it using D3.js.

Written in Python and uses a version written by [Hamid Adelyear](http://hamidadelyar.com/project/auto-trader-scraper/) as a starting point (although my version is heavily modified).

## File Structure
The folder called 'scraper' contains the Python code for doing the web scraping. Once the parameters have been set up this can be run on a scheduler to continually track prices over time. I run this component bi-weekly.

The folder called 'ml-testing' contains the data exploration and testing done for creating the ML models.

The folder called 'visualiser' contains...

## Visualisation Overview
