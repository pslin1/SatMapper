from skyfield.api import load, EarthSatellite, wgs84
import pandas as pd
import numpy as np
import requests

from flask import Flask, render_template, session, redirect, request

import folium
import geocoder

app = Flask(__name__)

def get_latlng():
    #Get user lat long via IP address
    myloc = geocoder.ip('me')

    return myloc.latlng

#https://stackoverflow.com/questions/19513212/can-i-get-the-altitude-with-geopy-in-python-with-longitude-latitude
#Credit: Iain D (https://stackoverflow.com/users/4486474/iain-d)
#Date: March 28, 2021
#This takes around 20ish seconds to run, if elevation not found, just returns 0
def get_elevation(lat, long):
    query = ('https://api.open-elevation.com/api/v1/lookup'f'?locations={lat},{long}')
    r = requests.get(query).json()  # json object, various ways you can extract value
    # extract elevation
    elevation = pd.json_normalize(r, 'results')['elevation'].values[0]
    return elevation

def calculate_visible(current_loc, map):
    ts = load.timescale()
    current_time = ts.now()
    #satellites_url = "https://celestrak.com/NORAD/elements/active.txt"
    satellites = load.tle_file('active.txt')

    for item in satellites:

        #calculate difference from topocentric (at surface) position to satellite
        difference = item - current_loc
        topocentric = difference.at(current_time)

        alt, az, distance = topocentric.altaz()
        if alt.degrees > 0:

            #calculate position relative to center of earth and get lat long
            geocentric = item.at(current_time)
            lat, lon = wgs84.latlon_of(geocentric)

            coords = [lat.degrees, lon.degrees]
            folium.Marker(coords, popup = item.name + "\n Altitude: " + str(alt) + '\n Distance: {:.1f} km'.format(distance.km)).add_to(map)

def generate_map(latlng):

    map = folium.Map(location = latlng, zoom_start = 13)

    return map

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/map', methods=['GET', 'POST'])
def show_map():

    #https://pythonise.com/series/learning-flask/flask-working-with-forms
    #Author: Julian Nash
    #Date: 2021-03-21
    if request.method == 'POST':

        req = request.form

        auto_latlng = get_latlng()

        #If blank, use values from geoIP
        if req.get("latitude") == '':
            latitude = auto_latlng[0]

        else:
            try:
                #try to turn input value into float
                latitude = float(req.get("latitude"))

                #valid values for latitude are between -90 and 90
                if latitude > 90.0 or latitude < -90.0:
                    return render_template('index.html')
            except:
                #return to main page if invalid input
                return render_template('index.html')

        #If blank, use values from geoIP
        if req.get("longitude") == '':
            longitude = auto_latlng[1]

        else:
            try:
                #try to turn input value into float
                longitude = float(req.get("longitude"))

                #valid values for longitude are between -180 and 180
                if longitude > 180.0 or longitude < -180.0:
                    return render_template('index.html')
            except:
                #return to main page if invalid input
                return render_template('index.html')

        #If blank, use values from geoIP
        if req.get("elevation") == '':
            elevation = get_elevation(latitude, longitude)

        else:
            try:
                #try to turn input value into float
                #allow any numeric values
                elevation = float(req.get("elevation"))

            except:
                #return to main page if invalid input
                return render_template('index.html')

        #set current location
        current_loc = wgs84.latlon(latitude, longitude, elevation)

        latlng = [latitude, longitude]

        map = generate_map(latlng)

        #TLE claculation
        calculate_visible(current_loc, map)


        return map._repr_html_()

    return render_template('index.html')

if __name__ == '__main__':
     app.run()
