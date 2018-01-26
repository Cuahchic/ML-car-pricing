# ML-car-pricing
Scrape car listings from Autotrader and store them in a Cassandra database, undertake machine learning on the results and visualise it using D3.js.

Written in Python 3.6.3 and uses a version written by [Hamid Adelyear](http://hamidadelyar.com/project/auto-trader-scraper/) as a starting point (although my version is heavily modified and adds much more features and functionality).

## File Structure
The folder called 'cql-scripts' contains the scripts to create the Cassandra tables.

The folder called 'ml-testing' contains the data exploration and testing done for creating the ML models. It also can be used to retrain the model using data that has been scraped.

The folder called 'scraper' contains the Python code for doing the web scraping. This can be run on a schedule to regularly pull down data, but be warned that too frequent pulls may result in being IP blocked.

The folder called 'static' contains the CSS and JavaScript files (and dependencies) which are required for the D3.js visualisation.

The folder called 'templates' contains the HTML file for the visualisation.

## Getting Started
This program was developed on a Windows machine, so instructions will only be valid for this operating system.

To begin, download and install Python. I recommend [Anaconda](https://conda.io/docs/user-guide/install/download.html). It will greatly help development, particularly the installation of new packages, by [adding the Python directories to the Windows PATH variable](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-7).

Once Python is installed and set up, [download and install Cassandra](https://www.datastax.com/2012/01/getting-started-with-apache-cassandra-on-windows-the-easy-way). [Create a keyspace](https://docs.datastax.com/en/cql/3.3/cql/cql_reference/cqlCreateKeyspace.html) called 'car_pricing' by running:
``` SQL
CREATE KEYSPACE car_pricing;
```
Once the keyspace has been created, run the ```CREATE TABLE``` commands in the three scripts in the 'cql-scripts' folder.

Now we need to set up search criteria ...

Run the scraper from the command line by first navigating to the directory, then running the script:
``` Batchfile
C:\Users\JoeBloggs>cd ..\..\GitHub\ML-car-pricing\scraper
C:\GitHub\ML-car-pricing\scraper>python autotrader_scraper.py
```
Note that this will take some time to complete.

Initialise the Flask server by running the following from the command line:
``` Batchfile
C:\Users\JoeBloggs>cd ..\..\GitHub\ML-car-pricing
C:\GitHub\ML-car-pricing>python frontend.py
```
Now you can navigate to ```http://127.0.0.1:65010/cars``` in your web browser to see the results.

## Visualisation Overview
