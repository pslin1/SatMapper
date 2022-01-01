import ephem
from skyfield.api import load, EarthSatellite, wgs84
from datetime import datetime
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

def make_observer(lat, long, elev):
    obs = ephem.Observer()
    obs.lat = lat
    obs.lon = long
    obs.elevation = elev

    obs.date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    return obs

def calculate_visible(obs, map):
    df = pd.read_csv('active.txt', delimiter = "\n", header= None)

    #Reshape dataframe into three column dataframe
    #Is there a better way to do this? Instead of reading in as a dataframe then reshaping, can we read it in a 3 column data frame?
    #https://stackoverflow.com/questions/39761366/transpose-the-data-in-a-column-every-nth-rows-in-pandas
    #Credit: jezrael (https://stackoverflow.com/users/2901002/jezrael)
    new_df = pd.DataFrame(np.reshape(df.values,(int(df.shape[0] / 3),3)),columns=['Name','Line 1','Line 2'])

    #Parse TLE data
    for index, row in new_df.iterrows():
        tle_rec = ephem.readtle(row['Name'], row['Line 1'], row['Line 2'])
        #Perform TLE computations given some observer object
        tle_rec.compute(obs)

        #if altitude over local horizon > 0
        try:
            if tle_rec.name == "ISS (ZARYA)":
                print(tle_rec.sublat / ephem.degree)
                print(tle_rec.sublong / ephem.degree)
                print(tle_rec.alt)
            if tle_rec.alt > 0:
                coords = [tle_rec.sublat / ephem.degree, tle_rec.sublong / ephem.degree]

                folium.Marker(coords, popup = tle_rec.name).add_to(map)

        except:
            pass



def generate_map(latlng):
    #Get user lat long via IP address
    myloc = geocoder.ip('me')

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

        ts = load.timescale()
        t = ts.now()

        #This loads the satellites in
        #satellites_url = "https://celestrak.com/NORAD/elements/active.txt"
        #satellites = load.tle_file(satellites_url)
        #print(satellites)
        #print('Loaded', len(satellites), 'satellites')

        #This is an example with the ISS
        n = 25544
        url = 'https://celestrak.com/satcat/tle.php?CATNR={}'.format(n)
        filename = 'tle-CATNR-{}.txt'.format(n)
        satellites = load.tle_file(url, filename=filename)
        print(satellites)

        #set current location, calculate difference and calculate difference from topocentric (at surface)
        current_loc = wgs84.latlon(latitude, longitude)
        difference = satellites[0] - current_loc
        topocentric = difference.at(t)

        alt, az, distance = topocentric.altaz()

        if alt.degrees > 0:
            print('The ISS is above the horizon')

        print('Altitude:', alt)
        print('Azimuth:', az)
        print('Distance: {:.1f} km'.format(distance.km))

        #calculateposition relative to center of earth and get lat long
        geocentric = satellites[0].at(t)
        lat, lon = wgs84.latlon_of(geocentric)
        print('Latitude:', lat)
        print('Longitude:', lon)

        latlng = [latitude, longitude]

        map = generate_map(latlng)

        obs = make_observer(latitude, longitude, elevation)

        #TLE CALCULATION HERE
        calculate_visible(obs, map)


        return map._repr_html_()

    return render_template('index.html')

if __name__ == '__main__':
     app.run()
