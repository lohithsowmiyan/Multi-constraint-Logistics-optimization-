from opencage.geocoder import OpenCageGeocode
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



import pandas as pd
data = pd.read_excel('/Users/lohithsowmiyan/Downloads/multimodal-transportation-optimization/model data-4.xlsx')
sources = data['Source']
destination = data['Destination']
# print(sources,destination) 
locations = {}
for i in sources:
    if i not in locations:
        try:
            locations[i]=get_location(i)
            print("Completed at",i)
        except Exception as e:
            print('Error in location : ',i)
            print(str(e))
    
    
 
for i in destination:
    if i not in locations:
        try:
            locations[i]=get_location(i)
            print("Completed at i")
        except Exception as e:
            print('Error in location : ',i)
            print(str(e))
    
print(locations)



dataFrame = {
    'City':[],
    'Latitude':[],
    'Longitude':[]
}
for i in locations:
    dataFrame['City'].append(i)
    dataFrame['Latitude'].append(locations[i][0])
    dataFrame['Longitude'].append(locations[i][1])
# print(dataFrame)

locations_df = pd.DataFrame(dataFrame)
locations_df.to_excel('latlong.xlsx')
