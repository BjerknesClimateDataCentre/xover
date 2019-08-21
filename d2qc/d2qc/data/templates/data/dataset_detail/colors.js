red_map = new ol.style.Style({
  image: new ol.style.Circle({
    fill: new ol.style.Fill({
      color: [255,0,0,.4]
    }),
    radius: 3,
  })
});
blue_map = new ol.style.Style({
  image: new ol.style.Circle({
    fill: new ol.style.Fill({
      color: [0,0,255,1]
    }),
    radius: 3,
  })
});

blue_hole_map = new ol.style.Style({
  image: new ol.style.Circle({
    stroke: new ol.style.Stroke({
      color: [0,0,255,.8]
    }),
    radius: 3,
  })
});

blue_line_map = new ol.style.Style({
  stroke: new ol.style.Stroke({
    color: [0,0,255,1],
  })
});


var blue_profile = 'rgb(75,75,255)'
var bluetransp_profile = 'rgba(75,75,255, .1)'
var red_profile = 'rgb(255,75,75)'
