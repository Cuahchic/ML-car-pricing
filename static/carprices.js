
// Global variables
var margin = { top: 20, right: 20, bottom: 50, left: 50 },
    basewidth = 565,
    baseheight = 565,
    width = basewidth - margin.left - margin.right,
    height = baseheight - margin.top - margin.bottom,
	
	leg = {rectSize: 10, rectSpacing: 4, rectTextSize: 11},
	
	statsWidth = 240,
    statsHeight = 240,
    statsMargin = { top: 10, right: 10, bottom: 10, left: 10, donutSize: 40 },
    statsRadius = d3.min([statsWidth - statsMargin.left - statsMargin.right, statsHeight - statsMargin.top - statsMargin.bottom]) / 2,
	
	myDuration = 500,
	totalDonutSize,
	selectedSearchNameEncoded,
	keyFacts = [],
	priceHistory = [],
	
    xaxis_class,
    yaxis_class,
    xaxislabel,
    yaxislabel,
	
	xMin = {"zoom": 0},
    xMax = {"zoom": 1},
    yMin = {"zoom": 0},
    yMax = {"zoom": 1},
	xRange = {"zoom": 1},
	yRange = {"zoom": 1},
	
    xLabel,
    yLabel,
    xLabelTxt,
    yLabelTxt,
	
	plottableColumns = [],
	data = {},
	colors = {},
	pieData = [],
	
	freezeMouseover = 0,
	
	locationsMap,
	redIcon,
	blueIcon,
	mapMarkers = {},
	geocoder,
	
	svg,
	donutG,
	donutMouseOverDiv,
	allDots,
	clustersDiv = d3.select("#clustersChart"),
	carImageImg = d3.select("#carImageContent").select("img"),
	adTitleSpan = d3.select("#adTitleText"),
	keyFactsList = d3.select("#keyFactsList"),
	priceHistoryList = d3.select("#priceHistoryList");

	
// setup x 
var xValue = function (d) { return d[xLabel]; }, // data -> value
    xScale = d3.scaleLinear().range([0, width]), // value -> display, range sets output range, in this case 0 to width
    xMap = function (d) { return xScale(xValue(d)); }, // data -> display
    xAxis = d3.axisBottom().scale(xScale);

// setup y
var yValue = function (d) { return d[yLabel]; }, // data -> value
    yScale = d3.scaleLinear().range([height, 0]), // value -> display, range sets output range, in this case height to 0
    yMap = function (d) { return yScale(yValue(d)); }, // data -> display
    yAxis = d3.axisLeft().scale(yScale);

// Get arc function for plotting stats
var arc = d3.arc()
    .innerRadius(statsRadius - statsMargin.donutSize)
    .outerRadius(statsRadius);

// Set up pie function
var pie = d3.pie()
    .value(function (d) { return d.count; });

// Read in data
listSearches();

// Create sliders for zooming
$(function () {
    $("#xSlider").slider({
        range: true,
        min: 0,
        max: 1,
        values: [0, 1],
        step: 0.01,
        slide: function (event, ui) {
			xMin["zoom"] = ui.values[0];
			xMax["zoom"] = ui.values[1];
			xRange["zoom"] = xMax["zoom"] - xMin["zoom"];
			
			zoom("x");
        }
    });
});

$(function () {
    $("#ySlider").slider({
        orientation: "vertical",
        range: true,
        min: 0,
        max: 1,
        values: [0, 1],
        step: 0.01,
        slide: function (event, ui) {
			yMin["zoom"] = ui.values[0];
			yMax["zoom"] = ui.values[1];
			yRange["zoom"] = yMax["zoom"] - yMin["zoom"];
			
			zoom("y");
        }
    });
});


// ****************************************************************************
// ****************************************************************************
// ************************** Start of functions ******************************
// ****************************************************************************
// ****************************************************************************

// Query the database to find the unique search names
function listSearches() {
	$.getJSON("/api/listsearches", function (json) {
		var axisSelector = d3.select("#axisSelectorDiv");
		
		axisSelector
			.append("span")
			.text("Choose search name   ")
		
		var signalSelect = axisSelector
			.append("select")
			.attr("id", "chooseSearchName")
			.on("change", getData);

		var signalOptions = signalSelect
			.selectAll("option")
			.data(json["searches"]).enter()
			.append("option")
			.text(function (d) { return d; });
			
		axisSelector.append("br");
		
		axisSelector
			.append("span")
			.text("x-axis   ")
			
		axisSelector
			.append("select")
			.attr("name", "xaxis")
			.attr("id", "xaxisSel")
			.on("change", updateScattergram);
			
		axisSelector.append("br");
		
		axisSelector
			.append("span")
			.text("y-axis   ")
		
		axisSelector
			.append("select")
			.attr("name", "yaxis")
			.attr("id", "yaxisSel")
			.on("change", updateScattergram);
		
		// Force the on change event to fire and populate the x and y axis boxes
		getData();
	});
}


// Query the database to get the relevant data related to a search
function getData() {
	var chooseSearchName = $("#chooseSearchName");
	var selectedSearchName = chooseSearchName[0].options[chooseSearchName[0].selectedIndex].text;
	selectedSearchNameEncoded = encodeURI(selectedSearchName);
	
	$.getJSON("/api/getdata/" + selectedSearchNameEncoded, function (json) {
		data = json["data"];
		plottableColumns = json["plottable_columns"];
		
		data.forEach(function(d) {
			// Format of API output is "Thu, 04 Jan 2018 14:26:52 GMT"
			var ts = Date.parse(d.foundtime);
			
			d["foundtime_date"] = new Date(ts);
		});
		
		populateXandYSelectors();
		createScattergram();
		createStatsCharts();
		createCarLocationsMap();
	});
}


// Function to put the plottable columns as options in the X and Y axis selectors
function populateXandYSelectors() {
	var xaxisSel = d3.select("#xaxisSel");
	
	xaxisSel
		.selectAll("option")
		.data(plottableColumns)
		.enter()
		.append("option")
		.property("value", function(d) { return d.name; })
		.text(function (d) { return d.friendly_name; });
	
	var yaxisSel = d3.select("#yaxisSel");
	
	yaxisSel
		.selectAll("option")
		.data(plottableColumns)
		.enter()
		.append("option")
		.property("value", function(d) { return d.name; })
		.text(function (d) { return d.friendly_name; });
		
	$('select[id=xaxisSel] option:eq(0)').attr('selected', 'selected');  // Select first option for x axis
	$('select[id=yaxisSel] option:eq(1)').attr('selected', 'selected');  // Select second option for y axis
}


// Function to create the scattergram
function createScattergram() {
    // Get selected elements
    getSelectedAxisOptions();

    // Add svg elements to div
    svg = clustersDiv.append("svg")
        .attr("width", basewidth)
        .attr("height", baseheight)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Find min and max values to set the domain of each axis
    resizeDomains();

    // x-axis
    xaxis_class = svg.append("g")
        .attr("class", "axis")
        .attr("id", "xaxis")
        .attr("transform", "translate(0," + height + ")");
        
    // y-axis
    yaxis_class = svg.append("g")
        .attr("class", "axis")
        .attr("id", "yaxis");
    
    // Add axis labels
    createAxisLabels();

    // Do the axis creation after adding text so the text appears on top --- NEEDS REVISITED
    /*xAxis.tickFormat(d3.format(".2f"));
    yAxis.tickFormat(d3.format(".2f"));*/
    xaxis_class.call(xAxis);
    yaxis_class.call(yAxis);

    // Add a clip path so that when we zoom any circles that go out of the chart area are not drawn
    var clip = svg.append("svg:clipPath")
        .attr("id", "clip")
        .append("svg:rect")
        .attr("id", "clip-rect")
        .attr("x", "0px")
        .attr("y", "0px")
        .attr("width", width)    // This accounts for 0.01 margin left and right, top and bottom
        .attr("height", height);

    // draw dots
    svg.selectAll(".dot")
        .data(data)
        .enter().append("circle")
        .attr("class", "dot")
        .attr("cx", xMap)
        .attr("cy", yMap)
        .attr("clip-path", "url(#clip)")
        .on("mouseover", mouseover)
        .on("mouseleave", mouseleave)
        .on("click", click);

    // Get all dots for mouseover
    selectDots();
}


// Function to create the map and set up things for viewing later
function createCarLocationsMap() {
	// Create icon objects using https://github.com/pointhi/leaflet-color-markers/blob/master/js/leaflet-color-markers.js
	redIcon = new L.Icon({
		iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
		shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
		iconSize: [25, 41],
		iconAnchor: [12, 41],
		popupAnchor: [1, -34],
		shadowSize: [41, 41]
	});
	
	blueIcon = new L.Icon({
		iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
		shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
		iconSize: [25, 41],
		iconAnchor: [12, 41],
		popupAnchor: [1, -34],
		shadowSize: [41, 41]
	});
	
	// Initialise the map and give it an image layer provided by OpenStreetMap
	locationsMap = L.map('locationMapContent').setView([54.357,-2.215], 5);
	
	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		maxZoom: 19,
		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
	}).addTo(locationsMap);
	
	// Initialise geocoder
	geocoder = new L.Control.Geocoder.Nominatim();
	
	// Get the users home location coordinates using geolookup, see https://stackoverflow.com/questions/30934341/leaflet-geosearch-get-lon-lat-from-address
	var postCode = data[0].searchcriteria.Postcode;
	
	postCode = postCode.substring(0, postCode.length - 3) + ' ' + postCode.substring(postCode.length - 3, postCode.length)	// Put a space in the postcode
	
	geocoder.geocode(postCode, function(results) {
		var latLng = new L.LatLng(results[0].center.lat, results[0].center.lng);
		var homeMarker = new L.Marker(latLng, {draggable:false, icon: blueIcon});
		locationsMap.addLayer(homeMarker);
		
		homeMarker.bindPopup("Home").openPopup();
		
		mapMarkers["home"] = homeMarker;
	});
}


// Function to get the selected values of x and y axis from the drop down menus
function getSelectedAxisOptions() {
    xLabel = $("#xaxisSel")[0].value;
    yLabel = $("#yaxisSel")[0].value;
    xLabelTxt = $("#xaxisSel")[0].options[$("#xaxisSel")[0].selectedIndex].text;
    yLabelTxt = $("#yaxisSel")[0].options[$("#yaxisSel")[0].selectedIndex].text;
}


// Function to scale domains based on min and max values of chosen columns
function resizeDomains() {
	// Set up original values which track the overall ranges based on all the data
	xMin["orig"] = data.reduce(function(prev, curr) { return prev[xLabel] < curr[xLabel] ? prev : curr; })[xLabel];
	xMax["orig"] = data.reduce(function(prev, curr) { return prev[xLabel] > curr[xLabel] ? prev : curr; })[xLabel];
	yMin["orig"] = data.reduce(function(prev, curr) { return prev[yLabel] < curr[yLabel] ? prev : curr; })[yLabel];
	yMax["orig"] = data.reduce(function(prev, curr) { return prev[yLabel] > curr[yLabel] ? prev : curr; })[yLabel];
	
	xRange["orig"] = xMax["orig"] - xMin["orig"];
	yRange["orig"] = yMax["orig"] - yMin["orig"];
	
	// Set up adjusted zoomed values for normalised values scaled to the full range of the data
	calcAdjZoomValues("x");
	calcAdjZoomValues("y");
	
	// Save the total value in the range
	totalDonutSize = data.length;
}


// Function which creates the x and y axis labels
function createAxisLabels() {
    xaxislabel = xaxis_class.append("text")
                    .attr("class", "axislabel")
                    .attr("x", width / 2)
                    .attr("y", margin.bottom * 0.7)
                    .text(xLabelTxt);

    yaxislabel = yaxis_class.append("text")
                    .attr("class", "axislabel")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -height / 2)
                    .attr("y", -margin.left * 0.7)
                    .text(yLabelTxt);
}


// Function to select all dots so we don't need to do this every mouseover
function selectDots() {
    allDots = d3.selectAll(".dot");
}


// Function to update chart when new x or y axis variable selected
function updateScattergram() {
    // Get selected elements
    getSelectedAxisOptions();
	
	// Resize the domain for the new data
	resizeDomains();
	
	// Relabel the numbers on each axis
	xaxis_class.call(xAxis);
    yaxis_class.call(yAxis);
	
    // Get existing elements
    var dots = svg.selectAll(".dot").data(data);
    dots
        .attr("cx", xMap)
        .attr("cy", yMap);

    // New elements
    var dotEnter = dots.enter();
    dotEnter.append("circle")
        .attr("class", "dot")
        .attr("cx", xMap)
        .attr("cy", yMap)
        .on("mouseover", mouseover)
        .on("mouseleave", mouseleave)
        .on("click", click);

    dots.exit().remove();

    // Add axis labels
    updateAxisLabels();

    // Get all dots for mouseover
    selectDots();
}


// Function which amends the x and y axis labels
function updateAxisLabels() {
    xaxislabel.text(xLabelTxt);
    yaxislabel.text(yLabelTxt);
}


// Function to add text to right hand side information on rollover of circle
function mouseover(d) {
    if (freezeMouseover == 0) {
        // Fade all circles
        allDots.attr("opacity", 0.1);

        // Make the mouseover circle full opacity
        d3.select(this).attr("opacity", 1);
		
		// Show car location on map		
		var locationFull = d.location + ", United Kingdom";		// Prevents showing of locations in other countries (e.g. Perth, Australia)
		
		geocoder.geocode(locationFull, function(results) {
			// Remove any lingering markers
			for (var key in mapMarkers) {
				if (key != "home") {
					locationsMap.removeLayer(mapMarkers[key]);
					
					delete mapMarkers[key];
				}
			}
			
			// Add new markers
			var adKey = d.searchcriteria["Search Name"] + " " + d.advertid;
			
			var latLng = new L.LatLng(results[0].center.lat, results[0].center.lng);
			
			mapMarkers[adKey] = new L.Marker(latLng, {draggable:false, icon: redIcon});
			locationsMap.addLayer(mapMarkers[adKey]);
			
			var popupText = "Car</br>" + String(d.distancefromyou) + " miles away</br>" + d.location.charAt(0).toUpperCase() + d.location.slice(1);
			
			mapMarkers[adKey].bindPopup(popupText).openPopup();
		});
		
		// Update the car image
		var imageAPIURL = '/api/adimage?searchname=' + selectedSearchNameEncoded + '&adid=' + d.advertid;
		carImageImg.attr("src", imageAPIURL);
		
		// Update the advert text
		adTitleSpan.text(d.adtitle);
		
		// Update key facts
		keyFacts = [];
		keyFacts.push(String(d.year) + " (" + String(d.plate) + " plate)");
		keyFacts.push(d.bodytype);
		keyFacts.push(String(d.mileage) + " miles");
		keyFacts.push(d.transmission);
		keyFacts.push(String(d.enginesize.toFixed(1)) + "L");
		keyFacts.push(d.fueltype);
		keyFacts.push(d.sellertype + " seller");
		
		updateList(keyFactsList, keyFacts);
		
		// Update price history
		priceHistory = [];
		priceHistory.push("On " + $.datepicker.formatDate('dd M yy', d.foundtime_date) + " price was £" + d.price);
		
		updateList(priceHistoryList, priceHistory);
    }
};


// Function to reset page when cursor moved away from circle
function mouseleave(d) {
    if (freezeMouseover == 0) {
        // Bring all circles back to full opacity
        allDots.attr("opacity", 1);
		
		// Update the car image
		carImageImg.attr("src", "");
		
		// Update the advert text
		adTitleSpan.text("");
		
		// Update key facts
		keyFacts = [];
		
		updateList(keyFactsList, keyFacts);
		
		// Update price history
		priceHistory = [];
		
		updateList(priceHistoryList, priceHistory);
		
		// Remove marker for car
		var adKey = d.searchcriteria["Search Name"] + " " + d.advertid;
		
		if (typeof(mapMarkers[adKey]) != "undefined") {
			locationsMap.removeLayer(mapMarkers[adKey]);
		}
		
		delete mapMarkers[adKey];
    };
};


// Function to freeze mouseover text
function click(d) {
    // Change value of freezeMouseover variable
    freezeMouseover = (freezeMouseover + 1) % 2;
};


// Function to zoom axis
function zoom(whichAxis) {
    // Change scale domain and assign tick values
    if (whichAxis == "x") {
		// Calculate new tick values for axis
		calcAdjZoomValues("x");
		
        xaxis_class.call(xAxis);
        allDots.attr("cx", xMap);
    }
    else if (whichAxis == "y") {
		calcAdjZoomValues("y");
		
        yaxis_class.call(yAxis);
        allDots.attr("cy", yMap);
    }
	
	// Recalculate the data in the window
	updateStatsCharts();
}


// Function to update the key facts section of the page on mouseover
function updateList(ulObject, dataList) {	
	var list = ulObject
		.selectAll("li")
		.data(dataList);
		
	var listEnter = list.enter().append("li");
	
	listEnter
		.merge(list)
		.text(function (d) { return d; });
		
	list.exit().remove();
}


// Function to calculate the adjusted zoom values based on the original values and the current zoom position
function calcAdjZoomValues(whichAxis) {
	if (whichAxis == "x") {
		xMin["adj_zoom"] = xMin["orig"] + xMin["zoom"] * xRange["orig"];		// xMin["zoom"] is in the range [0,1] and represents the fractional slider range, xMin["adj_zoom"] converts this into the units of the axis
		xMax["adj_zoom"] = xMax["orig"] - (1 - xMax["zoom"]) * xRange["orig"];
		
		xRange["adj_zoom"] = xMax["adj_zoom"] - xMin["adj_zoom"];
		
		xScale.domain([(-0.01 / 1.02 * xRange["adj_zoom"]) + xMin["adj_zoom"], xMax["adj_zoom"] + (0.01 / 1.02 * xRange["adj_zoom"])]);
	}
	else if (whichAxis == "y") {
		yMin["adj_zoom"] = yMin["orig"] + yMin["zoom"] * yRange["orig"];
		yMax["adj_zoom"] = yMax["orig"] - (1 - yMax["zoom"]) * yRange["orig"];
		
		yRange["adj_zoom"] = yMax["adj_zoom"] - yMin["adj_zoom"];
		
		yScale.domain([(-0.01 / 1.02 * yRange["adj_zoom"]) + yMin["adj_zoom"], yMax["adj_zoom"] + (0.01 / 1.02 * yRange["adj_zoom"])]);
	}
}

// Function to create statistics charts
function createStatsCharts() {
    // Create SVG element inside div
	var statChartsDiv = d3.select("#makesDonutContent");
	
	donutG = statChartsDiv
		.append("svg")
		.attr("width", statsWidth)
		.attr("height", statsHeight)
		.attr("id", "svgMakesDonut")	
		.append("g")
		.attr("transform", "translate(" + statsWidth / 2 + "," + statsHeight / 2 + ")");

	donutMouseOverDiv = statChartsDiv
		.append("div")
		.attr("class", "donutTooltip")
		.attr("id", "donutTooltipMakes");

    updateStatsCharts();
}


// Summarise data for statistics plotting
function summariseData() {
    var tmp = {};	// Use this to create a dictionary we can turn into an array for plotting
	pieData = [];	// Reset this variable because the zoom might have changed so we need to recount the relevant makes
	
	totalDonutSize = 0;
	
	data.forEach(function (d) {
        if (d[xLabel] >= xMin["adj_zoom"] && d[xLabel] <= xMax["adj_zoom"] && d[yLabel] >= yMin["adj_zoom"] && d[yLabel] <= yMax["adj_zoom"]) {
			if (typeof (tmp[d.make]) == "undefined") {	// Add the make if we haven't seen it before
				tmp[d.make] = 0;
			}

			tmp[d.make] += 1;
			totalDonutSize += 1;	// Count how many entries are in the zoomable view
        }
    });

    // Convert key value pair into array
	for (var k in tmp) {  // Each k will be a new car make (e.g. Volswagen, BMW, etc)
		var o = {};

		o["name"] = k;
		o["count"] = tmp[k];

		pieData.push(o);
	}

	// Get unique colours for each item only if we haven't done this already, on page load there is no zoom
	if ($.isEmptyObject(colors)) {
		colors = generateColours(pieData, "name");
	}
}


// Function to find key for matching with existing data when new data added/removed
function key(d) {
    return d.data.name;
}


// Function to update existing charts
function updateStatsCharts() {
    // Generate the up-to-date pie chart data
	summariseData();
	
	//pie.value(function (d) { return d[statsMeasure]; });    // Rebind pie value accessor

	var path = donutG.selectAll("path");        

	var data0 = path.data(),
		data1 = pie(pieData);

	// Create arc groups
	path = path.data(data1, key);

	// Remove unneeded entries
	path
		.exit()
		.transition()
		.duration(myDuration)
		.attrTween("d", function (d, index) {
			var currentIndex = this._previous.data.region;
			var i = d3.interpolateObject(d, this._previous);
			return function (t) {
				return arc(i(t));
			}
		})
		.remove();

	pathEnter = path.enter();

	pathEnter
		.append("path")
		.each(function (d, i) {
			var narc = findNeighborArc(i, data0, data1, key);
			if (narc) {
				this._current = narc;
				this._previous = narc;
			} else {
				this._current = d;
				this._previous = d;
			}
		})
		.attr("fill", function (d, i) {
			return colors[d.data.name];
		})
		.attr("class", "dpath")
		.merge(path)
		.transition()
		.duration(myDuration)
		.attrTween("d", arcTween);
         
	donutG.selectAll("path")
		.on("mousemove", function (d) {
			var mousePos = d3.mouse(this.parentNode);
			donutMouseOverDiv.style("left", mousePos[0] + 10 + (statsWidth / 2) + "px");
			donutMouseOverDiv.style("top", mousePos[1] - 25 + (statsHeight / 2) + "px");
			donutMouseOverDiv.style("display", "inline-block");

			var displayVal = d.data.count;

			donutMouseOverDiv.html(d.data.name + ": " + displayVal + " (" + d3.format(".1f")(100 * d.data.count / totalDonutSize) + "%)");
		})
		.on("mouseout", function (d) {
			donutMouseOverDiv.style("display", "none");
		});
	
	
	// Get top 5 entries for legend and decide how to centralise them
	var top5SortedData = data1.sort(function (a, b) { return b.data.count - a.data.count });
	var maxElements = Math.min(5, top5SortedData.length);
	top5SortedData = top5SortedData.slice(0, maxElements);
	var maxLength = 0;
	for (var j = 0; j < maxElements; j++) {
		top5SortedData[j].data.name2 = top5SortedData[j].data.name.substring(0, 22);

		maxLength = Math.max(maxLength, top5SortedData[j].data.name2.length);
	}

	// Update legend
	var legend = donutG.selectAll('.legend11').data(top5SortedData, key);

	// Remove unnecessary elements
	legend.exit().remove();

	// Add new legend entries
	legendenter = legend.enter().append('g');

	legendenter
			.attr('class', 'legend11')
		.merge(legend)
			.attr('transform', function (d, i) {
				var height = leg.rectSize + leg.rectSpacing;
				var offset = height * top5SortedData.length / 2;
				var horz = -(maxLength * 2 + height);
				var vert = i * height - offset;
				return "translate(" + horz + "," + vert + ")";
			});

	legendenter.append('rect')
		.attr('width', leg.rectSize)
		.attr('height', leg.rectSize)
		.style("stroke", "rgb(255,255,255)")
		.style("stroke-width", "1px")
		.style('fill', function (d) {
			return colors[d.data.name];
		});

	legendenter.append('text')
		.attr('x', leg.rectSize + leg.rectSpacing)
		.attr('y', "8px")
		.style("fill", "white")
		.style("font-size", leg.rectTextSize)
		.text(function (d) { return d.data.name2; });
}


// Find the arc which adjoins
function findNeighborArc(i, data0, data1, key) {
    var d;
    if (d = findPreceding(i, data0, data1, key)) {
        var obj = cloneObj(d)
        obj.startAngle = d.endAngle;
        return obj;
    } else if (d = findFollowing(i, data0, data1, key)) {
        var obj = cloneObj(d)
        obj.endAngle = d.startAngle;
        return obj;
    }
    return null;
}


// Find the element in data0 that joins the highest preceding element in data1.
function findPreceding(i, data0, data1, key) {
    var m = data0.length;
    while (--i >= 0) {
        var k = key(data1[i]);
        for (var j = 0; j < m; ++j) {
            if (key(data0[j]) === k) return data0[j];
        }
    }
}


// Find the element in data0 that joins the lowest following element in data1.
function findFollowing(i, data0, data1, key) {
    var n = data1.length, m = data0.length;
    while (++i < n) {
        var k = key(data1[i]);
        for (var j = 0; j < m; ++j) {
            if (key(data0[j]) === k) return data0[j];
        }
    }
}


// Determines how to transition from one arc to another
function arcTween(d) {
    var i = d3.interpolate(this._current, d);
    this._current = i(0);

    return function (t) {
        return arc(i(t))
    }
}


// Clone an object
function cloneObj(obj) {
    var o = {};
    for (var i in obj) {
        o[i] = obj[i];
    }
    return o;
}


// Create colour palette
function generateColours(arrayVals, key) {
    var hueStep = Math.floor(360 / arrayVals.length);
    var hexStrings = [];

    for (var i = 0; i < arrayVals.length; i++) {
        var H = i * hueStep;
        var S = Math.floor(Math.random() * 50) + 30;	// Gives range between 30 and 80
        var L = Math.floor(Math.random() * 45) + 35;	// Gives range between 35 and 80

        var hslValue = "hsl(" + H + ", " + S + "%, " + L + "%)";

        var hslValueTC = tinycolor(hslValue);

        hexStrings.push(hslValueTC.toHexString());
    }

    hexStrings = shuffle(hexStrings);		// Randomise array for assignment

    for (var i = 0; i < arrayVals.length; i++) {
        if (!(arrayVals[i][key] in colors)) {         // Only update colours array if we haven't seen this alarm before
            colors[arrayVals[i][key]] = hexStrings[i];
        }
    }

    return colors;
};


// Function to randomise array, from http://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
function shuffle(array) {
    var currentIndex = array.length, temporaryValue, randomIndex;

    // While there remain elements to shuffle...
    while (0 !== currentIndex) {

        // Pick a remaining element...
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex -= 1;

        // And swap it with the current element.
        temporaryValue = array[currentIndex];
        array[currentIndex] = array[randomIndex];
        array[randomIndex] = temporaryValue;
    };

    return array;
};