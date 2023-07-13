#! /usr/bin/env python3

import datetime
import os
import pathlib
from time import sleep
from unittest.mock import Mock

import pymysql.cursors
from dotenv import load_dotenv

try:
    import OPi.GPIO as GPIO
    import orangepi.zero2
except ModuleNotFoundError:
    GPIO = Mock()
    orangepi = Mock()


GREEN_PORT = 11
RED_PORT = 13

SCRIPT_DIR = pathlib.Path(__file__).parent


def init():
    GPIO.setmode(orangepi.zero2.BOARD)
    GPIO.setup(GREEN_PORT, GPIO.OUT)
    GPIO.setup(RED_PORT, GPIO.OUT)
    sleep(1)

    GPIO.output(GREEN_PORT, 1)
    GPIO.output(RED_PORT, 1)
    load_dotenv(SCRIPT_DIR/".env")

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


def sign_out(cursor, sign_in_time, delta_time=None):
    if not delta_time:
        time_today_proc = datetime.datetime.now()-sign_in_time
        delta_time = time_today_proc.total_seconds()
    query = f"UPDATE signinsheet SET timeToday = {delta_time} WHERE signInTime = '{sign_in_time}'"
    cursor.execute(query)
    print("Signed out!")


def main():
    connection = init()
    time_today_ind = 2
    sign_in_time_ind = 1
    with connection:
        while True:
            userID = input("What is your id?\n")
            with connection.cursor() as cursor:
                query = f"SELECT * FROM signinsheet WHERE personID = '{userID}' and signInTime = (SELECT max(signInTime) FROM signinsheet WHERE personID='{userID}');"
                cursor.execute(query)
                most_recent_entry = cursor.fetchone()
                if most_recent_entry and not most_recent_entry[time_today_ind]:
                    if most_recent_entry[sign_in_time_ind].date() == datetime.datetime.today().date():
                        sign_out(cursor, most_recent_entry[sign_in_time_ind])
                        blink_led(sign_in=False)
                    else:
                        sign_out(cursor, most_recent_entry[sign_in_time_ind], 60*60*2)
                        sign_in(cursor, userID)
                        blink_led(sign_in=True)
                else:
                    sign_in(cursor, userID)
                    blink_led(sign_in=True)
            connection.commit()


if __name__ == "__main__":
    main()
