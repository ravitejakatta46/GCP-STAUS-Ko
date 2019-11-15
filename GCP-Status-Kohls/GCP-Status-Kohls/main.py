from flask import Flask, request,render_template,redirect, request, url_for,session
import logging, json
from util import gcp
import requests
from apiclient import discovery
from oauth2client.client import AccessTokenCredentials
from oauth2client.client import GoogleCredentials
from authlib.client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import settings
from flask_oauth import OAuth 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from urllib2 import Request , urlopen, HTTPError, URLError
import httplib2
GOOGLE_CLIENT_ID = '1079399974466-oh4mfedvo84j8qiribgdq0dteahjppse.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '6x6gq0M2bjpHAnK0jGj8hT-d'
REDIRECT_URI = '/authorized'  # one of the Redirect URIs from Google APIs console

SECRET_KEY = 'development key'

# Flask app setup
app = Flask(__name__)
image = settings.image

#filter_zone=("name:"+region+ "*")
# User session management setup
app.secret_key = SECRET_KEY
oauth = OAuth()
'''
credentials = service_account.Credentials.from_service_account_file('./gcptest-credential.json')
client = datastore.Client(project='sathish-gcp8', namespace='Authorization', credentials=credentials)
'''
cred = credentials.Certificate('./firebase_cred.json')  
firebase_admin.initialize_app(cred)
db = firestore.client()


google = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': ('https://www.googleapis.com/auth/userinfo.email ' + 'https://www.googleapis.com/auth/logging.read '),
                                                'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)

@app.route('/')
def index():
    return render_template('base.html',image=image)


@app.route('/login',methods=['post','get'])
def login():
    access_token = session.get('access_token')                                                                        
    if access_token is None:
        return redirect(url_for('direct'))

    access_token = access_token[0]
    from urllib2 import Request, urlopen, URLError
    #from urllib.request import urlopen,URLError
    #import urllib.request

    headers = {'Authorization': 'OAuth '+ access_token}
    headers2 = {'Authorization': "Bearer {0}".format(access_token),}               
    appurl = ('https://www.googleapis.com/userinfo/v2/me')
    response = requests.get(appurl, headers=headers2)
    json_response = response.json()
    print(json_response)
    session_user = json_response['email']
    print(session_user)
    '''
    query = client.query(kind='Authorization')
    query.add_filter('Email', '=', session_user)
    results = list(query.fetch())
    print len(results)
    print(results)
    '''
    Auth_ref = db.collection(u'Authorization').document(session_user)
    doc = Auth_ref.get()
    print(u'Document data: {}'.format(doc.to_dict()))
    datastore_res=format(doc.to_dict())
    print(datastore_res)

    if ( datastore_res == "None"):
        #return redirect(url_for('index'))
        return render_template('error.html')
    else:
        return redirect(url_for('renderbasetemplate'))
   
    req = Request('https://gcp-stat-dot-cloud-migration-solution.appspot.com/regions',
                                                                        None, headers)
    try:
        res = urlopen(req)
    except URLError as e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('direct'))
        return res.read()
    return res.read()

  

@app.route('/direct')
def direct():
    print("****123")
    callback=url_for('authorized', _external=True)
    print("***$%^&???")
    print(callback)
    return google.authorize(callback=callback)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    # print("******")
    access_token = resp['access_token']
    print(access_token)
    session['access_token'] = access_token, ''
    print(session['access_token'])
    return redirect(url_for('login'))
@app.route('/returnbacktoindex')
def returnbacktoindex():
    return redirect(url_for('index')) 
'''
@app.route('/Unauthorized_user',methods=['GET','POST'])
def Unauthorized_user():
    data=gcp.sending_mail()
    return data
    #return redirect(url_for('index')) 
'''
@app.route('/logout')
def logout():
    session.pop('access_token', None)
    #session.clear('access_token', None)
    return redirect(url_for('index'))   

@google.tokengetter
def get_access_token():
    return session.get('access_token') 

@app.route('/instances', methods=['GET'])
def list_of_instances():
       region = request.args.get('regionname')
       PROJECT_ID = request.args.get('projectName')
       environment = request.args.get('environmentname')
       print("region and project id ===>",region,PROJECT_ID)
       print("Environment :",environment)
       zone_filter = ("name:"+region+"*")
       access_token=get_access_token()
       print(access_token)
       api_key='AIzaSyCiq6sldSNK-POWxZisxaBE_Y5jRtff_YM'
       data = gcp.get_list_of_instances(PROJECT_ID,zone_filter,access_token,api_key)
       return render_template('index.html', image=image,instancesList=data,region=region,projectid=PROJECT_ID,showtable=False,environment=environment)

@app.route('/selectedinstance/<region>/<projectid>', methods=['GET'])
def getSelectedInstance(region,projectid):
       print(region,projectid)
       environment = request.args.get('environmentname')
       print("Environment :",environment)
       zone_filter = ("name:"+region+"*")
       access_token=get_access_token()
       access_token=access_token[0]
       api_key='AIzaSyCiq6sldSNK-POWxZisxaBE_Y5jRtff_YM'
       data = gcp.get_list_of_instances(projectid,zone_filter,access_token,api_key)
       print(data)
       print ("environment :" ,environment)
       data1 = []
       if str(environment) != "all":
           for index, item in enumerate(data, start=0):
               print(index,item)
               if item['name'].find(environment)!= -1:
                   data1.append(data[index])
                   print(data1)
           return render_template('index.html', image=image,instances=data1,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)
       else:
           return render_template('index.html', image=image,instances=data,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)
 
@app.route('/regions', methods=['GET'])
def renderbasetemplate():
    return render_template('region-PI.html',image=image)


@app.route('/instances/<region>/<projectid>/<instance_name>/start', methods=['GET','POST'])
def start_instance(region,projectid,instance_name):
       gcp.start_instance(region,instance_name) 
       print(region,projectid)
       environment = instance_name
       print("Environment :",environment)
       zone_filter = ("name:"+region+"*")
       access_token=get_access_token()
       access_token=access_token[0]
       api_key='AIzaSyCiq6sldSNK-POWxZisxaBE_Y5jRtff_YM'
       data = gcp.get_list_of_instances(projectid,zone_filter,access_token,api_key)
       print(data)
       print ("environment :" ,environment)
       data1 = []
       if str(environment) != "all":
           for index, item in enumerate(data, start=0):
               print(index,item)
               if item['name'].find(environment)!= -1:
                   data1.append(data[index])
                   print(data1)
           return render_template('index.html', image=image,instances=data1,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)
       else:
           return render_template('index.html', image=image,instances=data,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)

@app.route('/instances/<region>/<projectid>/<instance_name>/stop', methods=['GET','POST'])
def stop_instance(region,projectid,instance_name):
       gcp.stop_instance(region,instance_name) 
       print(region,projectid)
       environment = instance_name
       print("Environment :",environment)
       zone_filter = ("name:"+region+"*")
       access_token=get_access_token()
       access_token=access_token[0]
       api_key='AIzaSyCiq6sldSNK-POWxZisxaBE_Y5jRtff_YM'
       data = gcp.get_list_of_instances(projectid,zone_filter,access_token,api_key)
       print(data)
       print ("environment :" ,environment)
       data1 = []
       if str(environment) != "all":
           for index, item in enumerate(data, start=0):
               print(index,item)
               if item['name'].find(environment)!= -1:
                   data1.append(data[index])
                   print(data1)
           return render_template('index.html', image=image,instances=data1,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)
       else:
           return render_template('index.html', image=image,instances=data,instancesList=data,region=region,projectid=projectid,showtable=True,environment=environment)


# main method
if __name__ == '__main__':
    app.run(debug=True)
