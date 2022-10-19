from crypt import methods
from datetime import datetime
from datetime import timedelta
from functools import wraps
import pandas as pd
import json
import re
from textwrap import wrap
from urllib import request
import uuid
import mmt
import jwt
from flask import Flask,request,render_template,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.security import generate_password_hash, check_password_hash
from opencage.geocoder import OpenCageGeocode
from sqlalchemy import and_, or_, not_
key = 'da60a256c5cf4429bbedd8cda0cf7929'  # get api key from:  https://opencagedata.com
from multi_modal_transportation import find_shortest
from latlongcost import find_closest

#Fetches the latitude and longitude while adding a new route
def get_location(location):
    geocoder = OpenCageGeocode(key)
    # query = 'Singapore port'  
    results = geocoder.geocode(location)
    results =results[0]
    lat = results['geometry']['lat']
    lng = results['geometry']['lng']
    # print(results)
    # print (lat,lng)
    return lat,lng

def change_excel(src,des,carrier):
    data = pd.read_excel('model data_2.xlsx')
    temp_routes1 = data.loc[data['Source']==src]
    temp_routes2 = temp_routes1.loc[temp_routes1['Destination']==des]
    temp_routes1 = temp_routes2.loc[temp_routes2['Carrier']!=carrier]
    min_cost = 10e15
    min_index = 0
    for i in len(range(temp_routes1)):
        temp_cost = temp_routes1.iloc[i]['Fixed Freight'] + temp_routes1.iloc[i]['Port/Airport/Rail Handling Cost'] + temp_routes1.iloc[i]['Bunker/ Fuel Cost'] + temp_routes1.iloc[i]['Documentation Cost'] +  temp_routes1.iloc[i]['Equipment Cost'] +  temp_routes1.iloc[i]['Extra Cost'] 
        if temp_cost < min_cost:
            min_cost = temp_cost
            min_index = i
    return (temp_routes1.iloc[i]['Source'])
         


    


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///server.db'
app.config['SECRET_KEY']='secretkey'

db = SQLAlchemy(app)


#Consumer Database
class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    public_id = db.Column(db.String(50),unique=True)
    name = db.Column(db.String(30))
    password = db.Column(db.String(50))
    firm_name = db.Column(db.String(50))
    address = db.Column(db.String(100))
    email = db.Column(db.String(30))
    # orders = db.relationship("Orders", backref=backref("users", uselist=False))
    
    # admin = db.Column(db.Boolean)

    def __repr__(self):
        return '<Task %r>' % self.public_id

#Orders Database
class Orders(db.Model):
        order_id  = db.Column(db.Integer,primary_key=True)
        route_common_id = db.Column(db.String(20))
        public_id=db.Column(db.String(50)) #foreign key to User Database
        status=db.Column(db.String(30))
        route_number = db.Column(db.Integer)#foreign key to Routes
        Shipper_id = db.Column(db.Integer)
        # Transaction_cost = db.Column(db.Float)
        Source = db.Column(db.String(50))
        Destination = db.Column(db.String(50))
        Commodity = db.Column(db.String(50))
        Shipper_name = db.Column(db.String(50))

        # Volume = db.Column(db.String(50))
        # Order_value = db.Column(db.String(50))
        #Weight = db.Column(db.String(50))
        
        # Shipper = db.Column(db.String(50))
        # Shipper_address = db.Column(db.String(50))
        # Shipper_Country = db.Column(db.String(50))
        # Consignee_Country = db.Column(db.String(50))
        # Order_date = db.Column(db.String(50))
        # Required_delivery = db.Column(db.String(50))
        # Journey_type = db.Column(db.String(50))
        # Tax = db.Column(db.String(50))

        def __repr__(self):
            return '<Task %r>' % self.order_id

#Routes Database
class Routes(db.Model):
    Route_Number = db.Column(db.Integer,primary_key=True)
    Source = db.Column(db.String(100))
    Destination = db.Column(db.String(100))
    Container_Size = db.Column(db.Integer)
    Carrier = db.Column(db.String(50))
    Travel_Mode = db.Column(db.String(30))
    Fixed_Freight_Cost = db.Column(db.Integer)
    Port_Airport_Rail_Handling_Cost=db.Column(db.Integer)
    Bunker_Fuel_Cost=db.Column(db.Integer)
    Documentation_Cost = db.Column(db.Integer)
    Equipment_Cost = db.Column(db.Integer)
    Extra_Cost = db.Column(db.Integer)
    Warehouse_Cost = db.Column(db.Integer)
    Transit_Duty = db.Column(db.Integer)
    CustomClearance_time=db.Column(db.Integer)
    Port_Airport_Rail_Handling_time=db.Column(db.Integer)
    Extra_Time = db.Column(db.Integer)
    Transit_time=db.Column(db.Integer)
    Monday = db.Column(db.Integer)
    Tuesday = db.Column(db.Integer)
    Wednesday = db.Column(db.Integer)
    Thursday = db.Column(db.Integer)
    Friday = db.Column(db.Integer)
    Saturday = db.Column(db.Integer)
    Sunday = db.Column(db.Integer)
    SrcLat = db.Column(db.Float)
    SrcLong = db.Column(db.Float)
    DesLat = db.Column(db.Float)
    DesLong = db.Column(db.Float)

    def __repr__(self):
        return '<Task %r>' % self.Source + self.Destination + self.Carrier

#Shipments Database -- under consideration
class Shipments(db.Model):
    container_id = db.Column(db.Integer,primary_key=True)
    Route_Number = db.Column(db.Integer)
    shipper_id  = db.Column(db.Integer)
    Travel_Mode = db.Column(db.String(30))
    Container_Size = db.Column(db.Integer)

#Shippers Database
class Shippers(db.Model):
    shipper_id = db.Column(db.String(50),primary_key=True)
    password = db.Column(db.String(300))
    shipper_name = db.Column(db.String(50))

#JWT Token for login
def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message':'Token is missing'})

       
       
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms='HS256')
            #print(data)
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return jsonify({'message':'Token is invalid!'})
        return f(*args,**kwargs)

    return decorated

#Landing Page
@app.route('/')
def index():
    return render_template("index.html")

#Fetching User
@app.route('/user/<public_id>',methods=['GET'])
@token_required
def get_user(public_id):

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message':'No user found!'})
    
    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user':user_data})

#Fetching Users
@app.route('/user',methods=['GET'])
#@token_required
def get_users():
    users = User.query.all()
    if not users:
        return jsonify({'message':'No user found!'})
    user_list = {}    
    for user in users:    
        
        user_list['public_id'] = user.public_id
        user_list['name'] = user.name
        user_list['password'] = user.password
        

    return jsonify({'users':user_list})

#Adding User
@app.route('/user',methods=['POST'])
#token_required
def create_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'],method='sha256')
    new_user = User(public_id=str(uuid.uuid4()),name=data['name'],password=hashed_password,email=data['email'],firm_name=data['firm_name'],address=data['address'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'new user added'})

#Deleting User
@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(public_id):
  
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})

#Logging In Of User
@app.route('/user/login',methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data['name'] or not data['password']:
        return make_response('Could not verify user',401,{'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    user = User.query.filter_by(name=data['name']).first()

    if not user:
        return make_response('Could not verify stored user', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    if check_password_hash(user.password,data['password']):
        signing_key = 'CLIENT_SECRET'
        token = jwt.encode({'public_id':user.public_id,'exp':datetime.utcnow()+timedelta(minutes=300)},app.config['SECRET_KEY'])
        return jsonify({'token':token})
        

    return make_response('Could not verify password', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#Fetch Routes  
@app.route('/route',methods=['GET'])
def get_routes():
    routes = Routes.query.all()
    if not routes:
        return jsonify({'Message':"routes Not found"})
    else:
        route=[]
        for r in routes:
            route.append((r.Source,r.Destination,r.Carrier))
        return jsonify({"routes":route})

#Add Routes from excel dataset 
@app.route('/route/add',methods=['GET'])
def add_all_routes():
    data = pd.read_excel('model data-4.xlsx')
    count =0 
    for i in range(len(data)):
       source = data.iloc[i]['Source']
       destination = data.iloc[i]['Destination']
       container = data.iloc[i]['Container Size']
       carrier = data.iloc[i]['Carrier']
       travel = data.iloc[i]['Travel Mode']
       freight = data.iloc[i]['Fixed Freight Cost']
       port = data.iloc[i]['Port/Airport/Rail Handling Cost']
       bunker = data.iloc[i]['Bunker/ Fuel Cost']
       document = data.iloc[i]['Documentation Cost']
       equipment = data.iloc[i]['Equipment Cost']
       extra = data.iloc[i]['Extra Cost']
       warehouse = data.iloc[i]['Warehouse Cost']
       transit = data.iloc[i]['Transit Duty']
       customer = data.iloc[i]['CustomClearance time (hours)']
       portairport = data.iloc[i]['Port/Airport/Rail Handling time (hours)']
       extra_time = data.iloc[i]['Extra Time']
       transit_hours = data.iloc[i]['Transit time (hours)']
       monday = data.iloc[i]['Monday']
       tuesday = data.iloc[i]['Tuesday']
       wednesday = data.iloc[i]['Wednesday']
       thursday = data.iloc[i]['Thursday']
       friday = data.iloc[i]['Friday']
       saturday = data.iloc[i]['Saturday']
       sunday = data.iloc[i]['Sunday']
       SrcLat,SrcLong = get_location(data.iloc[i]['Source'])
       DesLat, DesLong = get_location(data.iloc[i]['Destination'])

       new_route = Routes(
        Source = source,
        Destination = destination,
        Container_Size =container,
        Carrier = carrier,
        Travel_Mode = travel,
        Fixed_Freight_Cost = freight,
        Port_Airport_Rail_Handling_Cost=port,
        Bunker_Fuel_Cost=bunker,
        Documentation_Cost = document,
        Equipment_Cost = equipment,
        Extra_Cost = extra,
        Warehouse_Cost = warehouse,
        Transit_Duty = transit,
        CustomClearance_time=customer,
        Port_Airport_Rail_Handling_time= portairport,
        Extra_Time = extra_time,
        Transit_time= transit_hours,
        Monday = monday ,
        Tuesday = tuesday,
        Wednesday = wednesday,
        Thursday = thursday,
        Friday = friday,
        Saturday = saturday,
        Sunday = sunday,
        SrcLat = SrcLat,
        SrcLong = SrcLong,
        DesLat = DesLat,
        DesLong =DesLong
       )
       count +=1
       db.session.add(new_route)
       db.session.commit()
             
    return {"Routes_add":count}
    

#Place Order
@app.route('/user/order/<public_id>',methods=['POST'])
def place_order(public_id):
    data = request.get_json()
    commodity = data['commodity']
    routes_list = data['routes']
    # transaction_cost = data['transaction_cost']
    route_common_id = str(uuid.uuid4())
    for route in routes_list:
        query = Routes.query.filter_by(
            Source=route['From'],
            Destination=route['To'],
            Carrier=route['Carrier']
        ).all()
        if(len(query)>0):
            query=query[0].Route_Number
            print(query)
        else:
            continue
        if(Shippers.query.filter_by(shipper_name = route['Carrier']).first()):
                Shipper_id = Shippers.query.filter_by(shipper_name = route['Carrier']).first().shipper_id
        else:
            Shipper_id='Default_id'
        
        order = Orders(
            route_common_id=route_common_id,
            # Transaction_cost=transaction_cost
            public_id = public_id,
            status = "Ordered",
            route_number = query,
            Source = route['From'],
            Destination = route['To'],
            Commodity = commodity,
            Shipper_id=Shipper_id,
            Shipper_name = route['Carrier']
        )
        db.session.add(order)
    db.session.commit()

    return jsonify({"message":"order placed"})

#modify orders
@app.route('/user/update-order',methods=['POST'])
def change_order():
    input = request.get_json()
    data = pd.read_excel('model data-4.xlsx')
    temp_routes1 = data.loc[data['Source']==input['Source']]
    temp_routes2 = temp_routes1.loc[temp_routes1['Destination']==input['Destination']]
    temp_routes3 = temp_routes2.loc[temp_routes2['Carrier']==input['Carrier']]
    temp_route4 =  pd.concat([temp_routes2, temp_routes3, temp_routes3]).drop_duplicates(keep=False)
    print(temp_route4.head())
    # min_cost = 10e15
    # min_index = 0
    # for i in range(len(temp_routes1)):
    #     temp_cost = temp_routes1.iloc[i]['Fixed Freight Cost'] + temp_routes1.iloc[i]['Port/Airport/Rail Handling Cost'] + temp_routes1.iloc[i]['Bunker/ Fuel Cost'] + temp_routes1.iloc[i]['Documentation Cost'] +  temp_routes1.iloc[i]['Equipment Cost'] +  temp_routes1.iloc[i]['Extra Cost'] 
    #     if temp_cost < min_cost:
    #         min_cost = temp_cost
    #         min_index = i
    # order = Orders.query.filter_by(order_id=input['order_id']).first()
    # order.Source = temp_routes1.iloc[min_index]['Source']
    # order.Destination = temp_routes1.iloc[min_index]['Destination']
    # shipper = Shippers.query.filter_by(shipper_name = temp_routes1.iloc[min_index]['Carrier']).first()
    # order.Shipper_id = shipper
    # order.Shipper_name = temp_routes1.iloc[min_index]['Carrier']
    # db.session.commit()
    return jsonify({"updated_route":"order"})
    
@app.route('/orders',methods=['GET'])
def get_orders_utility():
    orders = Orders.query.all()
    li =[]
    for order in orders:
        li.append([order.order_id,order.Source,order.Destination,order.route_common_id,order.status])
    return jsonify({"Result list":li})

# @app.route('/routes',methods=['GET'])
# def get_routes_utilities():
#     routes = Routes.query.all()
#     totoal_routes = []
#     for route in routes:


#View the history of previous orders made by the user
@app.route('/user/view-history/<user_id>',methods=['GET'])
def view_user_history(user_id):
    orders_list = Orders.query.filter_by(public_id=user_id)
    different_orders = []
    result=[]
    for order in orders_list:
        if order.route_common_id not in different_orders:
            different_orders.append(order.route_common_id)
    for route_id in different_orders:
        sub_orders = Orders.query.filter_by(route_common_id=route_id).all()
        sub_orders_delivered  = Orders.query.filter_by(
            route_common_id = route_id,
            status='Delivered',
        ).all()
        sub_orders_returned = Orders.query.filter_by(
            route_common_id=route_id,
            status='Returned'
        ).all()
        sub_orders_cancelled = Orders.query.filter_by(
            route_common_id=route_id,
            status='Cancelled'
        ).all()
        if len(sub_orders)==len(sub_orders_delivered):
            temp ={}
            temp['Source']=sub_orders[0].Source
            temp['Destination']=sub_orders[-1].Destination
            temp['Status']='Delivered',
            temp['Route_Common_Id']=sub_orders[0].route_common_id
        elif(len(sub_orders_returned)>0):
            temp ={}
            temp['Source']=sub_orders[0].Source
            temp['Destination']=sub_orders[-1].Destination
            temp['Status']='Returned',
            temp['Route_Common_Id']=sub_orders[0].route_common_id
        elif(len(sub_orders_cancelled)>0):
            temp ={}
            temp['Source']=sub_orders[0].Source
            temp['Destination']=sub_orders[-1].Destination
            temp['Status']='Cancelled',
            temp['Route_Common_Id']=sub_orders[0].route_common_id
        else:
            temp ={}
            temp['Source']=sub_orders[0].Source
            temp['Destination']=sub_orders[-1].Destination
            temp['Status']='Not Delivered'
            temp['Route_Common_Id']=sub_orders[0].route_common_id
        result.append(temp)
    return jsonify({'orders-list':result})

#Cancel Order
@app.route('/user/cancel-order/<order_id>',methods=['GET'])
def cancel_order(order_id):
    order = Orders.query.filter_by(order_id=order_id).first()
    order.status='Returned'
    for order in Orders.query.filter_by(route_common_id=order.route_common_id).all():
        order.status='Returned'
    db.session.commit()
    return jsonify({
        'order-status-changed-to':order.status
    })

#View Order Status - how many shippers have accepted
@app.route('/user/view-order-status/<route_common_id>',methods=['GET'])
def view_order_status(route_common_id):
    total = Orders.query.filter_by(route_common_id=route_common_id).order_by(Orders.order_id).all()
    result = []
    for order in total:
        result.append({
            'Source':order.Source,
            'Destination':order.Destination,
            'Shipper_name':order.Shipper_name,
            'Status':order.status,
            'Commodity':order.Commodity
        })
    return jsonify({
        'Total':result
    })

#Shippers API
#Returns all shippers  
@app.route('/shipper',methods=['GET'])
def get_all_shipper():
    shippers = Shippers.query.all()
    li = []
    for shipper in shippers:
        li.append({"shipper_id":shipper.shipper_id,"name":shipper.shipper_name})
    return jsonify({'shippers':li})

#Fetch a specific shipper
@app.route('/shipper/<shipper_id>',methods=['GET'])
#@token_required
def get_shipper(shipper_id):

    shipper = Shippers.query.filter_by(shipper_id=shipper_id).first()

    if not shipper:
        return jsonify({'message':'No user found!'})
    
    user_data = {}
    user_data['shipper_id'] = shipper.shipper_id
    user_data['shipper_name'] = shipper.shipper_name
    user_data['password'] = shipper.password
    return jsonify({'user':user_data})

#Returns List of Shippers
@app.route('/shipper',methods=['GET'])
def get_shippers():
    shippers = Shippers.query.all()
    if not shippers:
        return jsonify({'message':'No user found!'})
    user_data = {}    
    for shipper in shippers:    
        user_data['shipper_id'] = shipper.shipper_id
        user_data['shipper_name'] = shipper.shipper_name
        user_data['password'] = shipper.password
    return jsonify({'shippers':user_data})

#Add Shipper
@app.route('/shipper',methods=['POST'])
#token_required
def create_shipper():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'],method='sha256')
    new_user = Shippers(shipper_id=str(uuid.uuid4()),shipper_name=data['shipper_name'],password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'new user added'})

#Delete a shipper
@app.route('/shipper/<public_id>', methods=['DELETE'])
@token_required
def delete_shipper(public_id):
  
    user = Shippers.query.filter_by(shipper_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})

#Logging in by Shipper
@app.route('/shipper/login',methods=['POST'])
def login_shipper():
    data = request.get_json()
    
    if not data or not data['shipper_name'] or not data['password']:
        return make_response('Could not verify user',401,{'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    user = Shippers.query.filter_by(name=data['shipper_name']).first()

    if not user:
        return make_response('Could not verify stored shipper', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
    
    if check_password_hash(user.password,data['password']):
        signing_key = 'CLIENT_SECRET'
        token = jwt.encode({'shipper_id':user.shipper_id,'exp':datetime.utcnow()+timedelta(minutes=300)},app.config['SECRET_KEY'])
        return jsonify({'token':token})
        

    return make_response('Could not verify password', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

#Add a route for a shipper
@app.route('/shipper/create-route/',methods=['POST'])
def create_route():
    data  = request.get_json()
    SrcLat,SrcLong = get_location(data['source'])
    DesLat, DesLong = get_location(data['destination'])
    route = Routes(
        Source = data['source'],
        Destination = data['destination'],
        Container_Size=data['container-size'],
        Carrier = data['carrier'],
        Travel_Mode = data['travel-mode'],
        Fixed_Freight_Cost = data['fixed-freight-cost'],
        Port_Airport_Rail_Handling_Cost=data['port-airport-cost'],
        Bunker_Fuel_Cost=data['bunker-fuel-cost'],
        Documentation_Cost = data['documentation-cost'],
        Equipment_Cost = data['equipment-cost'],
        Extra_Cost = data['extra-cost'],
        Warehouse_Cost = data['warehouse-cost'],
        Transit_Duty = data['transit-duty'],
        CustomClearance_time=data['custom-clearance-time'],
        Port_Airport_Rail_Handling_time=data['port-airport-handling-time'],
        Extra_Time = data['extra-time'],
        Transit_time=data['transit-time'],
        Monday = data['monday'],
        Tuesday = data['tuesday'],
        Wednesday = data['wednesday'],
        Thursday =data['thursday'],
        Friday = data['friday'],
        Saturday = data['saturday'],
        Sunday = data['sunday'],
        SrcLat = SrcLat,
        SrcLong = SrcLong,
        DesLat = DesLat,
        DesLong =DesLong
    )

    db.session.add(route)
    db.session.commit()
    return jsonify({'Message':"new route added"})

@app.route('/shipper/get-routes',methods=['GET'])
def get_all_routes():
    routes = Routes.query.all()
    li =[]
    for route in routes:
        li.append({"Source":route.Source,"Destination":route.Destination,"Carrier":route.Carrier})

    return jsonify({"route_list":li})

#Fetch the orders pending for the shipper
@app.route('/shipper/get-orders/<shipper_id>',methods=['GET'])
def get_orders(shipper_id):
    order_list = Orders.query.filter_by(Shipper_id = shipper_id).all()
    blacklisted_order=[]
    #Reverse Logistics on Shipper Side
    li = []
    for order in order_list:
        # total = Orders.query.filter_by(public_id=order.public_id).all()
        # returned = Orders.query.filter_by(public_id=order.public_id,status='Returned').all()
        li.append({'order_id':order.order_id,'public_id':order.public_id,'source':order.Source,'Destination':order.Destination,'commodity':order.Commodity})
        # if (len(returned)//len(total)>0.5):
        # blacklisted_order.append(li[(len(li)-1)%len(li)]['order_id'])
        # blacklisted_order.append(li[(0+3)%len(li)]['order_id'])
    return jsonify({"orders":li})
    

#Update the staus of order as accepted or declined by a shipper
@app.route('/shipper/update-status',methods=['POST'])
def update_status():
    data = request.get_json()
    # route_common_id = data['route_common_id']
    is_accepted = data['is_accepted']
    order = Orders.query.filter_by(order_id=data['order_id']).all()[0]
    if is_accepted==1:
        order.status='Accepted'
    elif is_accepted==2:
        order.status='Rejected'
    elif is_accepted==3:
        order.status='Shipped'
    elif is_accepted==4:
        order.status= 'Delivered'
    else:
        
        order.status= 'Cancelled'
        # for order in Orders.query.filter_by(route_common_id=order.route_common_id).all():
        #     order.status='Cancelled'
        #Look For an Alternative shipper who does the same service

    db.session.commit()
    return jsonify({
        'order_id':data['order_id'],
        'status':order.status
    })

#View the status of the route previously accepted
@app.route('/shipper/view-status/<order_id>',methods=['GET'])
def view_status(order_id):
    route_common_id = Orders.query.filter_by(order_id=order_id).first().route_common_id
    total_orders = len(Orders.query.filter_by(route_common_id=route_common_id).all())
    accepted = len(Orders.query.filter_by(route_common_id=route_common_id,status='Accepted').all())
    return jsonify({
        'Accepted':accepted,
        'Total-Shippers':total_orders})

#Find the minimum shortest path
@app.route('/routes',methods=['POST'])
#@token_required
def shortest_route():
    if request.method == 'POST':
        data = request.get_json()
        Source = data['source']
        Source1 = find_closest(Source)
        Destination = data['destination']
        Destination1 = find_closest(Destination)
        Commodity = data['commodity']
        Order_value = data['order_value']
        Weight = data['weight']
        Volume = data['volume']
        Shipper = "XYZ"
        Shipper_address = "888 street"
        Shipper_Country = "555 street"
        Consignee_Country = "India"
        Order_date = data['order_date']
        Required_delivery = data['required_delivery']
        Journey_type = data['journey_type']
        Tax = data['tax']

        input = {"Order Number":[1],
                 "Ship From":[Source1],
                 "Ship To":[Destination1],
                 "Commodity":[Commodity],
                 "Order Value":[int(Order_value)],
                 "Weight (KG)":[float(Weight)],
                 "Volume":[int(Volume)],
                 "Shipper Name":[Shipper],
                 "Shipper Address":[Shipper_address],
                 "Shipper Country":[Shipper_Country],
                 "Consignee Country":[Consignee_Country],
                 "Order Date":[datetime.strptime(Order_date,"%d %m %Y")],
                 "Required Delivery Date":[datetime.strptime(Required_delivery,"%d %m %Y")],
                 "Journey Type":[Journey_type],
                 "Tax Percentage":[float(Tax)],
                 }
                 
        paths = find_shortest(input)
        # total_containers =0
        # total_time=0
        # min_container_wastage=10000000
        # min_index_path=None
        # for path in paths:
        #     total_time=0
        #     for sub_path in path['Route']:
        #         total_time+=sub_path['Time']
        #         if input['Volume']>sub_path['Container']:
        #             total_containers = input['Volume']//sub_path['Container']
        #         else:
        #             total_containers=1
        #         wastage = abs(input['Volume']-total_containers*sub_path['Container'])
        #         if wastage<min_container_wastage:
        #             min_container_wastage=wastage
        #             min_index_path=path
        new_path = []
        for path in paths:
            path['Total cost'] +=0
            new_path.append(path)
        return new_path
        
                
        # for path in paths:
        #     temp={
        #         "By": "Truck",
        #         "Date": input['Order Date'],
        #         "From": Source,
        #         "No": "1",
        #         "To": Source1['City'],
        #         "SrcLat": Source1["SrcLat"],
        #         "SrcLong": Source1["SrcLong"],
        #         "DestLat": Source1["DestLat"],
        #         "DestLong": Source1["DestLong"]
        #         }
        #     path["Route"].insert(0,temp)
        #     temp={
        #         "By": "Truck",
        #         "Date": input['Required Delivery Date'],
        #         "From": Destination1["City"],
        #         "No": str(len(path)),
        #         "To": Destination,
        #         "SrcLat": Destination1["DestLat"],
        #         "SrcLong": Destination1["DestLong"],
        #         "DestLat": Destination1["SrcLat"],
        #         "DestLong": Destination1["SrcLong"]
        #         }
        #     path["Route"].append(temp)
        #     path["Transportation cost"]+=(Source1['distance']*2.0)+(Destination1['distance']*2.0)
        #     path["Total cost"]+=(Source1['distance']*2.0)+(Destination1['distance']*2.0)
        # return [json.loads(path) for path in paths]


if __name__ == "__main__":
    app.run(debug=True,port = 4000)