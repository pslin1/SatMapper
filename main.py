import ephem
import datetime
import pandas as pd
import numpy as np

def main():

    df = pd.read_csv('active.txt', delimiter = "\n", header= None)

    #Is there a better way to do this? Instead of reading in as a dataframe then reshaping, can we do better?
    #https://stackoverflow.com/questions/39761366/transpose-the-data-in-a-column-every-nth-rows-in-pandas
    #Credit: jezrael (https://stackoverflow.com/users/2901002/jezrael)
    new_df = pd.DataFrame(np.reshape(df.values,(int(df.shape[0] / 3),3)),columns=['Name','Line 1','Line 2'])

    for index, row in new_df.iterrows():
        tle_rec = ephem.readtle(row['Name'], row['Line 1'], row['Line 2'])
        tle_rec.compute()
        print(tle_rec.sublong, tle_rec.sublat, tle_rec.elevation)

    # This is an example of how to use ephem.readtle
    # name = "ISS (ZARYA)";
    # line1 = "1 25544U 98067A   21040.93620630  .00000791  00000-0  22545-4 0  9995"
    # line2 = "2 25544  51.6439 252.1222 0002708 354.7355  81.9453 15.48944724268874"
    #
    # tle_rec = ephem.readtle(name, line1, line2)
    # tle_rec.compute()
    #
    # print(tle_rec.sublong, tle_rec.sublat, tle_rec.elevation)


if __name__ == '__main__':
    main()
