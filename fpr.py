# !/usr/bin/env python
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import time
import RPi.GPIO as GPIO
from datetime import date
from datetime import datetime
from mfrc522 import SimpleMFRC522
import mysql.connector

db = mysql.connector.connect(
    host="",
    user="",
    passwd="",
    database=""
)


# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
import serial
uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

cursor = db.cursor()
reader = SimpleMFRC522()
	
cursor = db.cursor(buffered=True)	
	
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
			
		
		
    #if finger.read_templates() != adafruit_fingerprint.OK:
       #raise RuntimeError("Failed to read templates")
       
    #print("Fingerprint templates:", finger.templates)
    #i = 0
    #while (i > 127) or (i < 1):
        #try:
            #i = int(input("Enter ID # from 1-127: "))
            
        #except ValueError:
            #pass

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

def register_fp():	
		
	print("-----------------")
    
	print('Enter Name of new user')
	name = input("Name: ")

	print("Enter CIN")
	CIN = input("CIN:")

	print("Enter Admin ID")
	AdminID = input("Admin ID:")

	print("Enter Start Date")
	date_entry = input('Enter a date (i.e. 2022,7,1)')
	year, month, day = map(int, date_entry.split(','))
	sdate = datetime(year, month, day)

	print("Enter End Date")
	date_entry = input('Enter a date (i.e. 2022,7,1)')
	year, month, day = map(int, date_entry.split(','))
	edate = datetime(year, month, day)

	sql_insert= "INSERT INTO ADHERENT (Nom, CIN, admin_id, Date_debut, Date_fin) VALUES (%s, %s, %s, %s, %s)"
	cursor.execute(sql_insert, (name, CIN, AdminID, sdate, edate))
	db.commit()

	#print("USER ID")
	sql_select = "SELECT id FROM ADHERENT ORDER BY id DESC LIMIT 1"
	cursor.execute(sql_select)
	here=cursor.fetchone()
	k=sum(here)
	#print(k)
	
	print("enrollement")
	i=enroll_finger(get_num())
	sql_insert = "INSERT INTO EMPREINTE (adh_id, idfp) VALUES (%s, %s)"
	cursor.execute(sql_insert, (k, i))
	db.commit()
	
	print("User" + name + "saved")
	
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
			
def check_fp():
	
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
				print("ACCESS GRANTED. WELCOME TO THE GYM "+result2[0])
				return result[0]
			elif cursor.rowcount >= 1 and today > result3[0]:
				cursor.execute("UPDATE ADHERENT SET Acces = 0 where id = "+str(result[0]))
				db.commit()
				print("ACCESS DENIED. Your subscription ended.")
			            
			else:
				print("User does not exist. Register First.")     
			
	else:
            print("Finger not found")
	               
	               
def add_fp():
	
	print("Do you have an RFID or FINGERPRINT?")
	ans=input(">")
	if ans == "RFID":
		print("Place your old card or nfc")
		id, text = reader.read()
		cursor.execute("Select ADHERENT.id FROM ADHERENT INNER JOIN RFID ON ADHERENT.id = RFID.adh_id WHERE idrfid=" + str(id))
		res = cursor.fetchone()
		print("Please wait")
		i=enroll_finger(get_num())	
		sql_insert = "INSERT INTO EMPREINTE (adh_id, idfp) VALUES (%s, %s)"
		cursor.execute(sql_insert, (res[0], i))
		db.commit()
		print("New Fingerprint added")
	else:
		print("Please enter your old fingerprint")
		x=check_fp()
		print("-------------------")
		print("Please wait")
		i=enroll_finger(get_num())	
		sql_insert = "INSERT INTO EMPREINTE (adh_id, idfp) VALUES (%s, %s)"
		cursor.execute(sql_insert, (x, i))
		db.commit()
		print("New Fingerprint added")
    	               


