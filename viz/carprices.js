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
var xaxissel = $("#xaxisSel");
var yaxissel = $("#yaxisSel");
var kf = d3.select("#keyfacts");
var chart = d3.select("#chartlink");
var caclStatsButton = d3.select("#calcButton");

// Read in data
$('select[name=xaxis] option:eq(0)').attr('selected', 'selected');  // Select first option for x axis
$('select[name=yaxis] option:eq(1)').attr('selected', 'selected');  // Select second option for y axis
readData();

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

// Add action to radio button (do this via JS because otherwise this is called when default is selected and causes problems)
setTimeout(function () {
    d3.selectAll("input.radio_mSR").on("click", optionChange);
}, 1000);


// ****************************************************************************
// ****************************************************************************
// ************************** Start of functions ******************************
// ****************************************************************************
// ****************************************************************************

// Read the CSV data and store it as a JSON
function readData() {
    // Read data
    d3.csv("../../Data/loadprofiles/ScoredHires.csv", function (error, data) {
        // Convert entries which should be numbers from string
        data.forEach(function (d) {
            d.NumPoints = +d.NumPoints;
            d.RunHours_hrs = +d.RunHours_hrs;
            d.PeriodScore = +d.PeriodScore;
            d.StableScore = +d.StableScore;
            d.NegligScore = +d.NegligScore;
            d.IrreguScore = +d.IrreguScore;
            d.HighlyScore = +d.HighlyScore;
            d.RelativeScore = +d.RelativeScore;
            d.TotalScore = +d.TotalScore;
            d.RelTotScore = +d.RelTotScore;
            d.Value_USD = +d.Value_USD;
            d.HireDuration_days = +d.HireDuration_days;
            d.Rating_kW = d.Rating_kW + "kW";

            d.KeyFacts = [];
            // Hire and generator details
            d.KeyFacts.push("Hire Start Date : " + d.OnOffHireStartTime);
            d.KeyFacts.push("Hire Finish Date : " + d.OnOffHireFinishTime);
            d.KeyFacts.push("Hire Duration (days) : " + d.HireDuration_days);
            d.KeyFacts.push("Number Of Data Points : " + d.NumPoints);
            d.KeyFacts.push("Product Line : " + d.ProductLine);
            d.KeyFacts.push("Rating (kW) : " + d.Rating_kW);
            d.KeyFacts.push("Engine : " + d.EngineDetails);

            // Agreement and customer details
            d.KeyFacts.push("Agreement Number : " + d.AgreementNumber);
            d.KeyFacts.push("Customer : " + d.CustomerName);
            d.KeyFacts.push("Industry Sector : " + d.AICCode);
            d.KeyFacts.push("Region : " + d.Region);
            d.KeyFacts.push("Service Centre : " + d.ServiceCenter);
            d.KeyFacts.push("Value (USD) : $" + d3.format(",.2f")(d.Value_USD));
        });

        alldata = data;

        createScattergram();
    })
}

// Function to get the selected values of x and y axis from the drop down menus
function getSelectedAxisOptions() {
    xLabel = xaxissel[0].value;
    yLabel = yaxissel[0].value;
    xLabelTxt = xaxissel[0].options[xaxissel[0].selectedIndex].text;
    yLabelTxt = yaxissel[0].options[yaxissel[0].selectedIndex].text;

    caclStatsButton.attr("disabled", null);
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

    // To avoid dots overlapping axis change the domain slightly
    xScale.domain([-0.01, +1.01]);  // The d3 min function applies a function (xValue) to an array (data). We know our data will be in the range [0,1] so add 0.01 buffer each side.
    yScale.domain([-0.01, +1.01]);

    // x-axis
    xaxis = svg.append("g")
        .attr("class", "axis")
        .attr("id", "xaxis")
        .attr("transform", "translate(0," + height + ")");
        

    // y-axis
    yaxis = svg.append("g")
        .attr("class", "axis")
        .attr("id", "yaxis");
    

    // Add axis labels
    createAxisLabels();

    // Do the axis creation after adding text so the text appears on top
    xAxis.tickFormat(d3.format(".2f"));
    yAxis.tickFormat(d3.format(".2f"));
    xaxis.call(xAxis);
    yaxis.call(yAxis);

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
        .data(alldata)
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

// Function to update chart when new x or y axis variable selected
function updateScattergram() {
    // Get selected elements
    getSelectedAxisOptions();

    // Get existing elements
    var dots = svg.selectAll(".dot");
    dots
        .attr("cx", xMap)
        .attr("cy", yMap);

    // New elements
    var dotEnter = dots.data(alldata).enter();
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

// Function which creates the x and y axis labels
function createAxisLabels() {
    xaxislabel = xaxis.append("text")
                    .attr("class", "axislabel")
                    .attr("x", width / 2)
                    .attr("y", margin.bottom * 0.7)
                    .text(xLabelTxt);

    yaxislabel = yaxis.append("text")
                    .attr("class", "axislabel")
                    .attr("transform", "rotate(-90)")
                    .attr("x", -height / 2)
                    .attr("y", -margin.left * 0.7)
                    .text(yLabelTxt);
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

        if (userView == "loadProfiles") {   // If viewing load profiles update chart to display and tabulate key facts
            kf.style("visibility", "");	    // Unhide description

            chart
		        .attr("src", d.Example)
		        .style("visibility", "");

            tabulateKeyFacts(d, 7);
        } else if (userView == "stats") {   // If viewing stats then highlight relevant parts of charts which relate to dot
            // Highlight stats charts if this view selected
            for (var i = 0; i < statCharts.length; i++) {
                var statChartsDiv = d3.select("#stats" + statCharts[i]);
                var svg = statChartsDiv.select("svg").select("g");

                var path = svg.selectAll("path");

                var filt = d[statCharts[i]];

                path.attr("opacity", 0.1);

                path.filter(function (d) { return d.data.name == filt; }).attr("opacity", 1);
            }
        }
    }
};

// Function to reset page when cursor moved away from circle
function mouseleave(d) {
    if (freezeMouseover == 0) {
        // Bring all circles back to full opacity
        allDots.attr("opacity", 1);

        if (userView == "loadProfiles") {   // If viewing load profiles update chart to display and tabulate key facts
            // Hide the stuff on the right panes
            kf.style("visibility", "hidden");		// Hide key facts
            chart.style("visibility", "hidden");	// Hide chart
        } else if (userView == "stats") {   // If viewing stats then highlight relevant parts of charts which relate to dot
            for (var i = 0; i < statCharts.length; i++) {
                var statChartsDiv = d3.select("#stats" + statCharts[i]);
                var svg = statChartsDiv.select("svg").select("g");

                var path = svg.selectAll("path");

                path.attr("opacity", 1);
            }
        }
    };
};

// Function to freeze mouseover text
function click(d) {
    // Change value of freezeMouseover variable
    freezeMouseover = (freezeMouseover + 1) % 2;
};

// Function to select all dots so we don't need to do this every mouseover
function selectDots() {
    allDots = d3.selectAll(".dot");
}

// Take key facts and display them
function tabulateKeyFacts(data, nrow) {
    kf.selectAll("div").remove();
    kf.selectAll("table").remove();
    var title = "Key Facts About Highlighted Hire";
    var attrkf = { h: 14, w: 290 };
    var ncol = Math.ceil(data.KeyFacts.length / nrow);

    kf.append("div")
		.text(title)
		.style("font-weight", "bold")
		.attr("position", "absolute")
		.attr("height", attrkf.h)
		.attr("width", 900)
		.attr("top", 0)
		.attr("left", 0);

    var table = kf.append("table")
					.attr("width", attrkf.w * ncol)
					.attr("height", 20 * nrow);

    for (var i = 0; i < (Math.min(data.KeyFacts.length, nrow)) ; i++) {
        row = table
			.append("tr");

        for (var j = 0; j < ncol; j++) {
            var idx = i + j * nrow;
            if (idx < data.KeyFacts.length) {
                row
					.append("td")
					.text(data.KeyFacts[idx])
            }
        }
    }
};

// Function to zoom axis
function zoom(begin, end, whichAxis) {
    // Get transition element
    //var t = svg.transition().duration(0);

    // Calculate new tick values for axis
    var rng = end - begin;
    var step = rng / 10;
    var ticks = [];
    for (var i = 0; i <= 10; i++) {
        ticks.push(begin + step * i);
    }

    // Change scale domain and assign tick values calculated above
    if (whichAxis == "x") {
        //xScale.domain([begin - 0.01, end + 0.01]);
        xScale.domain([(-0.01 / 1.02 * rng) + begin, end + (0.01 / 1.02 * rng)]);
        xAxis.tickValues(ticks);
        xaxis.call(xAxis);
        allDots.attr("cx", xMap);
    }
    else if (whichAxis == "y") {
        //yScale.domain([begin - 0.01, end + 0.01]);
        yScale.domain([(-0.01 / 1.02 * rng) + begin, end + (0.01 / 1.02 * rng)]);
        yAxis.tickValues(ticks);
        yaxis.call(yAxis);
        allDots.attr("cy", yMap);
    }
}

// Function when a new tab selected
function changeView(evt, displayType) {
    // Hide all tab content divs (this also means they do not take up any space in the DOM)
    d3.selectAll(".tabcontent").style("display", "none");

    // Remove active from class of previously selected elements
    d3.selectAll(".tablinks").attr("class", "tablinks");

    // Display the correct block
    d3.select("#" + displayType).style("display", "block");

    // Activate currently selected element
    evt.currentTarget.className += " active";

    // Update stored value of user view
    userView = displayType;
}

// Summarise data for statistics plotting
function summariseData(obj) {
    // Create dictionary of key values
    var tmp = {};
    for (var i = 0; i < statCharts.length; i++) {
        tmp[statCharts[i]] = {};
        obj[statCharts[i]] = [];
    }

    alldata.forEach(function (d) {
        if (d[xLabel] >= xMin && d[xLabel] <= xMax && d[yLabel] >= yMin && d[yLabel] <= yMax) {
            for (var i = 0; i < statCharts.length; i++) {
                if (typeof (tmp[statCharts[i]][d[statCharts[i]]]) == "undefined") {
                    tmp[statCharts[i]][d[statCharts[i]]] = { "count": 0, "valueUSD": 0.00, "hireDays": 0 };
                }

                tmp[statCharts[i]][d[statCharts[i]]]["count"] += 1;
                tmp[statCharts[i]][d[statCharts[i]]]["valueUSD"] += d.Value_USD;
                tmp[statCharts[i]][d[statCharts[i]]]["hireDays"] += d.HireDuration_days;
            }
        }
    });

    // Convert key value pair into array
    for (var c in tmp) {    // This is c11, c12, etc
        for (var k in tmp[c]) {  // This is Generator, Generator Gas, etc
            var o = {};

            o["name"] = k;
            o["count"] = tmp[c][k]["count"];
            o["valueUSD"] = tmp[c][k]["valueUSD"];
            o["hireDays"] = tmp[c][k]["hireDays"];

            obj[c].push(o);
        }

        // Get unique colours for each item
        colors = generateColours(obj[c], "name");
    }

    return obj;
}

// Function to create statistics charts
function createStatsCharts() {
    // Create SVG element inside div
    for (var i = 0; i < statCharts.length; i++) {
        var statChartsDiv = d3.select("#stats" + statCharts[i]);
        
        statChartsDiv
                    .append("svg")
	                .attr("width", statsWidth)
	                .attr("height", statsHeight)
                    .attr("id", "svg" + statCharts[i])
                    .append("g")
                    .attr("transform", "translate(" + statsWidth / 2 + "," + statsHeight / 2 + ")");

        statChartsDiv
                    .append("div")
                    .attr("class", "donutTooltip")
                    .attr("id", "donutTooltip" + statCharts[i]);
    }

    updateStatsCharts();
}

// Function to find key for matching with existing data when new data added/removed
function key(d) {
    return d.data.name;
}

// Function to update existing charts
function updateStatsCharts() {
    pie.value(function (d) { return d[statsMeasure]; });    // Rebind pie value accessor outside of for loop as it is the same for all charts

    for (var i = 0; i < statCharts.length; i++) {
        var statChartsDiv = d3.select("#stats" + statCharts[i]);
        var svg = statChartsDiv.select("svg").select("g");

        var path = svg.selectAll("path");        

        var data0 = path.data(),
            data1 = pie(statdata[statCharts[i]]);

        var totalDonutSize = 0;
        for (var j = 0; j < data1.length; j++) {
            totalDonutSize += data1[j].data[statsMeasure];
        }

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
            //.attr("id", function (d) { return "p" + d.data.name.replace(/ /g, ""); })
            .merge(path)
            .transition()
            .duration(myDuration)
            .attrTween("d", arcTween);
         
        svg.selectAll("path")
            .on("mousemove", function (d) {
                var donutName = this.parentNode.parentNode.id;
                donutName = donutName.substring(3, donutName.length);
                var ttDiv = d3.select("#donutTooltip" + donutName);
                var mousePos = d3.mouse(this.parentNode);
                ttDiv.style("left", mousePos[0] + 10 + (statsWidth / 2) + "px");
                ttDiv.style("top", mousePos[1] - 25 + (statsHeight / 2) + "px");
                ttDiv.style("display", "inline-block");

                var displayVal = d.data[statsMeasure];
                if (statsMeasure == "valueUSD") {
                    displayVal = "$" + d3.format(",.2f")(displayVal);
                }

                ttDiv.html(d.data.name + ": " + displayVal + " (" + d3.format(".1f")(100 * d.data[statsMeasure] / totalDonutSize) + "%)");
            })
            .on("mouseout", function (d) {
                var donutName = this.parentNode.parentNode.id;
                donutName = donutName.substring(3, donutName.length);
                var ttDiv = d3.select("#donutTooltip" + donutName);

                ttDiv.style("display", "none");
            });

        // Get top 5 entries for legend and decide how to centralise them
        var top5SortedData = data1.sort(function (a, b) { return b.data[statsMeasure] - a.data[statsMeasure] });
        var maxElements = Math.min(5, top5SortedData.length);
        top5SortedData = top5SortedData.slice(0, maxElements);
        var maxLength = 0;
        for (var j = 0; j < maxElements; j++) {
            top5SortedData[j].data.name2 = top5SortedData[j].data.name.substring(0, 22);

            maxLength = Math.max(maxLength, top5SortedData[j].data.name2.length);
        }

        // Update legend
        var legend = svg.selectAll('.legend11').data(top5SortedData, key);

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
            .style('fill', function (d) {
                return colors[d.data.name];
            });

        legendenter.append('text')
            .attr('x', leg.rectSize + leg.rectSpacing)
            .attr('y', "8px")
            .style("font-size", leg.rectTextSize)
            .text(function (d) { return d.data.name2; });

        // Update existing elements
        /*legend.attr('transform', function (d, i) {
            var height = leg.rectSize + leg.rectSpacing;
            var offset = height * top5SortedData.length / 2;
            var horz = -(maxLength * 2 + height);
            var vert = i * height - offset;
            return "translate(" + horz + "," + vert + ")";
        });*/
    }
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

// Function to calculate and visualise summary statistics
function calculateStats() {
    // Get summary statistics
    statdata = summariseData(statdata);

    if (firstStats == 1) {
        firstStats = 0;
        createStatsCharts();
    }
    else {
        updateStatsCharts();
    }

    caclStatsButton.attr("disabled", true);
}

// Function which is called when radio button changed
function optionChange() {
    statsMeasure = $('input[name="measureSelectorRadio"]:checked').val();

    updateStatsCharts();
}