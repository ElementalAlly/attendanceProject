import pymysql.cursors
import datetime
import subprocess

subprocess.Popen(["uvicorn", "app.main:app", "--reload", "--port", "80"])

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="NBzfFJ#k4$DYHbV94i*7",
                             database="attendancedb")

with connection:
    while True:
        userID = input("What is your id?\n")
        with connection.cursor() as cursor:
            query = f"SELECT * FROM signInSheet WHERE personID = {userID} and signInTime = (SELECT max(signInTime) FROM signInSheet WHERE personID={userID});"
            print(query)
            cursor.execute(query)
            mostRecentEntry = cursor.fetchone()
        print(mostRecentEntry)
        if mostRecentEntry:
            if not mostRecentEntry[2]:
                print(mostRecentEntry[1].date())
                print(datetime.datetime.today().date())
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
        print(query)
        connection.commit()
