var margin = { top: 20, right: 20, bottom: 50, left: 50 },
    statsMargin = { top: 10, right: 10, bottom: 10, left: 10, donutSize: 40 },
    leg = {rectSize: 10, rectSpacing: 4, rectTextSize: 11},
    basewidth = 565,
    baseheight = 565,
    width = basewidth - margin.left - margin.right,
    height = baseheight - margin.top - margin.bottom,
    xLabel,
    yLabel,
    xLabelTxt,
    yLabelTxt,
    svg,
    myDuration = 500,
    alldata,
    statdata = {},
    xaxis,
    yaxis,
    xaxislabel,
    yaxislabel,
    freezeMouseover = 0,
    allDots,
    xMin = 0,
    xMax = 1,
    yMin = 0,
    yMax = 1,
    statsWidth = 278,
    statsHeight = 278,
    statsRadius = d3.min([statsWidth - statsMargin.left - statsMargin.right, statsHeight - statsMargin.top - statsMargin.bottom]) / 2,
    statCharts = ["ProductLine", "Rating_kW", "EngineDetails", "AICCode", "Region"],
    colors = {},
    firstStats = 1,
    userView = "loadProfiles",
    statsMeasure = "count";

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

// Get DOM elements at global variables so we don't need to keep finding them every time we want to use them
var clustersDiv = d3.select("#clustersChart");
var kf = d3.select("#keyfacts");
var chart = d3.select("#chartlink");
var caclStatsButton = d3.select("#calcButton");

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
            caclStatsButton.attr("disabled", null);

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
            caclStatsButton.attr("disabled", null);

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
			.on("change", "getData();");

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
			.on("change", "updateScattergram();");
			
		axisSelector.append("br");
		
		axisSelector
			.append("span")
			.text("y-axis   ")
		
		axisSelector
			.append("select")
			.attr("name", "yaxis")
			.attr("id", "yaxisSel")
			.on("change", "updateScattergram();");
		
		// Force the on change event to fire and populate the x and y axis boxes
		getData();
	});
}


function getData() {
	var chooseSearchName = $("#chooseSearchName");
	var selectedSearchName = chooseSearchName[0].options[chooseSearchName[0].selectedIndex].text;
	
	$.getJSON("/api/getdata/" + encodeURI(selectedSearchName), function (json) {
		var a = 1;
	});
}

































