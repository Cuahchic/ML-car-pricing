# ML-car-pricing
Scrape car listings from Autotrader and store them in a Cassandra database, undertake machine learning on the results and visualise it using D3.js.

Written in Python 3.6.3 and uses a version written by [Hamid Adelyear](http://hamidadelyar.com/project/auto-trader-scraper/) as a starting point (although my version is heavily modified and adds much more features and functionality).

## File Structure
The folder called 'cql-scripts' contains the scripts to create the Cassandra tables.

The folder called 'img' contains an example visualisation image for the README.

The folder called 'ml-testing' contains the data exploration and testing done for creating the ML models. It also can be used to retrain the model using data that has been scraped.

The folder called 'scraper' contains the Python code for doing the web scraping. This can be run on a schedule to regularly pull down data, but be warned that too frequent pulls may result in being IP blocked.

The folder called 'static' contains the CSS and JavaScript files (and dependencies) which are required for the D3.js visualisation.

The folder called 'templates' contains the HTML file for the visualisation.

## Getting Started
This program was developed on a Windows machine, so instructions will only be valid for this operating system.

To begin, download and install Python. I recommend [Anaconda](https://conda.io/docs/user-guide/install/download.html). It will greatly help development, particularly the installation of new packages, by [adding the Python directories to the Windows PATH variable](https://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-7).

Once Python is installed and set up, [download and install Cassandra](https://www.datastax.com/2012/01/getting-started-with-apache-cassandra-on-windows-the-easy-way). [Create a keyspace](https://docs.datastax.com/en/cql/3.3/cql/cql_reference/cqlCreateKeyspace.html) called 'car_pricing' by running:
```SQL
CREATE KEYSPACE car_pricing;
```
Once the keyspace has been created, run the ```CREATE TABLE``` commands in the three scripts in the 'cql-scripts' folder.

Now we need to set up search criteria, an example of which can be seen in the 'Example Search Criteria.cql' file under the 'cql-scripts' folder. The key of the map should correspond to the keys as below (this can also be found in the 'autotrader_scraper.py' file, in the 'translations' variable of the 'searchCriteria' class):
```
{'Miles From': 'radius',
 'Postcode': 'postcode',
 'Car Types': 'onesearchad',
 'Make': 'make',
 'Model': 'model',
 'Model Variant': 'aggregatedTrim',
 'Price From': 'price-from',
 'Price To': 'price-to',
 'Year From': 'year-from',
 'Year To': 'year-to',
 'Mileage From': 'minimum-mileage',
 'Mileage To': 'maximum-mileage',
 'Body Types': 'body-type',
 'Fuel Type': 'fuel-type',
 'Engine Size From': 'minimum-badge-engine-size',
 'Engine Size To': 'maximum-badge-engine-size',
 'Transmission': 'transmission',
 'Keywords': 'keywords'}
```
Any variables which can have multiple choices, for example 'Car Types', should be stored as a string separated by a comma, e.g. 'New,Used'.

Run the scraper from the command line by first navigating to the directory, then running the script:
```Batchfile
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

## Price Prediction Overview
The first thing we need to do is define what features are likely to be useful when predicting car prices. Through data exploration these were found to be:
```
year - the year of registration
plate - which half of the year it was registered
mileage - number of miles covered by car
enginesize - engine capacity in litres
bhp - the power output of the engine in brake horsepower
averagempg - how fuel efficient the car is in miles per gallon
advertage_days - how long the advert had been advertised for
bodytype - whether is was a saloon, hatchback, estate, etc
fueltype - whether the car was petrol or diesel
make - the brand
model - the model within the brand
sellertype - whether it was a trade or private seller
```
For some algorithms, categorical features need to be [one-hot encoded](https://hackernoon.com/what-is-one-hot-encoding-why-and-when-do-you-have-to-use-it-e3c6186d008f) before they can be used to make predictions. Additionally, for some algorithms, too many features (columns) can make for poor predictions, and a dimensionality reduction technique such as [principle components analysis](http://setosa.io/ev/principal-component-analysis/) or [t-Distributed Stochastic Neighbour Embedding](https://lvdmaaten.github.io/tsne/) should be used to reduce the number of features.

There were three algorithms considered - [Gradient Boosted Regression](https://machinelearningmastery.com/gentle-introduction-gradient-boosting-algorithm-machine-learning/), [Random Forest Regression](https://www.r-bloggers.com/how-random-forests-improve-simple-regression-trees/) and [k-Nearest Neighbours Regression](http://www.saedsayad.com/k_nearest_neighbors_reg.htm). Using Grid Search with 3-fold cross validation for each of these, they were compared and it was found that Gradient Boosted Regression minimised the median average deviation the most.

With the optimum parameters found, the predicted vs actual price looked as follows:
![ML results](https://github.com/Cuahchic/ML-car-pricing/blob/master/ml-testing/Actual%20vs%20Predicted%20Prices.png)

It's worth remembering that the goal here is to predict car prices, but those prices are being set by car salespeople, and are inherently flawed (i.e. they don't represent the global solution). With enough data, the salespersons prices should average out to get a good picture of the price differences.

## Visualisation Overview
Once everything is working, you should be able to see the following visualisation:

![Visualisation example](https://github.com/Cuahchic/ML-car-pricing/blob/master/img/visualisation-image.PNG)

The visualisation is split into 7 sections:

### Controls
Use the 'Search Name' drop down to choose one of your saved searches to view the results for.

Use the 'x-axis' and 'y-axis' drop downs to choose which variables to display on the scattergram.

### Manufacturers
This is a donut chart showing the distribution of different car manufacturers in the data. THis will automatically update when the scattergram sliders are changed. Mouseover to get the exact number and percentage of total.

### Image
This shows the advert title and first image when the user mouseovers a point on the scattergram. The image is clickable and takes you to the advert on the Autotrader website.

### Key Facts
This shows some key details about the car when the user mouseovers a point on the scattergram.

### Price History
This shows any prices changes the advert has had when the user mouseovers a point on the scattergram.

### Map
A map showing the home location (the post code used for the search) in blue and the location of the car in red when the user mouseovers a point on the scattergram. Use the zoom buttons to zoom in and out.

### Scattergram
There is where the bulk of the action happens. Mouseover a point to populate the Image, Key Facts, Price History and Map sections. Single-left click on a point to freeze the mouseover and allow the image to be clicked.

Use the sliders to zoom the chart axes and update the donut chart as appropriate.





