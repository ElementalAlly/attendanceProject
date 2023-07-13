import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .library.helpers import openfile
import pymysql.cursors
import datetime
import csv
import io

from dotenv import load_dotenv
load_dotenv()

LOCAL_USER = os.getenv("user")
LOCAL_PASSWORD = os.getenv("password")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def calc_date(date1, date2):
    now = datetime.datetime.now()
    if not date1:
        if now.month < 6:
            date1 = f"{now.year-1}-06-01 00:00:00"
        else:
            date1 = f"{now.year}-06-01 00:00:00"
    if not date2:
        date2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (date1, date2)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    data["currentPage"] = "home"
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})


@app.post("/registerPost", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), user_id: str = Form(...)):
    your_name = name
    your_id = user_id
    if not your_id:
        return templates.TemplateResponse('register.html', context={"request": request, "error": "Please input an ID."})
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT memberName FROM registry WHERE personID = '{your_id}'"
            cursor.execute(query)
            if cursor.fetchone():
                return templates.TemplateResponse('register.html', context={"request": request, "error": "ID already taken."})
            query = f"SELECT personID FROM registry WHERE memberName = '{your_name}'"
            cursor.execute(query)
            if cursor.fetchone():
                return templates.TemplateResponse('register.html', context={"request": request, "error": "Name already taken."})
            query = f"INSERT INTO registry VALUES ('{your_id}', '{your_name}');"
            cursor.execute(query)
        connection.commit()
    return templates.TemplateResponse('register.html', context={"request": request, "your_name": your_name, "your_id": your_id})


@app.get("/reports", response_class=HTMLResponse)
def reports_get(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.post("/reportPost", response_class=HTMLResponse)
def reports_post(request: Request, identification: str = Form(...), from_date: str = Form(...), to_date: str = Form(...)):
    sign_in_time_ind = 1
    time_today_ind = 0
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT personID FROM registry WHERE memberName = '{identification}'"
            cursor.execute(query)
            user_id = cursor.fetchone()
            if user_id:
                user_id = user_id[0]
                name = identification
            else:
                user_id = identification
                query = f"SELECT memberName FROM registry WHERE personID = '{user_id}'"
                cursor.execute(query)
                name = cursor.fetchone()
                if name:
                    name = name[0]
            if from_date != "0000-00-00":
                from_date = from_date + " 00:00:00"
            else:
                now = datetime.datetime.now()
                if now.month < 6:
                    from_date = f"{now.year-1}-06-01 00:00:00"
                else:
                    from_date = f"{now.year}-06-01 00:00:00"
            if to_date != "0000-00-00":
                to_date = to_date + " 23:59:59"
            else:
                to_date = datetime.datetime.now()
                to_date = to_date.strftime("%Y-%m-%d %H:%M:%S")
            query = f"SELECT timeToday, signInTime FROM signinsheet WHERE personID = '{user_id}' AND signInTime > '{from_date}' AND signInTime < '{to_date}'"
            cursor.execute(query)
            allEntries = cursor.fetchall()
    total_time = 0
    all_times = []
    all_dates = []
    for entry in allEntries:
        all_dates.append(entry[sign_in_time_ind].strftime("%Y-%m-%d"))
        all_times.append(entry[time_today_ind]/3600)
        total_time += entry[time_today_ind]/3600
    if name:
        report = f"Hello {name}, your ID is {user_id} and you've spent {total_time} hours from {from_date[0:10]} to {to_date[0:10]} in robotics this season!"
    else:
        report = f"Your ID is {user_id} and you've spent {total_time} hours from {from_date[0:10]} to {to_date[0:10]} in robotics this season! (btw, you don't have a name registered to your ID, you may want to visit the register page here :) )"
    return templates.TemplateResponse('reports.html', context={"request": request, "report": report, "dateValues": all_dates, "timeValues": all_times, "titleValue": f"Report from {from_date[0:10]} to {to_date[0:10]} for {user_id}:"})


@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    return templates.TemplateResponse('adminHome.html', context={"request": request})


@app.get("/admin/report", response_class=HTMLResponse)
async def admin_report(request: Request):
    name_ind = 0
    id_ind = 1
    sign_in_time_ind = 2
    time_today_ind = 3
    from_date, to_date = calc_date(None, None)
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    data = {}
    with connection:
        with connection.cursor() as cursor:
            query = f"""SELECT
            registry.memberName,
            signinsheet.personID,
            signinsheet.signInTime,
            signinsheet.timeToday
            FROM
            signinsheet
            INNER JOIN registry USING(personID)
            WHERE signInTime > '{from_date}' AND signInTime < '{to_date}'
            ORDER BY signInTime;"""
            cursor.execute(query)
            for row in cursor:
                try:
                    data[(row[name_ind], row[id_ind])].append([row[sign_in_time_ind], row[time_today_ind]/3600])
                    data[(row[name_ind], row[id_ind])][0] += row[time_today_ind]/3600
                except KeyError:
                    data[(row[name_ind], row[id_ind])] = [0]
                    data[(row[name_ind], row[id_ind])].append([row[sign_in_time_ind], row[time_today_ind]/3600])
                    data[(row[name_ind], row[id_ind])][0] += row[time_today_ind]/3600
    return templates.TemplateResponse('adminReports.html', context={"request": request, "data": data})


@app.get("/admin/csv", response_class=StreamingResponse)
async def admin_csv(request: Request):
    data = []
    id_ind = 0
    name_ind = 1
    from_date, to_date = calc_date(None, None)
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = "SELECT memberName, personID FROM registry;"
            cursor.execute(query)
            registry = cursor.fetchall()
            query = f"""SELECT
            registry.memberName,
            signinsheet.personID,
            signinsheet.signInTime,
            signinsheet.timeToday
            FROM
            signinsheet
            LEFT JOIN registry USING(personID)
            WHERE signInTime > '{from_date}' AND signInTime < '{to_date}'
            ORDER BY signInTime;"""
            cursor.execute(query)
            data = list(cursor.fetchall())
            data.append([None, None, None, None])
            data.append(["Registered ID", "Registered Name", None, None])
            for i in range(len(registry)):
                data.append([registry[i][id_ind], registry[i][name_ind], None, None])
    data_stream = io.StringIO()
    report = csv.writer(data_stream)
    for row in data:
        report.writerow(row)
    response = StreamingResponse(iter([data_stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={from_date[0:4]}-{int(from_date[0:4]) + 1}SeasonalAttendanceReport.csv"
    return response
