#! /usr/bin/env python3

import pathlib
import os
import pymysql.cursors
import datetime
from time import sleep

import OPi.GPIO as GPIO
import orangepi.zero2

from dotenv import load_dotenv

GREEN_PORT = 11
RED_PORT = 13

TIME_TODAY = 2
SIGN_IN_TIME = 1


def init():
    GPIO.setmode(orangepi.zero2.BOARD)
    GPIO.setup(GREEN_PORT, GPIO.OUT)
    GPIO.setup(RED_PORT, GPIO.OUT)
    sleep(1)

    GPIO.output(GREEN_PORT, 1)
    GPIO.output(RED_PORT, 1)
    load_dotenv()

    localUser = os.getenv("user")
    localPassword = os.getenv("password")

    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")

    return connection


def blink_led(sign_in):
    sleepTime = 1.1
    if sign_in:
        port = GREEN_PORT
    else:
        port = RED_PORT
    GPIO.output(port, 0)
    sleep(sleepTime)
    GPIO.output(port, 1)


def sign_in(cursor, ID):
    query = f"INSERT INTO signinsheet (personID, signInTime) VALUES ('{ID}', CURRENT_TIMESTAMP)"
    cursor.execute(query)
    print("Signed in!")
    blink_led(sign_in=True)



def main(connection):
    with connection:
        while True:
            userID = input("What is your id?\n")
            with connection.cursor() as cursor:
                query = f"SELECT * FROM signinsheet WHERE personID = '{userID}' and signInTime = (SELECT max(signInTime) FROM signinsheet WHERE personID='{userID}');"
                cursor.execute(query)
                mostRecentEntry = cursor.fetchone()
            if mostRecentEntry:
                if not mostRecentEntry[TIME_TODAY]:
                    if mostRecentEntry[SIGN_IN_TIME].date() == datetime.datetime.today().date():
                        with connection.cursor() as cursor:
                            timeTodayProc = datetime.datetime.now()-mostRecentEntry[1]
                            timeToday = timeTodayProc.total_seconds()
                            query = f"UPDATE signinsheet SET timeToday = {timeToday} WHERE signInTime = '{mostRecentEntry[SIGN_IN_TIME]}'"
                            cursor.execute(query)
                            print("Signed out!")
                            blink_led(sign_in=False)
                    else:
                        with connection.cursor() as cursor:
                            query = f"UPDATE signinsheet SET timeToday = {60*60*2} WHERE signInTime = '{mostRecentEntry[SIGN_IN_TIME]}'"
                            cursor.execute(query)
                            sign_in(cursor, userID)
                else:
                    with connection.cursor() as cursor:
                        sign_in(cursor, userID)
            else:
                with connection.cursor() as cursor:
                    sign_in(cursor, userID)
            connection.commit()


if __name__ == "__main__":
    connection = init()
    main(connection)
