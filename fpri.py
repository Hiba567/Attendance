# !/usr/bin/env python
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import time
import RPi.GPIO as GPIO
from datetime import date
from datetime import datetime
from mfrc522 import SimpleMFRC522
import mysql.connector


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


    	               


