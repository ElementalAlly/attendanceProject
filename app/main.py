import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .library.helpers import openfile
import pymysql.cursors
import datetime
import numpy
import pandas
import io

from dotenv import load_dotenv
load_dotenv()

localUser = os.getenv("user")
localPassword = os.getenv("password")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    data["currentPage"] = "home"
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})


@app.post("/registerPost", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), ID: str = Form(...)):
    yourname = name
    yourID = ID
    if yourID:
        connection = pymysql.connect(host="localhost",
                                     user=localUser,
                                     password=localPassword,
                                     database="attendancedb")
        with connection:
            with connection.cursor() as cursor:
                query = f"SELECT memberName FROM registry WHERE personID = '{yourID}'"
                cursor.execute(query)
                if cursor.fetchone():
                    return templates.TemplateResponse('register.html', context={"request": request, "error": "ID already taken."})
                query = f"SELECT personID FROM registry WHERE memberName = '{yourname}'"
                cursor.execute(query)
                if cursor.fetchone():
                    return templates.TemplateResponse('register.html', context={"request": request, "error": "Name already taken."})
                query = f"INSERT INTO registry VALUES ('{yourID}', '{yourname}');"
                cursor.execute(query)
            connection.commit()
        return templates.TemplateResponse('register.html', context={"request": request, "yourname": yourname, "yourID": yourID})
    return templates.TemplateResponse('register.html', context={"request": request, "error": "Please input an ID."})


@app.get("/reports", response_class=HTMLResponse)
def reports_get(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.post("/reportPost", response_class=HTMLResponse)
def reports_post(request: Request, identification: str = Form(...), fromDate: str = Form(...), toDate: str = Form(...)):
    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT personID FROM registry WHERE memberName = '{identification}'"
            cursor.execute(query)
            ID = cursor.fetchone()
            if ID:
                ID = ID[0]
                name = identification
            else:
                ID = identification
                query = f"SELECT memberName FROM registry WHERE personID = '{ID}'"
                cursor.execute(query)
                name = cursor.fetchone()
                if name:
                    name = name[0]
            if fromDate != "0000-00-00":
                fromDate = fromDate + " 00:00:00"
            else:
                now = datetime.datetime.now()
                if now.month < 6:
                    fromDate = f"{now.year-1}-06-01 00:00:00"
                else:
                    fromDate = f"{now.year}-06-01 00:00:00"
            if toDate != "0000-00-00":
                toDate = toDate + " 23:59:59"
            else:
                toDate = datetime.datetime.now()
                toDate = toDate.strftime("%Y-%m-%d %H:%M:%S")
            query = f"SELECT timeToday, signInTime FROM signinsheet WHERE personID = '{ID}' AND signInTime > '{fromDate}' AND signInTime < '{toDate}'"
            cursor.execute(query)
            allEntries = cursor.fetchall()
    totalTime = 0
    allTimes = []
    allDates = []
    for entry in allEntries:
        allDates.append(entry[1].strftime("%Y-%m-%d"))
        allTimes.append(entry[0]/3600)
        totalTime += entry[0]/3600
    if name:
        report = f"Hello {name}, your ID is {ID} and you've spent {totalTime} hours from {fromDate[0:10]} to {toDate[0:10]} in robotics this season!"
    else:
        report = f"Your ID is {ID} and you've spent {totalTime} hours from {fromDate[0:10]} to {toDate[0:10]} in robotics this season! (btw, you don't have a name registered to your ID, you may want to visit the register page here :) )"
    return templates.TemplateResponse('reports.html', context={"request": request, "report": report, "dateValues": allDates, "timeValues": allTimes, "titleValue": f"Report from {fromDate[0:10]} to {toDate[0:10]} for {ID}:"})


@app.get("/admin", response_class=HTMLResponse)
async def adminHome(request: Request):
    return templates.TemplateResponse('adminHome.html', context={"request": request})


@app.get("/admin/report", response_class=HTMLResponse)
async def adminReport(
    request: Request,
    fromDate: str = None,
    toDate: str = None
):
    data = []
    now = datetime.datetime.now()
    if not fromDate:
        if now.month < 6:
            fromDate = f"{now.year-1}-06-01 00:00:00"
        else:
            fromDate = f"{now.year}-06-01 00:00:00"
    if not toDate:
        toDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = "SELECT * FROM registry;"
            cursor.execute(query)
            allNames = cursor.fetchall()
            for name in allNames:
                data.append([name[0], name[1], 0])
            for i in range(len(data)):
                query = f"SELECT * FROM signinsheet WHERE personID = '{data[i][0]}' AND signInTime > '{fromDate}' AND signInTime < '{toDate}'"
                cursor.execute(query)
                personData = cursor.fetchall()
                for entry in personData:
                    data[i].append([entry[1], entry[2]/3600])
                    data[i][2] += entry[2]
                data[i][2] /= 3600
    return templates.TemplateResponse('adminReports.html', context={"request": request, "data": data})


@app.get("/admin/csv", response_class=StreamingResponse)
async def adminCSV(
    request: Request,
    fromDate: str = None,
    toDate: str = None
):
    data = []
    idsIndices = {}
    now = datetime.datetime.now()
    if not fromDate:
        if now.month < 6:
            fromDate = f"{now.year-1}-06-01 00:00:00"
        else:
            fromDate = f"{now.year}-06-01 00:00:00"
    if not toDate:
        toDate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = "SELECT * FROM registry;"
            cursor.execute(query)
            registry = cursor.fetchall()
            for i in range(len(registry)):
                idsIndices[registry[i][0]] = i
            query = f"SELECT * FROM signinsheet WHERE signInTime > '{fromDate}' AND signInTime < '{toDate}'"
            cursor.execute(query)
            signIns = cursor.fetchall()
            for i in range(len(signIns)):
                data.append([None, None, None, None])
                data[i][1] = signIns[i][0]
                data[i][2] = signIns[i][1]
                data[i][3] = signIns[i][2]
                try:
                    data[i][0] = registry[idsIndices[data[i][1]]][1]
                except KeyError:
                    pass
            data.append([None, None, None, None])
            data.append(["Registered ID", "Registered Name", None, None])
            for i in range(len(registry)):
                data.append([registry[i][0], registry[i][1], None, None])
    dataFrame = numpy.asarray(data)
    dataStream = io.StringIO()
    pandas.DataFrame(dataFrame).to_csv(dataStream, index=False, header=["Name", "ID", "Time of sign in", "Time spent (secs)"])
    response = StreamingResponse(iter([dataStream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={fromDate[0:4]}-{int(fromDate[0:4]) + 1}SeasonalAttendanceReport.csv"
    return response
