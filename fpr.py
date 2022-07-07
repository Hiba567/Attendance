from flask import Flask, request, jsonify
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import time
import json, requests
import random
import serial
import mysql.connector
from datetime import date
from datetime import datetime
from mfrc522 import SimpleMFRC522

app = Flask(__name__)


uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

#@app.route('/add', methods =['POST'])
#def add():
    #data = request.get_json()
    #print(data["Name"])
    #if "Name" in data:
        #return "created", 200
    #else:
        #return "bad request", 400

db = mysql.connector.connect(
    host="",
    user="",
    passwd="",
    database=""
)

cursor = db.cursor()
reader = SimpleMFRC522()


@app.route('/add_admin', methods =['POST'])
def add_admin():
    data = request.get_json()

    ANAME = data["Name"]
    ACIN = data["CIN"]
    
    sql_insert = "INSERT INTO ADMINISTRATEUR (NOM, CIN) VALUES (%s, %s)"
    cursor.execute(sql_insert, (ANAME, ACIN))
    db.commit()
    return "ADMIN ADDED", 200
        

@app.route('/add_rfid', methods =['POST'])
def add_rfid():
    data = request.get_json()
    name = data["Name"]
    CIN = data["CIN"]
    AdminID = data["admin"]
    sdate = data["sdate"]
    edate = data["edate"]
    Type = data["type"]
    
    if "Name" in data:
        sql_insert= "INSERT INTO ADHERENT (Nom, CIN, admin_id, Date_debut, Date_fin) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_insert, (name, CIN, AdminID, sdate, edate))
        db.commit()
        sql_select = "SELECT id FROM ADHERENT ORDER BY id DESC LIMIT 1"
        cursor.execute(sql_select)
        here=cursor.fetchone()
        i=sum(here)
	
        print("Place your rfid")

        id, text = reader.read()
	
        sql_insert = "INSERT INTO RFID (adh_id, Type, idrfid) VALUES (%s, %s, %s)"
        cursor.execute(sql_insert, (i, Type, id))
        db.commit()
        
        return "User saved", 200
    else:
        return "bad request", 400

@app.route('/check_rfid', methods =['GET'])
def check_rfid():
    while True:

        print('Place Card to record attendance')
        id, text = reader.read()
        
        cursor = db.cursor(buffered=True)

        cursor.execute("Select ADHERENT.id FROM ADHERENT INNER JOIN RFID ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
        result = cursor.fetchone()
        
        cursor.execute("Select RFID.Type FROM RFID INNER JOIN ADHERENT ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
        result2 = cursor.fetchone()
                           
        cursor.execute("Select ADHERENT.Nom FROM RFID INNER JOIN ADHERENT ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
        result4 = cursor.fetchone()
        
        today = date.today()
        cursor.execute("Select ADHERENT.Date_fin FROM ADHERENT INNER JOIN RFID ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
        result3 = cursor.fetchone()
        
        if cursor.rowcount >= 1 and today < result3[0]:	
            cursor.execute("UPDATE ADHERENT SET Acces = 1 where id = "+str(result[0]))
            db.commit()		
            cursor.execute("INSERT INTO PRESENCE (adh_id, Type) VALUES (%s, %s)", (result[0],result2[0]))
            db.commit()
            
            return "ACCESS GRANTED. WELCOME TO THE GYM "+result4[0], 200          
           
            
        elif cursor.rowcount >= 1 and today > result3[0]:
            cursor.execute("UPDATE ADHERENT SET Acces = 0 where id = "+str(result[0]))
            db.commit()
            return "ACCESS DENIED. Your subscription ended.", 200
            
            
        else:
            return "User does not exist. Register First.", 200


def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="", flush=True)
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="", flush=True)
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
        return location
        
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True
    
@app.route('/add_fp', methods =['POST'])
def add_fp():	
    
    data = request.get_json()
    name = data["Name"]
    CIN = data["CIN"]
    AdminID = data["admin"]
    sdate = data["sdate"]
    edate = data["edate"]
    Type = "EMPREINTE"
    
    if "Name" in data:
    
        sql_insert= "INSERT INTO ADHERENT (Nom, CIN, admin_id, Date_debut, Date_fin) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_insert, (name, CIN, AdminID, sdate, edate))
        db.commit()

        sql_select = "SELECT id FROM ADHERENT ORDER BY id DESC LIMIT 1"
        cursor.execute(sql_select)
        here=cursor.fetchone()
        k=sum(here)
	

        i=enroll_finger(get_num())
        sql_insert = "INSERT INTO EMPREINTE (adh_id, idfp) VALUES (%s, %s)"
        cursor.execute(sql_insert, (k, i))
        db.commit()
	
        return "User " + name + " saved", 200
    else:
        return "not saved", 400
    
    
def get_num():
	"""Use input() to get a valid number from 1 to 127. Retry till success!"""
	i=0
	k=0
	j=0
	sql_select = "SELECT idfp FROM EMPREINTE ORDER BY id DESC LIMIT 1"
	cursor.execute(sql_select)
	j=cursor.fetchone()
	
	if (j is None):
		i = 1
		return i
	elif int(j[0]) >=1:
		print("here")
		while int(j[0])>=1 and int(j[0])<127:
			i = int(j[0])+1
			print("this i", i)
			return int(i)
            
	
def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_fast_search() != adafruit_fingerprint.OK:
        return False
    return True
        
@app.route('/check_fp', methods =['GET'])
def check_fp():
    while True:
        if get_fingerprint():
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
                cursor.execute("Select ADHERENT.id FROM ADHERENT INNER JOIN EMPREINTE ON ADHERENT.id =EMPREINTE.adh_id WHERE idfp=" + str(finger.finger_id))
                result = cursor.fetchone()
                cursor.execute("Select ADHERENT.Nom FROM ADHERENT INNER JOIN EMPREINTE ON ADHERENT.id =EMPREINTE.adh_id WHERE idfp=" + str(finger.finger_id))
                result2 = cursor.fetchone()
                
                today = date.today()
                cursor.execute("Select ADHERENT.Date_fin FROM ADHERENT INNER JOIN EMPREINTE ON ADHERENT.id = EMPREINTE.adh_id WHERE idfp=" + str(finger.finger_id))
                result3 = cursor.fetchone()
                
                print(cursor.rowcount)
                if cursor.rowcount >= 1 and today < result3[0]:	
                    cursor.execute("UPDATE ADHERENT SET Acces = 1 where id = "+str(result[0]))
                    db.commit()
                    sql_insert = "INSERT INTO PRESENCE (adh_id,Type) VALUES (%s,%s)"
                    cursor.execute(sql_insert, (result[0],'EMPREINTE')) 
                    db.commit()
                    return"ACCESS GRANTED. WELCOME TO THE GYM "+result2[0], 200
                    #return result[0]
                    
                elif cursor.rowcount >= 1 and today > result3[0]:
                    cursor.execute("UPDATE ADHERENT SET Acces = 0 where id = "+str(result[0]))
                    db.commit()
                    return "ACCESS DENIED. Your subscription ended.", 200
                            
                else:
                    return "User does not exist. Register First.", 200 
                
        else:
                return "Finger not found", 400

@app.route('/add_rfid_rfid', methods=['POST'])
def add_rfid_rfid():
		Type2="CARTE"
		print("Place your old card or nfc")
		id, text = reader.read()
		cursor.execute("Select ADHERENT.id FROM ADHERENT INNER JOIN RFID ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
		res = cursor.fetchone()		
		print("-------------------")
		print("Please wait")
		print("Place new card or nfc")
		id2, text = reader.read()
		print("id2", id2)
		sql_insert = "INSERT INTO RFID (adh_id, Type, idrfid) VALUES (%s, %s, %s)"
		cursor.execute(sql_insert, (res[0], Type2, id2))
		db.commit()
		return "NEW RFID added", 200

@app.route('/add_rfid_fp', methods=['POST'])
def add_rfid_rfid():
		Type2="CARTE"
		print("Place your old card or nfc")
		id, text = reader.read()
		cursor.execute("Select ADHERENT.id FROM ADHERENT INNER JOIN RFID ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
		res = cursor.fetchone()		
		print("-------------------")
		print("Please wait")
		print("Place new card or nfc")
		id2, text = reader.read()
		print("id2", id2)
		sql_insert = "INSERT INTO RFID (adh_id, Type, idrfid) VALUES (%s, %s, %s)"
		cursor.execute(sql_insert, (res[0], Type2, id2))
		db.commit()
		return "NEW RFID added", 200

 
if __name__ == '__main__':
    app.run(debug=True)
