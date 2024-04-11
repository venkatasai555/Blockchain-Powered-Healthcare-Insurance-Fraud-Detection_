from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import ipfsapi
from web3 import Web3,HTTPProvider
import json

def connectWithBlockchain():
    web3=Web3(HTTPProvider('http://127.0.0.1:7545'))
    web3.eth.defaultAccount=web3.eth.accounts[0]

    with open('../build/contracts/Insurance.json') as f:
        artifact_json=json.load(f)
        contract_abi=artifact_json['abi']
        contract_address=artifact_json['networks']['5777']['address']
    
    contract=web3.eth.contract(abi=contract_abi,address=contract_address)
    return contract,web3


client = MongoClient('127.0.0.1', 27017)
db = client.insurance_fraud_detection

hospitals_db=db['hospitals']
patients_db=db['patients']
insurance_db=db['insurance']

c = db['c']
claims_collection = db['c']  # MongoDB collection for claims

app = Flask(__name__)
app.secret_key = 'sai@'
app.config["uploads"] = "uploads/"


@app.route('/')
def home():
    return render_template('Index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


# Routes for login pages
@app.route('/patient_login')
def login():
    return render_template('Patient_l.html')

@app.route('/hospital_login')
def hospital_management_login():
    return render_template('Hospital_Management_l.html')

@app.route('/insurance_login')
def insurance_company_login():
    return render_template('Insurance_company_l.html')

@app.route('/patient_home')
def Patient_home_page():
    return render_template('Patient_Home.html')

# Routes for signup pages
@app.route('/patient_signup')
def signup():
    hos_data=hospitals_db.find()
    data=[]
    for i in hos_data:
        dummy=[]
        dummy.append(i['hospital'])
        dummy.append(i['username'])
        data.append(dummy)
    return render_template('Patient_s.html',data=data)

@app.route('/hospital_signup')
def hospital_management_signup():
    return render_template('Hospital_s.html')

@app.route('/insurance_signup')
def insurance_company_signup():
    return render_template('Insurance_s.html')

patients_and_claims = []

@app.route('/hos_home')
def home_page():
    
    contract,web3=connectWithBlockchain()
    _claimsby,_claimsfor,_claimsids,_claimages,_phonenos,_dobs,_address,_diagnosis,_claimMonth,_amounts,_statuses,_filehashes=contract.functions.viewClaims().call()
    for i in range(len(_claimsids)):
        print(_claimsids[i])
        c.update_one({'claim_id':str(_claimsids[i])},{'$set':{'status':_statuses[i],'file':_filehashes[i]}})
    
    patients_and_claims=c.find()
    return render_template('hospital_home.html', patients_and_claims=patients_and_claims)

@app.route('/upload_claim', methods=['POST'])
def hospital_home():
    data=request.form
    claims_collection.insert_one(dict(data))
    patients_and_claims=claims_collection.find()
    chooseFile=request.files['chooseFile']
    doc=secure_filename(chooseFile.filename)
    chooseFile.save(app.config['uploads']+'/'+doc)
    client=ipfsapi.Client('127.0.0.1',5001)
    print(app.config['uploads']+'/'+doc)
    response=client.add(app.config['uploads']+'/'+doc)
    contract,web3=connectWithBlockchain()
    tx_hash=contract.functions.addClaim(session['username'],data['patient_name'],int(data['claim_id']),int(data['age']),data['phone_number'],data['dob'],data['address'],data['diagnosis'],data['start_month'],data['claim_amount'],response['Hash']).transact()
    web3.eth.waitForTransactionReceipt(tx_hash)
    print(response)
    return render_template('hospital_home.html', patients_and_claims=patients_and_claims)

# Handling form submissions for login
@app.route('/patient_login', methods=['POST'])
def login_data():
    patient_name = request.form['patient_name']
    password = request.form['password']
    user_data = patients_db.find_one({'patient_name': patient_name, 'password': password})
    print(patient_name,password)
    print(user_data)
    if user_data:
        session['patient_name'] = patient_name
        user_data = c.find_one({'patient_name': patient_name})
        if user_data:
            diagnosis = user_data.get('diagnosis', '')
            age = user_data.get('age', '')
            phone_number = user_data.get('phone_number', '')

            # Sample claim status data (replace with your actual claim status retrieval mechanism)
            claims_data = []
            contract,web3=connectWithBlockchain()
            _claimsby,_claimsfor,_claimsids,_claimages,_phonenos,_dobs,_address,_diagnosis,_claimMonth,_amounts,_statuses,_filehashes=contract.functions.viewClaims().call()

            print(session['username'])
            for i in range(len(_claimsids)):
                if(_claimsfor[i]==session['patient_name']):
                    dummy=[]
                    dummy.append(_claimsby[i])
                    dummy.append(_claimsids[i])
                    dummy.append(_claimMonth[i])
                    dummy.append(_statuses[i])
                    dummy.append(_filehashes[i])
                    claims_data.append(dummy)
            
            return render_template('/Patient_Home.html', name=patient_name, diagnosis=diagnosis, age=age, phone=phone_number, claims=claims_data)
        else:
            return 'User data not found.'
    else:
        return render_template('Patient_l.html', err1='Invalid Credentials')

# Handling form submissions for signup
@app.route('/patient_signup', methods=['POST'])
def signup_data():
    hospital = request.form['hospital']
    id = request.form['id']
    patient_name = request.form['patient_name']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password!=confirm_password:
        return render_template('Patient_s.html',err='passwords didnt matched')
    
    existing_user = patients_db.find_one({'patient_name': patient_name})
    if existing_user:
        return render_template('Patient_s.html', err='You have already registered')
    user_data = {'hospital': hospital, 'id': id, 'patient_name': patient_name, 'password': password, 'confirm_password':confirm_password}
    patients_db.insert_one(user_data)
    return render_template('Patient_l.html', res='You have registered successfully')

@app.route('/hospital_login', methods=['POST'])
def hospital_data():
    username = request.form['username']
    password = request.form['password']
    user_data = hospitals_db.find_one({'username': username, 'password': password})
    if user_data:
        session['username'] = username
        return redirect('/hos_home')
    else:
        return render_template('Hospital_Management_l.html', err1='Invalid Credentials')

@app.route('/hospital_signup', methods=['POST'])
def hospital_signup():
    if request.method == 'POST':
        hospital = request.form['hospital']
        id = request.form['id']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password!=confirm_password:
            return render_template('Hospital_s.html',err='passwords didnt matched')

        existing_user = hospitals_db.find_one({'username': username})
        if existing_user:
            return render_template('Hospital_s.html', err='You have already registered')

        user_data = {'hospital': hospital, 'id': id, 'username': username, 'password': password, 'confirm_password': confirm_password}
        hospitals_db.insert_one(user_data)
        return render_template('Hospital_Management_l.html', res='You have registered successfully')

    return render_template('Hospital_s.html')

@app.route('/insurancesignup',methods=['post'])
def insurancesignup():
    if request.method=="POST":
        company_name=request.form['company_name']
        id=request.form['id']
        username=request.form['username']
        password=request.form['password']
        confirm_password=request.form['confirm_password']

        if password!=confirm_password:
            return render_template('Insurance_s.html',err='passwords didnt matched')
        
        existing_user=insurance_db.find_one({'username':username})
        if existing_user:
            return render_template('Insurance_s.html',err='You have already registered')
        
        user_data={'company_name':company_name,'id':id,'username':username,'password':password,'confirm_password':confirm_password}
        insurance_db.insert_one(user_data)
        return render_template('Insurance_company_l.html',res='You have registered successfully')
    
    return render_template('Insurance_s.html')

@app.route('/insurancelogin',methods=['post'])
def insurancelogin():
    id=request.form['id']
    username=request.form['username']
    password=request.form['password']

    user_data={'id':id,'username':username,'password':password}
    insurance_data=insurance_db.find_one(user_data)
    if insurance_data:
        session['username']=username
        return redirect('/insurancedashboard')
    else:
        return render_template('Insurance_company_l.html',err='Invalid Details')

@app.route('/patient_home')
def patient_home_page():
    if 'patient_name' in session:
        patient_name = session['patient_name']
        user_data = c.find_one({'patient_name': patient_name})
        print(user_data)
        if user_data:
            diagnosis = user_data.get('diagnosis', '')
            age = user_data.get('age', '')
            phone_number = user_data.get('phone_number', '')
            
            # Sample claim status data (replace with your actual claim status retrieval mechanism)
            claims = []
            
            return render_template('/Patient_Home.html', name=patient_name, diagnosis=diagnosis, age=age, phone_number=phone_number, claims=claims)
        else:
            return 'User data not found.'
    else:
        return redirect(url_for('/patient_login'))  # Redirect to the login page

@app.route('/insurancedashboard')
def insurancedashboard():
    data=insurance_db.find_one({'username':session['username']})

    claims_data=[]

    contract,web3=connectWithBlockchain()
    _claimsby,_claimsfor,_claimsids,_claimages,_phonenos,_dobs,_address,_diagnosis,_claimMonth,_amounts,_statuses,_filehashes=contract.functions.viewClaims().call()

    print(session['username'])
    for i in range(len(_claimsids)):
            dummy=[]
            dummy.append(_claimsfor[i])
            dummy.append(_claimsby[i])
            dummy.append(_claimsids[i])
            dummy.append(_claimMonth[i])
            dummy.append(_statuses[i])
            dummy.append(_amounts[i])
            dummy.append(_filehashes[i])
            claims_data.append(dummy)

    return render_template('Insurance_dashboard.html',name=data['company_name'],claims=claims_data)

@app.route('/logout')
def logout():
    session['username']=None
    return redirect('/')

@app.route('/updatestatus/<id1>/<id2>')
def updatestatus(id1,id2):
    id1=int(id1)
    id2=int(id2)
    contract,web3=connectWithBlockchain()
    tx_hash=contract.functions.updateClaim(id1,id2).transact()
    web3.eth.waitForTransactionReceipt(tx_hash)
    return redirect('/insurancedashboard')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=9001)
