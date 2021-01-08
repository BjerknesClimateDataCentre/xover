// Plots summary stats
var summary_stats = JSON.parse('{{ summary_stats | escapejs }}');
w_mean = {
  x: summary_stats.date.map(date => new Date(date)),
  y: summary_stats.w_mean,
  text: summary_stats.expocode,
  textposition: 'top',
  error_y: {
    type: 'data',
    array: summary_stats.w_stdev,
    visible: true
  },
  mode: 'markers+text',
  type: 'scatter',
  line: {
    color: 'black'
  },
  hoverinfo: 'text',
  textposition: 'top right',
  name: 'Weighted mean &plusmn; st. dev'
};
mean = {
  x: [...summary_stats.date, new Date(summary_stats.eval_dataset_date)],
  y: [...summary_stats.mean, summary_stats.mean[0]],
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile
  },
  name: 'Weighted mean ' + summary_stats.mean[0].toPrecision(4),
  hoverinfo: 'text',
  hovertext:
    'Mean ' + summary_stats.mean[0].toPrecision(4) + '<br>'
      + 'Stdev &plusmn;' + summary_stats.stdev[0].toPrecision(4)
};
stdev_arr = [
  ...summary_stats.mean.map(
    function(x, i){return x + summary_stats.stdev[i];}
  ),
  summary_stats.mean[0] + summary_stats.stdev[0]
]
stdev = {
  x: [...summary_stats.date, new Date(summary_stats.eval_dataset_date)],
  y: stdev_arr,
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  name: 'Stdev &#177;' + summary_stats.stdev[0].toPrecision(4),
  hoverinfo: 'skip'
};
stdev2_arr = [
  ...summary_stats.mean.map(
    function(x, i){return x - summary_stats.stdev[i];}
  ),
  summary_stats.mean[0] - summary_stats.stdev[0]
]
stdev2 = {
  x: [...summary_stats.date, new Date(summary_stats.eval_dataset_date)],
  y: stdev2_arr,
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  showlegend: false,
  hoverinfo: 'skip'
};
dataset = {
  x: [new Date(summary_stats.eval_dataset_date)],
  y: [summary_stats.mean[0]],
  mode: 'markers',
  type: 'scatter',
  marker: {
    symbol: 'line-ns',
    size: 2000,
    line: {
      color: blue_profile,
      width: 3
    }
  },
  name:  'Date for data set {{ object.expocode }}',
  hoverinfo: 'skip'
};


data = [
  w_mean,
  mean,
  stdev,
  stdev2,
  dataset
]

title = 'Mean and stdev offsets for {{ object.expocode }} and matching '
title += 'reference cruises'
layout = {
    yaxis: {title: {text:'Offset'}},
    margin: {l: 60, r:0},
    legend: {orientation: 'h'},
    hovermode: 'x',
    title: title
};

Plotly.newPlot('summary-stats', data, layout);
