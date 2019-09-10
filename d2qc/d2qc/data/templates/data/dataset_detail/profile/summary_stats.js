var summary_stats = JSON.parse('{{ summary_stats | escapejs }}');
w_mean = {
  x: summary_stats.date,
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
  x: summary_stats.date,
  y: summary_stats.mean,
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
stdev = {
  x: summary_stats.date,
  y: summary_stats.mean.map(function(x, i){return x + summary_stats.stdev[i];}),
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  name: 'Stdev &#177;' + summary_stats.stdev[0].toPrecision(4),
  hoverinfo: 'skip'
};
stdev2 = {
  x: summary_stats.date,
  y: summary_stats.mean.map(function(x, i){return x - summary_stats.stdev[i];}),
  mode: 'lines',
  type: 'scatter',
  line: {
    color: red_profile,
    dash: 'dot'
  },
  showlegend: false,
  hoverinfo: 'skip'
};

data = [
  w_mean,
  mean,
  stdev,
  stdev2
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
