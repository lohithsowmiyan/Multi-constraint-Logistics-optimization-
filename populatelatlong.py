import pandas as pd
model = pd.read_excel('model data-4.xlsx')
latlong = pd.read_excel('latlong.xlsx')

srclat = []
srclong = []
deslat = []
deslong = []
#{'Shangai International Airport, China': (31.141345, 121.8046366), 'Hong Kong International airport, Hong Kong': (22.3125986, 113.9173238), 'Louisville International Airport, USA': (38.1866987, -85.7414172), 'Boston International Airport, USA': (37.097997, -94.460264), 'Sharjah International Airport, UAE': (25.3401476, 55.5137442), 'Felixstone International Airport, UK': (54.75844, -2.69531), 'Delhi Air Cargo, Delhi': (28.65381, 77.22897), 'Bombay International Airport, India': (22.0, 79.0), 'Nhava Sheva Sea Port, India': (22.0, 79.0), 'Mundra Sea Port, India': (22.0, 79.0), 'Chennai Port, India': (13.0964425, 80.3036316), 'Kolkata Sea Port, India': (22.0, 79.0), 'Shangai Port, China': (31.141345, 121.8046366), 'Shenzen Port, China': (35.0, 105.0), 'New York Sea Port, US': (30.838366, -87.205314), 'Los Angeles Sea Port, US': (34.047863, -118.245353), 'Jebel Ali Port, UAE': (24.9804578, 55.0598883), 'Port Zayed, UAE': (24.5231134, 54.3737411), 'Immingham, UK': (53.6159963, -0.2136727), 'Southampton Port, UK': (50.8870044, -1.3944361), 'Bangalore Railway Station': (13.280475, 77.5516397), 'Bangalore Warehouse': (12.9516005, 77.5953398), 'Louisville Railway Station': (47.27103, 8.8218), 'Boston Railway Station': (52.9758976, -0.1107757), 'New York Railway Station': (40.8796602, -73.5625424), 'Los Angeles Railway Station': (47.27103, 8.8218), 'Chennai Railway Station': (13.0054225, 80.2477977), 'Kolkata Railway Station': (22.5551465, 88.2605445), 'Mundra Railway Station': (47.27103, 8.8218), 'Mumbai Railway Station': (19.1648029, 72.8500454), 'Delhi Railway Station': (28.736827, 76.8596791), 'Louisville Warehouse': (38.2622602, -85.7765678)}
for i in range(len(model)):
    
    srclat.append(float(latlong.loc[latlong['City']==model.iloc[i]['Source']]['Latitude'].values))
    srclong.append(float(latlong.loc[latlong['City']==model.iloc[i]['Source']]['Longitude'].values))
    deslat.append(float(latlong.loc[latlong['City']==model.iloc[i]['Destination']]['Latitude'].values))
    deslong.append(float(latlong.loc[latlong['City']==model.iloc[i]['Destination']]['Longitude'].values))

model['SrcLat'] = srclat
model['SrcLong'] = srclong
model['DesLat'] = deslat
model['DesLong'] = deslong

print(model.head(20))

model.to_excel('data-set.xlsx')
