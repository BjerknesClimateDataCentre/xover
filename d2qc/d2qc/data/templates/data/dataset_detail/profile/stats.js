// Plot stats
var xtype_title = 'Depth'
var data = []
var mean = {
  x: stats.mean,
  y: stats.y,
  mode: 'markers',
  type: 'scatter',
  marker: {
    color: blue_profile
  },
  name: 'Mean'
};

var stdev_plus = {
  x: stats.mean.map(function (v, i) {return stats.stdev[i] == null ? null : v + stats.stdev[i]}),
  y: stats.y,
  mode: 'lines',
  type: 'scatter',
  line: {
    color: blue_profile
  },
  name: '&#177;  St. dev'
};
var stdev_min = {
  x: stats.mean.map(function (v, i) {return stats.stdev[i] == null ? null : v - stats.stdev[i]}),
  y: stats.y,
  mode: 'lines',
  type: 'scatter',
  line: {
    color: blue_profile
  },
  showlegend: false,
  name: '&#177;  St. dev'
};
var w_mean = {
  x: [stats.w_mean, stats.w_mean],
  y: [Math.min(...stats.y), Math.max(...stats.y)],
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile
  },
  name: 'Weighted mean ' + stats.w_mean.toPrecision(4)
};
var w_std_plus = {
  x: [stats.w_mean + stats.w_stdev, stats.w_mean + stats.w_stdev],
  y: [Math.min(...stats.y), Math.max(...stats.y)],
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  name: 'Weighted st. dev &#177;' + stats.w_stdev.toPrecision(4)
};
var w_std_min = {
  x: [stats.w_mean - stats.w_stdev, stats.w_mean - stats.w_stdev],
  y: [Math.min(...stats.y), Math.max(...stats.y)],
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  name: 'Weighted st. dev',
  showlegend: false
};


var data = [
  mean,
  stdev_plus,
  stdev_min,
  w_mean,
  w_std_plus,
  w_std_min
];
title = "Weighted mean diff."
title += "<br>{{ parameter.name }}"
title += "<br>{{ object.expocode }} vs. {{ crossover_expocode }}"
var layout = {
  yaxis: {autorange: 'reversed',title: {text:xtype_title}},
  margin: {l: 60, r:0},
  legend: {orientation: 'h'},
  hovermode: 'y',
  title: title
};

Plotly.newPlot('stats', data, layout);
