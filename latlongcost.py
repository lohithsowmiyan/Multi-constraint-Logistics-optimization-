import pandas as pd
import math
from geopy import distance
from opencage.geocoder import OpenCageGeocode
from math import sin, cos, sqrt, atan2, radians
key = 'da60a256c5cf4429bbedd8cda0cf7929'  # get api key from:  https://opencagedata.com

def get_location(location):
    geocoder = OpenCageGeocode(key)
    # query = 'Singapore port'  
    results = geocoder.geocode(location)
    results =results[0]
    lat = results['geometry']['lat']
    lng = results['geometry']['lng']
    # print(results)
    # print (lat,lng)
    return (lat,lng)

def find_distance(lat1,long1,lat2,long2):
    # x1 = lat1/57.29577951
    # y1 = long1/57.29577951
    # x2 = lat2/57.29577951
    # y2 = long2/57.29577951
    # distance = math.sqrt((x1-x2)**2 + (y1-y2)**2)
    # return distance



    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(long1)
    lat2 = radians(lat2)
    lon2 = radians(long2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def find_closest(src):
   (lat,long) = get_location(src)
   data = pd.read_excel('latlong.xlsx')
   min_dis = 100000
   temp = ""
   min_index=0
   for i in range(len(data)):
    distance = find_distance(lat,long,data.iloc[i]['Latitude'],data.iloc[i]['Longitude'])
    if distance < min_dis:
        min_dis = round(distance,2)
        temp=data.loc[i,'City']
        min_index=i

   #return {"City":temp,"distance":min_dis,"SrcLat":lat,"SrcLong":long,"DestLat":data.iloc[min_index]['Latitude'],"DestLong":data.iloc[min_index]['Longitude']}
   return temp
     

