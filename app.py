from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL 
import yaml,smtplib
from email.mime.text import MIMEText
import os
from flask import make_response
import logging



app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Load database configuration
with open('db.dev.yaml', 'r') as file:
    db = yaml.load(file, Loader=yaml.FullLoader)

# Configure MySQL
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

app.config['CORS_HEADERS'] = 'Content-Type'


mysql = MySQL(app)
# cors = CORS(app)
logging.getLogger('flask_cors').level = logging.DEBUG
# cors =CORS(app, origins=["http://localhost:80","http://localhost"])
@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    print(origin)
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, OPTIONS, PUT, PATCH, DELETE')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)

    return response





@app.route("/register", methods=["POST"])
def register():

    payload = request.json
    username = payload["username"]
    password = payload["password"]
    email_address = payload["email"]
    phonenumber = payload["phone_number"]
    bloodgroup = payload["bloodgroup"]
    dob = payload["DOB"]
    address = payload["address"]
    city = payload["city"]
    state = payload["state"]
    pincode = payload["pincode"]
    print(payload)
    print (username)
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user(username, password,email, phone_number, blood_group, dob, address, city, state, pin_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, password,email_address, phonenumber, bloodgroup, dob, address, city, state, pincode))
    mysql.connection.commit()
    cur.close()
    
    return payload




@app.route("/login", methods=["POST"])
def login():
       
    payload = request.json
    username = payload["username"]
    password = payload["password"]


    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id ,username, password, role_id FROM user WHERE username = %s AND password = %s", (username, password))
    existing_user = cur.fetchone()
    cur.close()
    print(existing_user)

    if existing_user:
     
        response={
            "username":username, 
            "role_id":existing_user[3],
            "user_id":existing_user[0]
            
        }
        return response
    else: 
        response={
            "message":"user doesnot exist"
        }
        return make_response(response,"404")




   

# @app.errorhandler(404)
# def page_not_found(e):
#     return "This route doesn't exist"

# @app.errorhandler(500)
# def internal_server_error(e):
#     return "Application is down right now"


@app.route('/donor_form/<user_id>', methods=['POST'])
# @cross_origin()
def donor_form(user_id):


    payload = request.json
    print (payload)
    units = int(payload.get('units'))
    disease = payload.get('disease')
    donated_date = payload.get('donated_date')
    print("donor form",user_id)

    cur = mysql.connection.cursor()
    
    cur.execute("INSERT INTO donation (user_id, units, disease, donated_date) VALUES (%s, %s, %s, %s)", (user_id, units, disease, donated_date))
    mysql.connection.commit()
    cur.close()
    return jsonify(payload)


@app.route('/donation_requests', methods=['GET'])
def donation_requests():
    # if not session.get("username"):
    #     return jsonify({"message": "Unauthorized access"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT donation_id, username, blood_group, units, disease, donated_date, phone_number, status FROM user JOIN donation ON user.user_id = donation.user_id")
    donation_requests = cur.fetchall()
    cur.close()

    # Convert the query results to a list of dictionaries
    donation_requests_list = [
        {
            "donation_id": req[0],
            "username": req[1],
            "blood_group": req[2],
            "units": req[3],
            "disease": req[4],
            "donated_date": req[5],
            "phone_number": req[6],
            "status": req[7]
        }
        for req in donation_requests
    ]

    return jsonify({'donationrequests': donation_requests_list})


@app.route('/patient_form/<user_id>', methods=['POST'])
def patient_form(user_id):
    payload = request.json
    print (payload)
    units = int(payload.get('units'))
    reason = payload.get('reason')
    requested_date = payload.get('requested_date')
    

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO patient_request (user_id, units, reason, requested_date) VALUES (%s, %s, %s, %s)", (user_id, units, reason, requested_date))
    mysql.connection.commit()
    cur.close()
    
    return jsonify(payload)




@app.route('/patient_requests', methods=['GET'])
def patient_requests():
 
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT request_id, username, blood_group, units, reason, requested_date, phone_number, status FROM user JOIN patient_request ON user.user_id = patient_request.user_id")
    userdetails = cur.fetchall()
    cur.close()
    
    # Convert data to list of dictionaries for JSON response
    patient_requests_list = [{
        'request_id': row[0],
        'username': row[1],
        'blood_group': row[2],
        'units': row[3],
        'reason': row[4],
        'requested_date': row[5],
        'phone_number': row[6],
        'status': row[7]
    } for row in userdetails]
    
    return jsonify({'patientrequests': patient_requests_list})

    


@app.route('/reject_patient_request/<request_id>', methods=['POST'])
def reject_patient_request(request_id):
  
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE patient_request SET status = 'rejected' WHERE request_id = %s", [request_id])
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"message": "Request rejected"})


@app.route('/delete/<donation_id>', methods=['POST'])
def delete(donation_id):
   
    cur = mysql.connection.cursor()
    cur.execute("UPDATE donation SET status = 'rejected' WHERE donation_id = %s", [donation_id])
    mysql.connection.commit()
    cur.close()
    response = {"message": "Request rejected"}
    
    return jsonify(response)

@app.route('/update_donation_request/<donation_id>', methods=['PUT'])
def update_donation_request(donation_id):
    payload = request.json
    status = payload.get('status')
    # Create a cursor to interact with the database
    cur = mysql.connection.cursor()
    
    try:
        # Update the donation status to 'Accepted'
        cur.execute("UPDATE donation SET status = %s WHERE donation_id = %s", (status, donation_id))
        
        # Fetch donor details
        cur.execute("""
            SELECT donation.units, user.blood_group
            FROM donation
            INNER JOIN user ON user.user_id = donation.user_id
            WHERE donation.donation_id = %s
        """, [donation_id])
        donor = cur.fetchone()

        if donor:
            units = donor[0]
            blood_group = donor[1]
            
            # Update the blood stock
            cur.execute("UPDATE blood_stock SET units = units + %s WHERE bloodgroup = %s", (units, blood_group))
            mysql.connection.commit()
            
            response = {"message": "Donation request updated!"}
        else:
            response = {"message": "doantion request not found!"}
    
    except Exception as e:
        mysql.connection.rollback()
        response = {"message": f"An error occurred: {str(e)}"}
    
    finally:
        cur.close()

    return jsonify(response)


@app.route('/update_patient_request/<request_id>', methods=['PUT'])
def update_patient_request(request_id):
    payload = request.json
    status = payload.get('status')
    # Create a cursor to interact with the database
    cur = mysql.connection.cursor()
    
    try:
        # Update the donation status to 'Accepted'
        cur.execute("UPDATE patient_request SET status = %s WHERE request_id = %s", (status, request_id))
        
        # Fetch donor details
        cur.execute("""
            SELECT patient_request.units, user.blood_group
            FROM patient_request
            INNER JOIN user ON user.user_id = patient_request.user_id
            WHERE patient_request.request_id = %s
        """, [request_id])
        donor = cur.fetchone()

        if donor:
            units = donor[0]
            blood_group = donor[1]
            
            # Update the blood stock
            cur.execute("UPDATE blood_stock SET units = units - %s WHERE bloodgroup = %s", (units, blood_group))
            mysql.connection.commit()
            
            response = {"message": "patient request updated!"}
        else:
            response = {"message": "patient request not found!"}
    
    except Exception as e:
        mysql.connection.rollback()
        response = {"message": f"An error occurred: {str(e)}"}
    
    finally:
        cur.close()

    return jsonify(response)




# @app.route('/blood_stock', methods=['GET'])
# def blood_stock_view():
#     if not session.get("username"):
#         return redirect("/login")
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT bloodgroup, units FROM blood_stock")
#     blood_stock = cur.fetchall()
#     cur.close()
#     blood_stock_dict = {row[0]: row[1] for row in blood_stock}
#     return render_template('blood_stock.html', blood_stock=blood_stock_dict)


@app.route('/blood_stock', methods=['GET'])
def blood_stock_view():
    # if not session.get("username"):
    #     return jsonify({"message": "Unauthorized access"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT bloodgroup, units FROM blood_stock")
    blood_stock = cur.fetchall()
    cur.close()

    # Convert the data to a dictionary for JSON response
    blood_stock_dict = {row[0]: row[1] for row in blood_stock}
    return jsonify(blood_stock_dict)



    

# @app.route('/patient_history', methods=['GET'])
# def patient_history():
#     if not session.get("username"):
#         return redirect("/login")
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT username, blood_group, units, reason, requested_date, status FROM user JOIN patient_request ON user.user_id = patient_request.user_id")
#     patient_history = cur.fetchall()  # Ensure this variable name matches
#     cur.close()
#     return render_template('patient_history.html', patient_history=patient_history)

# @app.route('/donor_history', methods=['GET'])
# def donor_history():
#     if not session.get("username"):
#        return redirect("/login")
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT username, blood_group, units, disease, donated_date, status FROM user JOIN donation ON user.user_id = donation.user_id")
#     patient_history = cur.fetchall()  # Ensure this variable name matches
#     cur.close()
#     return render_template('donor_history.html', donor_history=donor_history)

@app.route('/donor_history', methods=['GET'])
def donor_history():

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT donation_id,blood_group, units, disease, donated_date, status 
            FROM user 
            JOIN donation ON user.user_id = donation.user_id
            
        """)
        donor_history = cur.fetchall()
        cur.close()

        # Check if no donor history is found for the user
        if not donor_history:
            return jsonify({"message": "No donation history found for this user"}), 404
        
        # Convert the data to a list of dictionaries (JSON-friendly format)
        donor_history_list = [{
            'donation_id':row[0],
            'blood_group': row[1],
            'units': row[2],
            'disease': row[3],
            'donated_date': row[4],
            'status': row[5]
        } for row in donor_history]

        return jsonify({"donorhistory": donor_history_list})


@app.route('/patient_history', methods=['GET'])
def patient_history():
    # if not session.get("username"):
    #     return jsonify({"message": "Unauthorized access"}), 401
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, blood_group, units, reason, requested_date, status,request_id FROM user JOIN patient_request ON user.user_id = patient_request.user_id")
    patient_history = cur.fetchall()
    cur.close()

    # Convert the data to a list of dictionaries (JSON-friendly format)
    patient_history_list = [{
        'username': row[0],
        'blood_group': row[1],
        'units': row[2],
        'reason': row[3],
        'requested_date': row[4],
        'status': row[5],
        'request_id':row[6]
    } for row in patient_history]

    return jsonify({"patienthistory":patient_history_list})




@app.route('/view_donations/<user_id>', methods=['GET'])
def view_donations(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT units, disease, donated_date, status,user_id FROM donation WHERE user_id = %s", [user_id])
    view_donations = cur.fetchall()
    cur.close()
    
    # Convert the data to a list of dictionaries (JSON-friendly format)
    donations_list = [{
        'units': row[0],
        'disease': row[1],
        'donated_date': row[2],
        'status': row[3],
        'user_id':row[4]
    } for row in view_donations]

    return jsonify({'donations': donations_list})



@app.route('/test_api')
def test_api():
    return 'hello'

@app.route('/test_api2')
def test_api2():
    name= 'jayadeep'
    return name

@app.route('/test_api3')
def test_api3():
    data = {
        'name': 'jayadeep',
        'age':  23
        }
    return data

@app.route('/view_requests/<user_id>', methods=['GET'])
def view_requests(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT units,reason,requested_date,status,user_id from patient_request where user_id = %s",[user_id])
    view_requests=cur.fetchall()
    mysql.connection.commit()
    cur.close()
    patient_list = [{
        'units': row[0],
        'reason': row[1],
        'requested_date': row[2],
        'status': row[3],
        'user_id':row[4]
    } for row in view_requests]

    return jsonify({'viewrequests': patient_list})
    # print (view_requests)
    # output = jsonify(view_requests)
    # print (output)

    # #return render_template('view_requests.html',view_requests=view_requests)
    # return output


    

if __name__ == '__main__':
    # initialize_blood_stock()  # Initialize the blood stock table if needed
    app.run(host='0.0.0.0',debug=True)
