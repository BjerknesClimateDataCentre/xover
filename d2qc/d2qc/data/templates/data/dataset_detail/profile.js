// Profiles:
var data = [];
var profiles = [];
var interp_profiles = [];
var profiles_ref = [];
var interp_profiles_ref = [];
var stats = false;

// Profiles dataset
{% if dataset_profiles %}
  var profiles = JSON.parse('{{ dataset_profiles | escapejs }}');
{% endif %}
{% if dataset_interp_profiles %}
  var interp_profiles = JSON.parse('{{ dataset_interp_profiles | escapejs }}');
{% endif %}

// Reference dataset
{% if dataset_ref_profiles %}
  var profiles_ref = JSON.parse('{{ dataset_ref_profiles | escapejs }}');
{% endif %}
{% if dataset_ref_interp_profiles %}
  var interp_profiles_ref = JSON.parse('{{ dataset_ref_interp_profiles | escapejs }}');
{% endif %}

// Stats
{% if dataset_stats %}
  stats = JSON.parse('{{ dataset_stats | escapejs }}');
{% endif %}

var current_dataset = 0;
var data_set_id = parseInt('{{ object.id }}')


for (var i=0; i<interp_profiles.length; i++) {
  var showlegend = false
  if (i == 0) {
    showlegend = true
  }
  profile = createProfile(
    interp_profiles[i],
    blue_profile,
    showlegend,
    true
  )
  if(profile) {
    data.push(profile)
  }
}

// Min and max values for the plotting parameter
var param_max = Number.MIN_VALUE
var param_min = Number.MAX_VALUE

function max_reduce(max, x){
  retval = x
  if (null == x) {
    retval = max
  }
  else if (null != max) {
    retval = Math.max(max, x)
  }
  return retval
}

function min_reduce(min, x){
  retval = x
  if (null == x) {
    retval = min
  }
  else if (null != min) {
    retval = Math.min(min, x)
  }
  return retval
}

for (var i=0; i<profiles.length; i++) {
  profile = createProfile(profiles[i], blue_profile, false, false)
  if(profile) {
    data.push(profile)
    param_max = Math.max(param_max, profiles[i].param.data.reduce(max_reduce))
    param_min = Math.min(param_min, profiles[i].param.data.reduce(min_reduce))
  }
}
for (var i=0; i<profiles_ref.length; i++) {
  profile = createProfile(profiles_ref[i], red_profile, false, false)
  if(profile) {
    data.push(profile)
    param_max = Math.max(param_max, profiles_ref[i].param.data.reduce(max_reduce))
    param_min = Math.min(param_min, profiles_ref[i].param.data.reduce(min_reduce))
  }
}
for (var i=0; i<interp_profiles_ref.length; i++) {
  var showlegend = false
  if (i == 0) {
    showlegend = true
  }
  profile = createProfile(interp_profiles_ref[i], red_profile, showlegend, true)
  if(profile) {
    data.push(profile)
  }
}

// Check stats are not empty
if (stats) {
  // Indicate where statistics are valid
  min_stat = Math.min(...stats.y)
  max_stat = Math.max(...stats.y)
  diff_stat = max_stat-min_stat
  diff_param = param_max - param_min
  var stats_limits = {
    x: [
      param_min,
      param_max,
      param_max,
      param_max + diff_param / 14,
    ],
    y: [
      min_stat,
      min_stat,
      min_stat - diff_stat / 5,
      min_stat + diff_stat / 2,
    ],
    mode: 'lines',
    type: 'scatter',
    line: {
      color: bluetransp_profile,
    },
    marker: {
      color: bluetransp_profile,
    },
    showlegend: false
  }
  stats_fill = JSON.parse(JSON.stringify(stats_limits))
  stats_fill.y = [
    max_stat,
    max_stat,
    max_stat + diff_stat / 5,
    max_stat - diff_stat / 2,
  ]
  stats_fill.fill = 'tonexty'
  stats_fill.fillcolor = bluetransp_profile
  stats_fill.showlegend = true
  stats_fill.name = 'Matching crossover area'

  // Add these to the beginning of the data array
  data.unshift(stats_fill)
  data.unshift(stats_limits)
}
title = "Cruise profiles, parameter: {{ parameter.name }}"

var layout = {
  yaxis: {autorange: 'reversed',title: {text:'Sigma 4'}},
  xaxis: {title: {text:profiles[0].parameter}},
  margin: {l: 60, r:0},
  legend: {orientation: 'h'},
  hovermode: 'y',
  title: title
};
Plotly.newPlot('profiles', data, layout);
/* create a profile for the profile plot */
function createProfile(p, color, showlegend, line) {
  if (!('param' in p)) {
    return []
  }

  var profile = {
    x: Object.values(p.param.data),
    y: Object.values(p.sigma4.data),
    mode: 'markers',
    showlegend: showlegend,
    name: '',
    marker: {
      color: color,
      size: 3,
    },
  }
  if (line) {
    profile.mode = 'lines'
    profile.line = {
      color: color,
      width: 1,
    }
    profile.hoverinfo = 'skip'
  }
  if (showlegend) {
    profile.name = p.expocode
  }
  return profile
}

{% if dataset_stats %}
  {% include "./profile/stats.js"%}
{% endif %}
{% if summary_stats %}
  {% include "./profile/summary_stats.js"%}
{% endif %}
