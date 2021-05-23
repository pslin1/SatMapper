import ephem
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
    # one approach is to use pandas json functionality:
    elevation = pd.json_normalize(r, 'results')['elevation'].values[0]
    return elevation

def make_observer(lat, long, elev):
    obs = ephem.Observer()
    obs.lat = '60.721188'
    obs.lon = '-135.056839'
    obs.elevation = elev
    #print(obs.lat, obs.long, obs.elev)
    obs.date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    return obs

def calculate_visible(obs, map):
    df = pd.read_csv('active.txt', delimiter = "\n", header= None)

    #Reshape dataframe into three column dataframe
    #Is there a better way to do this? Instead of reading in as a dataframe then reshaping, can we read it in a 3 column data frame?
    #https://stackoverflow.com/questions/39761366/transpose-the-data-in-a-column-every-nth-rows-in-pandas
    #Credit: jezrael (https://stackoverflow.com/users/2901002/jezrael)
    new_df = pd.DataFrame(np.reshape(df.values,(int(df.shape[0] / 3),3)),columns=['Name','Line 1','Line 2'])

    #count_int = 0

    #Parse TLE data
    for index, row in new_df.iterrows():
        tle_rec = ephem.readtle(row['Name'], row['Line 1'], row['Line 2'])
        tle_rec.compute(obs)
        #print(tle_rec.sublat / ephem.degree, tle_rec.sublong, tle_rec.elevation)
        if tle_rec.alt > 0:
            coords = [tle_rec.sublat / ephem.degree, tle_rec.sublong / ephem.degree]
        #print(tle_rec.alt)
        #count_int += 1
        #print(tle_rec.name)
            folium.Marker(coords, popup = tle_rec.name).add_to(map)

    #print(count_int)


def generate_map(latlng):
    #Get user lat long via IP address
    myloc = geocoder.ip('me')

    map = folium.Map(location = latlng, zoom_start = 13)

    return map

@app.route('/')
def index():

    #Create single column dataframe from csv of TLE
    #df = pd.read_csv('active.txt', delimiter = "\n", header= None)

    #Reshape dataframe into three column dataframe
    #Is there a better way to do this? Instead of reading in as a dataframe then reshaping, can we read it in a 3 column data frame?
    #https://stackoverflow.com/questions/39761366/transpose-the-data-in-a-column-every-nth-rows-in-pandas
    #Credit: jezrael (https://stackoverflow.com/users/2901002/jezrael)
    #new_df = pd.DataFrame(np.reshape(df.values,(int(df.shape[0] / 3),3)),columns=['Name','Line 1','Line 2'])

    #Parse TLE data
    #for index, row in new_df.iterrows():
        #tle_rec = ephem.readtle(row['Name'], row['Line 1'], row['Line 2'])
        #tle_rec.compute()
        #print(tle_rec.sublong, tle_rec.sublat, tle_rec.elevation)

    # This is an example of how to use ephem.readtle
    # name = "ISS (ZARYA)";
    # line1 = "1 25544U 98067A   21040.93620630  .00000791  00000-0  22545-4 0  9995"
    # line2 = "2 25544  51.6439 252.1222 0002708 354.7355  81.9453 15.48944724268874"
    #
    # tle_rec = ephem.readtle(name, line1, line2)
    # tle_rec.compute()
    #
    # print(tle_rec.sublong, tle_rec.sublat, tle_rec.elevation)

    #Check iscircumpolar as well as next_pass
    #look at .alt property of an object?

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

        latlng = [latitude, longitude]

        map = generate_map(latlng)

        #elevation = get_elevation(latitude, longitude)
        #elevation=0

        obs = make_observer(latitude, longitude, elevation)

        #DO TLE CALCULATION HERE
        calculate_visible(obs, map)


        return map._repr_html_()

    return render_template('index.html')

# if __name__ == '__main__':
#     main()
