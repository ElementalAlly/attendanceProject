import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .library.helpers import openfile
import pymysql.cursors

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
def register_post(request: Request, name: str = Form(...), ID: int = Form(...)):
    yourname = name
    yourID = ID
    if yourID != 0:
        connection = pymysql.connect(host="localhost",
                                     user=localUser,
                                     password=localPassword,
                                     database="attendancedb")
        with connection:
            with connection.cursor() as cursor:
                query = f"INSERT INTO registry VALUES ({yourID}, '{yourname}');"
                print(query)
                cursor.execute(query)
            connection.commit()
        return templates.TemplateResponse('register.html', context={"request": request, "yourname": yourname, "yourID": yourID})
    return templates.TemplateResponse('register.html', context={"request": request, "error": "Please input a valid ID."})


@app.get("/reports", response_class=HTMLResponse)
def reports_get(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.post("/reportNamePost", response_class=HTMLResponse)
def reports_name_post(request: Request, name: str = Form(...)):
    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT personID FROM registry WHERE memberName = '{name}';"
            cursor.execute(query)
            ID = cursor.fetchone()[0]
            query = f"SELECT timeToday FROM signInSheet WHERE personID = {ID};"
            cursor.execute(query)
            allTimes = cursor.fetchall()
    totalTime = 0
    for time in allTimes:
        totalTime += time[0]
    totalTime = totalTime / 3600
    report = f"Hello {name}, your ID is {ID} and you've spent {totalTime} in robotics this season!"
    return templates.TemplateResponse('reports.html', context={"request": request, "report": report})


@app.post("/reportIDPost", response_class=HTMLResponse)
def reports_ID_post(request: Request, ID: int = Form(...)):
    connection = pymysql.connect(host="localhost",
                                 user=localUser,
                                 password=localPassword,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT timeToday FROM signInSheet WHERE personID = {ID};"
            cursor.execute(query)
            allTimes = cursor.fetchall()
    print(allTimes)
    totalTime = 0
    for time in allTimes:
        totalTime += time[0]
    print(totalTime)
    totalTime = totalTime / 3600
    report = f"You've spent {totalTime} hours in robotics this season."
    return templates.TemplateResponse('reports.html', context={"request": request, "report": report})
