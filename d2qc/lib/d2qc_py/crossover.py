from math import radians, cos, sin, asin, sqrt
#from pylab import savefig
import matplotlib.pyplot as plt

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
import os.path
import d2qc.data as data
from PIL import Image

def crossover(data = None, refdata = None):
    """
    Performs crossover analysis on hydrographic data.

    Input data is in the form provided by the get_data_set_data - function
    (The original matlab-function is called sec_QC)
    """
    pass

def get_haversine_distance(lat1, lon1, lat2, lon2):
    """
        Get the distance between two points. Input in decimal degrees. Output in
        metres.
    """

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in meters is 6 371 000m
    m = 6371 * c * 1000
    return m

def plot_overview_map(dataset = [], refdata=[], center_lat=0, center_lon=0):
    """
    Plot matching reference-cruices together with the current cruise, to show
    how they match in space.
    """
    for ix,name in enumerate(dataset[0]['data_columns']):
        if name == 'latitude':
            latix = ix
        elif name == 'longitude':
            lonix = ix

    map = Basemap(projection='ortho', lat_0=center_lat, lon_0=center_lon,
            resolution='c')
    map.drawcoastlines(linewidth=0.25)
    map.drawcountries(linewidth=0.25)
    map.fillcontinents(color='coral',lake_color='aqua')
    # draw the edge of the map projection region (the projection limb)
    map.drawmapboundary(fill_color='aqua')
    # draw lat/lon grid lines every 30 degrees.
    map.drawmeridians(np.arange(0,360,30))
    map.drawparallels(np.arange(-90,90,30))

    path = os.path.dirname(data.__file__)
    links = {}
    plots = []
    cnt = 0
    for ref_dataset in refdata:
        expocode = ref_dataset['expocode']
        ref_lat = None
        ref_lon = None
        lat = None
        lon = None
        for ref in ref_dataset['data_points']:
            if ref_lat != ref[latix] and ref_lon != ref[lonix]:
                plots.append(map.plot(ref[lonix], ref[latix], latlon=True, color='red', marker='o',
                        linestyle='', markerfacecolor='none'))
            ref_lat = ref[latix]
            ref_lon = ref[lonix]
        for row in dataset[0]['data_points']:
            if lat != row[latix] and lon != row[lonix]:
                plots.append(map.plot(row[lonix], row[latix], latlon=True, color='blue', marker='o',
                        linestyle='', markerfacecolor='none'))
            lat = row[latix]
            lon = row[lonix]

        # Save the map
        link = '/static/data/plots/' + expocode + '_overview.png'
        plt.savefig(path + link, bbox_inches='tight', dpi=150)
        links[expocode] = link
        for p in plots:
            p[0].remove()
        plots = []
        cnt += 1
        if cnt>8:
            break

    plt.close('all')
    return links


def plot_bounds_map(bounds, dataset = [], refdata=[], limit=222000):
    """
    Plot reference cruise data points within the limit (222km) with the current
    cruise, to show details of how they match in space.
    """
    if not bounds:
        return

    for ix,name in enumerate(dataset[0]['data_columns']):
        if name == 'latitude':
            latix = ix
        elif name == 'longitude':
            lonix = ix

    center_lat = (bounds[0] + bounds[1]) / 2
    center_lon = (bounds[2] + bounds[3]) / 2
    map = Basemap(llcrnrlon=bounds[2],llcrnrlat=bounds[0],
            urcrnrlon=bounds[3],urcrnrlat=bounds[1],
            projection='merc', lat_0=center_lat,
            lon_0=center_lon, resolution='i')
    map.drawcoastlines(linewidth=0.25)
    map.drawcountries(linewidth=0.25)
    map.fillcontinents(color='coral',lake_color='aqua')
    # draw the edge of the map projection region (the projection limb)
    map.drawmapboundary(fill_color='aqua')
    # draw lat/lon grid lines every 30 degrees.
    #map.drawmeridians(np.arange(0,360,30))
    #map.drawparallels(np.arange(-90,90,30))
    path = os.path.dirname(data.__file__)
    links = {}
    plots = []
    positions =  [];
    lat = None
    lon = None
    for row in dataset[0]['data_points']:
        if lat != row[latix] and lon != row[lonix]:
            positions.append((row[lonix], row[latix]))
        lat = row[latix]
        lon = row[lonix]

    cnt = 0
    for ref_dataset in refdata:
        expocode = ref_dataset['expocode']
        ref_lat = None
        ref_lon = None
        lat = None
        lon = None
        for ref in ref_dataset['data_points']:
            if ref_lat != ref[latix] and ref_lon != ref[lonix]:
                for p in positions:
                    dist = get_haversine_distance(p[1], p[0], ref[latix], ref[lonix])
                    if dist < limit:
                        plots.append(map.plot(
                                float(ref[lonix]),
                                float(ref[latix]),
                                latlon=True,
                                color='red',
                                marker='o',
                                linestyle='',
                                markerfacecolor='none'
                        ))
                        break
            ref_lat = ref[latix]
            ref_lon = ref[lonix]
        for p in positions:
            plots.append(map.plot(
                    float(p[0]),
                    float(p[1]),
                    latlon=True,
                    color='blue',
                    marker='o',
                    linestyle='',
                    markerfacecolor='none'
            ))

        # Save the map
        link = '/static/data/plots/' + expocode + '_bounds.png'
        plt.savefig(path + link, bbox_inches='tight', dpi=150)
        links[expocode] = link
        for p in plots:
            p[0].remove()
        plots = []
        cnt += 1
        if cnt>8:
            break

    plt.close('all')
    return links

def merge_images(file1, file2, savepath):
    """Merge two images into one, displayed side by side
    :param file1: path to first image file
    :param file2: path to second image file
    :return: the merged Image object
    """
    image1 = Image.open(file1)
    image2 = Image.open(file2)

    (width1, height1) = image1.size
    (width2, height2) = image2.size

    result_width = width1 + width2
    result_height = max(height1, height2)

    result = Image.new('RGB', (result_width, result_height))
    result.paste(im=image1, box=(0, 0))
    result.paste(im=image2, box=(width1, 0))
    result.save(savepath)
