# !/usr/bin/env python
from concurrent.futures import wait, FIRST_COMPLETED
from pebble import ProcessPool
from fp import *
from rfid import *
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

cursor = db.cursor()
reader = SimpleMFRC522()

def register_admin():
	print("Enter Admin name")
	ANAME = input("Admin name:")

	print("Enter Admin cin")
	ACIN = input("Admin cin:")

	sql_insert = "INSERT INTO ADMINISTRATEUR (NOM, CIN) VALUES (%s, %s)"
	cursor.execute(sql_insert, (ANAME, ACIN))
	db.commit()
	print("ADMIN ADDED")
	
while True:
	print("-------------------------------")
	print("Choose an option:")   
	print("a RFID registration")
	print("b FINGERPRINT registration")
	print("c Attendance check")
	print("d Admin registration")
	print("e Add card, nfc, or fingerprint")
	print("f Quit")
	print("-------------------------------")

	c = input("> ")

	if c == "a":
		register_rfid()
		
	elif c == "b":
		register_fp()

	elif c == "c":
		
	    with ProcessPool(max_workers=2) as pool:
             f1 = pool.schedule(check_rfid)
             f2 = pool.schedule(check_fp)
             done, not_done = wait((f1, f2), return_when=FIRST_COMPLETED)
             for f in not_done:
                 f.cancel()
		
	elif c =="d":
		register_admin()

	elif c=="e":
		print("Do you want to add RFID OR FINGERPRINT")
		answer = input("choice:")
		if answer == "RFID":
			add_rfid()
		else:
			add_fp()
        
	elif c=="f":
		print("GoodBye")
		quit()
		
	else:
		print("Invalid choice")

