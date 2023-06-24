import os
import pymysql.cursors
import datetime
import subprocess

from dotenv import load_dotenv
load_dotenv()

localUser = os.getenv("user")
localPassword = os.getenv("password")

subprocess.Popen(["uvicorn", "app.main:app", "--reload", "--port", "80"])

connection = pymysql.connect(host="localhost",
                             user=localUser,
                             password=localPassword,
                             database="attendancedb")

with connection:
    while True:
        userID = input("What is your id?\n")
        with connection.cursor() as cursor:
            query = f"SELECT * FROM signInSheet WHERE personID = {userID} and signInTime = (SELECT max(signInTime) FROM signInSheet WHERE personID={userID});"
            cursor.execute(query)
            mostRecentEntry = cursor.fetchone()
        if mostRecentEntry:
            if not mostRecentEntry[2]:
                if mostRecentEntry[1].date() == datetime.datetime.today().date():
                    with connection.cursor() as cursor:
                        timeTodayProc = datetime.datetime.now()-mostRecentEntry[1]
                        timeToday = timeTodayProc.total_seconds()
                        query = f"UPDATE signInSheet SET timeToday = {timeToday} WHERE signInTime = '{mostRecentEntry[1]}'"
                        cursor.execute(query)
                        print("Signed out!")
                else:
                    with connection.cursor() as cursor:
                        query = f"UPDATE signInSheet SET timeToday = {60*60*2} WHERE signInTime = '{mostRecentEntry[1]}'"
                        cursor.execute(query)
                        query = f"INSERT INTO signInSheet (personID, signInTime) VALUES ({userID}, CURRENT_TIMESTAMP)"
                        cursor.execute(query)
                        print("Signed in! (time yesterday reset to 2 hrs)")
            else:
                with connection.cursor() as cursor:
                    query = f"INSERT INTO signInSheet (personID, signInTime) VALUES ({userID}, CURRENT_TIMESTAMP)"
                    cursor.execute(query)
                    print("Signed in!")
        else:
            with connection.cursor() as cursor:
                query = f"INSERT INTO signInSheet (personID, signInTime) VALUES ({userID}, CURRENT_TIMESTAMP)"
                cursor.execute(query)
                print("Signed in!")
        connection.commit()
