// Global variables
var margin = { top: 20, right: 20, bottom: 50, left: 50 },
    basewidth = 565,
    baseheight = 565,
    width = basewidth - margin.left - margin.right,
    height = baseheight - margin.top - margin.bottom,
	
	statsWidth = 278,
    statsHeight = 278,
    statsMargin = { top: 10, right: 10, bottom: 10, left: 10, donutSize: 40 },
    statsRadius = d3.min([statsWidth - statsMargin.left - statsMargin.right, statsHeight - statsMargin.top - statsMargin.bottom]) / 2,
	
    svg,
	allDots,
	
    xaxis_class,
    yaxis_class,
    xaxislabel,
    yaxislabel,
	
	xMin = {},
    xMax = {},
    yMin = {},
    yMax = {},
	xRange = {},
	yRange = {},
	
    xLabel,
    yLabel,
    xLabelTxt,
    yLabelTxt,
	
	plottableColumns = [],
	data = {},
	
	freezeMouseover = 0,
	
	clustersDiv = d3.select("#clustersChart");

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
    .value(function (d) { return d[statsMeasure]; });

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
            xMin = ui.values[0];
            xMax = ui.values[1];

            zoom(xMin, xMax, "x");
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
            yMin = ui.values[0];
            yMax = ui.values[1];

            zoom(yMin, yMax, "y");
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
	
	$.getJSON("/api/getdata/" + encodeURI(selectedSearchName), function (json) {
		data = json["data"];
		plottableColumns = json["plottable_columns"];
		
		populateXandYSelectors();
		createScattergram();
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
        .attr("r", 1.5)
        .attr("cx", xMap)
        .attr("cy", yMap)
        .attr("clip-path", "url(#clip)")
        .on("mouseover", mouseover)
        .on("mouseleave", mouseleave)
        .on("click", click);

    // Get all dots for mouseover
    selectDots();
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
	xMin = data.reduce(function(prev, curr) { return prev[xLabel] < curr[xLabel] ? prev : curr; })[xLabel];
	xMax = data.reduce(function(prev, curr) { return prev[xLabel] > curr[xLabel] ? prev : curr; })[xLabel];
	yMin = data.reduce(function(prev, curr) { return prev[yLabel] < curr[yLabel] ? prev : curr; })[yLabel];
	yMax = data.reduce(function(prev, curr) { return prev[yLabel] > curr[yLabel] ? prev : curr; })[yLabel];
	
	xRange = xMax - xMin;
	yRange = yMax - yMin;
	
	xScale.domain([xMin - (0.01 * xRange), xMax + (0.01 * xRange)]);
    yScale.domain([yMin - (0.01 * yRange), yMax + (0.01 * yRange)]);
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
        .attr("r", 1.5)
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
    }
};

// Function to reset page when cursor moved away from circle
function mouseleave(d) {
    if (freezeMouseover == 0) {
        // Bring all circles back to full opacity
        allDots.attr("opacity", 1);
    };
};

// Function to freeze mouseover text
function click(d) {
    // Change value of freezeMouseover variable
    freezeMouseover = (freezeMouseover + 1) % 2;
};


// Function to zoom axis
function zoom(begin, end, whichAxis) {
    // Calculate new tick values for axis
	var adj_begin = xMin + begin * xRange;		// Begin is in the range [0,1] and represents the fractional slider range, adj_begin converts this into the units of the axis
	var adj_end = xMax - (1 - end) * xRange;
	
    var rng = adj_end - adj_begin;
    var step = rng / 10;
    var ticks = [];
    for (var i = 0; i <= 10; i++) {
        ticks.push(adj_begin + step * i);
    }

    // Change scale domain and assign tick values calculated above
    if (whichAxis == "x") {
        xScale.domain([(-0.01 / 1.02 * rng) + adj_begin, adj_end + (0.01 / 1.02 * rng)]);
        xAxis.tickValues(ticks);
        xaxis_class.call(xAxis);
        allDots.attr("cx", xMap);
    }
    else if (whichAxis == "y") {
        yScale.domain([(-0.01 / 1.02 * rng) + adj_begin, adj_end + (0.01 / 1.02 * rng)]);
        yAxis.tickValues(ticks);
        yaxis_class.call(yAxis);
        allDots.attr("cy", yMap);
    }
}










