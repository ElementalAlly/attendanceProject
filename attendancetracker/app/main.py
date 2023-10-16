import os
from fastapi import Cookie, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .library.helpers import openfile
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pymysql.cursors
import datetime
import csv
import io
import pathlib
import qrcode

from dotenv import load_dotenv
load_dotenv()

LOCAL_USER = os.getenv("user")
LOCAL_PASSWORD = os.getenv("password")
ADMIN_PASSWORD = os.getenv("admin")

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
def home_get(request: Request):
    today = datetime.datetime.now()
    today = today.strftime("%Y-%m-%d")
    name_ind = 0
    role_ind = 1
    id_ind = 2
    sign_in_time_ind = 3
    time_today_ind = 4
    data = []
    mentors = []
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"""SELECT
            registry.memberName,
            registry.mentor,
            signinsheet.personID,
            signinsheet.signInTime,
            signinsheet.timeToday
            FROM
            signinsheet
            LEFT JOIN registry USING(personID)
            WHERE DATE(signInTime) = '{today}'
            ORDER BY signInTime;"""
            cursor.execute(query)
            raw_data = list(cursor.fetchall())
    for entry in raw_data:
        if entry[time_today_ind]:
            signed_out = "yes"
        else:
            signed_out = "no"
        data.append([entry[name_ind], entry[id_ind], entry[sign_in_time_ind].strftime("%H:%M:%S"), signed_out])
        if entry[role_ind]:
            mentors.append(entry[name_ind])
    mentors = list(dict.fromkeys(mentors))
    return templates.TemplateResponse("home.html", {"request": request, "data": data, "mentors": mentors, "today": today})


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})


@app.post("/registerPost", response_class=HTMLResponse)
def register_post(request: Request, name: str = Form(...), user_id: str = Form(...), mentor: bool = Form(False)):
    your_name = name
    your_id = user_id
    is_mentor = mentor
    if is_mentor:
        role = "mentor"
    else:
        role = "student"
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
            query = f"INSERT INTO registry VALUES ('{your_id}', '{your_name}', {is_mentor});"
            cursor.execute(query)
        connection.commit()
    return templates.TemplateResponse('register.html', context={"request": request, "your_name": your_name, "your_id": your_id, "your_role": role})


@app.get("/reports", response_class=HTMLResponse)
def reports_get(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})


@app.post("/reportPost", response_class=HTMLResponse)
def reports_post(request: Request, identification: str = Form(...), from_date: str = Form(...), to_date: str = Form(...)):
    sign_in_time_ind = 1
    time_today_ind = 0
    id_ind = 0
    role_ind = 1
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"SELECT personID, mentor FROM registry WHERE memberName = '{identification}'"
            cursor.execute(query)
            entry = cursor.fetchone()
            if entry:
                user_id = entry[id_ind]
                name = identification
                if entry[role_ind]:
                    role = "mentor"
                else:
                    role = "student"
            else:
                user_id = identification
                query = f"SELECT memberName FROM registry WHERE personID = '{user_id}'"
                cursor.execute(query)
                name = cursor.fetchone()
                if name:
                    name = name[id_ind]
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
        if entry[time_today_ind]:
            all_times.append(entry[time_today_ind]/3600)
            total_time += entry[time_today_ind]/3600
    if name:
        report = f"Hello {name}, your ID is {user_id}, your role is {role}, and you've spent {total_time} hours from {from_date[0:10]} to {to_date[0:10]} in robotics this season!"
    else:
        report = f"Your ID is {user_id} and you've spent {total_time} hours from {from_date[0:10]} to {to_date[0:10]} in robotics this season! (btw, you don't have a name registered to your ID, you may want to visit the register page here :) )"
    return templates.TemplateResponse('reports.html', context={"request": request, "report": report, "dateValues": all_dates, "timeValues": all_times, "titleValue": f"Report from {from_date[0:10]} to {to_date[0:10]} for {user_id}:"})


@app.get("/qr", response_class=HTMLResponse)
def make_qr(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})


@app.post("/qrPost", response_class=StreamingResponse)
def make_qr(request: Request, qrtext: str = Form(...)):
    # This is modified from https://www.geeksforgeeks.org/how-to-generate-qr-codes-with-a-custom-logo-using-python/
    logo_path = pathlib.Path(__file__).parent / "logo.jpg"
    logo = Image.open(str(logo_path))

    basewidth = 80
    wpercent = (basewidth/float(logo.size[0]))
    hsize = int((float(logo.size[1])*float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.LANCZOS)
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr.add_data(qrtext)
    qr.make()
    qr_img = qr.make_image().convert('RGB')
    pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos)

    data_stream = io.BytesIO()
    qr_img.save(data_stream, format="JPEG")

    response = StreamingResponse(iter([data_stream.getvalue()]), media_type="image/jpeg")
    response.headers["Content-Disposition"] = "attachment; filename=qrcode.jpg"
    return response


def _check_admin_credential(credentials):
    return credentials == ADMIN_PASSWORD


@app.post("/adminLogin", response_class=HTMLResponse)
def admin_login(request: Request, password: str = Form(...)):
    response = templates.TemplateResponse('adminRedirect.html', context={"request": request})
    response.set_cookie(key="admin", value=password)
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})
    return templates.TemplateResponse('adminHome.html', context={"request": request})


@app.get("/admin/report", response_class=HTMLResponse)
async def admin_report(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})
    name_ind = 0
    role_id = 1
    id_ind = 2
    sign_in_time_ind = 3
    time_today_ind = 4
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
            registry.mentor,
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
                role = "student"
                if row[role_id]:
                    role = "mentor"
                if row[time_today_ind]:
                    try:
                        data[(row[name_ind], row[id_ind], role)].append([row[sign_in_time_ind], row[time_today_ind]/3600])
                        data[(row[name_ind], row[id_ind], role)][0] += row[time_today_ind]/3600
                    except KeyError:
                        data[(row[name_ind], row[id_ind], role)] = [0]
                        data[(row[name_ind], row[id_ind], role)].append([row[sign_in_time_ind], row[time_today_ind]/3600])
                        data[(row[name_ind], row[id_ind], role)][0] += row[time_today_ind]/3600
    return templates.TemplateResponse('adminReports.html', context={"request": request, "data": data})


@app.get("/admin/csv", response_class=StreamingResponse)
async def admin_csv(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})
    data = []
    total_times = {}
    id_ind = 1
    name_ind = 0
    role_id = 2
    sign_in_time_ind = 2
    time_today_ind = 3
    from_date, to_date = calc_date(None, None)
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = "SELECT memberName, personID, mentor FROM registry;"
            cursor.execute(query)
            registry = cursor.fetchall()
            for entry in registry:
                total_times[entry[id_ind]] = 0
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
            raw_data = list(cursor.fetchall())
            for i in range(len(raw_data)):
                data.append((raw_data[i][name_ind], raw_data[i][id_ind], raw_data[i][sign_in_time_ind].strftime("%m/%d/%Y"), raw_data[i][sign_in_time_ind].strftime("%H:%M:%S"), raw_data[i][time_today_ind] / 60))
                try:
                    total_times[raw_data[i][id_ind]] += raw_data[i][time_today_ind]
                except KeyError:
                    total_times[raw_data[i][id_ind]] = raw_data[i][time_today_ind]
            data.append([None, None, None, None, None])
            data.append(["Registered ID", "Registered Name", "Total Time", "Role", None])
            for i in range(len(registry)):
                role = "student"
                if registry[i][role_id]:
                    role = "mentor"
                data.append([registry[i][id_ind], registry[i][name_ind], total_times[registry[i][id_ind]], role, None])
    data_stream = io.StringIO()
    report = csv.writer(data_stream)
    for row in data:
        report.writerow(row)
    response = StreamingResponse(iter([data_stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={from_date[0:4]}-{int(from_date[0:4]) + 1}SeasonalAttendanceReport.csv"
    return response


@app.get("/admin/signInSheet", response_class=HTMLResponse)
def admin_sign_in_get(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})
    return templates.TemplateResponse('adminSignInSheet.html', context={"request": request})


@app.post("/admin/signInPost", response_class=HTMLResponse)
def admin_sign_in_post(request: Request, date: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})
    name_ind = 0
    role_ind = 1
    id_ind = 2
    sign_in_time_ind = 3
    time_today_ind = 4
    data = []
    mentors = []
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"""SELECT
            registry.memberName,
            registry.mentor,
            signinsheet.personID,
            signinsheet.signInTime,
            signinsheet.timeToday
            FROM
            signinsheet
            LEFT JOIN registry USING(personID)
            WHERE DATE(signInTime) = '{date}'
            ORDER BY signInTime;"""
            cursor.execute(query)
            raw_data = list(cursor.fetchall())
    for entry in raw_data:
        if entry[time_today_ind]:
            signed_out = "yes"
        else:
            signed_out = "no"
        data.append([entry[name_ind], entry[id_ind], entry[sign_in_time_ind].strftime("%H:%M:%S"), signed_out])
        if entry[role_ind]:
            mentors.append(entry[name_ind])
    mentors = list(dict.fromkeys(mentors))
    return templates.TemplateResponse("adminSignInSheet.html", {"request": request, "data": data, "mentors": mentors, "given_date": date})


def _edit_users_page(request, connection):
    with connection.cursor() as cursor:
        query = "SELECT * FROM registry;"
        cursor.execute(query)
        users = list(cursor.fetchall())
    return templates.TemplateResponse('adminEditUsers.html', context={"request": request, "users": users})


@app.get("/admin/editUsers", response_class=HTMLResponse)
def admin_edit_users(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        return _edit_users_page(request, connection)


@app.post("/admin/editUsersEditPost", response_class=HTMLResponse)
def admin_edit_users_edit_post(request: Request, user_id: str = Form(...), name: str = Form(...), mentor: bool = Form(False)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"""UPDATE registry
            SET memberName = '{name}', mentor = {mentor}
            WHERE personID = '{user_id}';"""
            cursor.execute(query)
        connection.commit()
        return _edit_users_page(request, connection)


@app.post("/admin/editUsersDeletePost", response_class=HTMLResponse)
def admin_edit_users_delete_post(request: Request, user_id: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"DELETE FROM registry WHERE personID = '{user_id}';"
            cursor.execute(query)
        connection.commit()
        return _edit_users_page(request, connection)


@app.post("/admin/editUsersAddPost", response_class=HTMLResponse)
def admin_edit_users_add_post(request: Request, user_id: str = Form(...), name: str = Form(...), mentor: bool = Form(False)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"INSERT INTO registry VALUES ('{user_id}', '{name}', {mentor});"
            cursor.execute(query)
        connection.commit()
        return _edit_users_page(request, connection)


@app.get("/admin/editSignIn", response_class=HTMLResponse)
def admin_edit_sign_in(request: Request):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    return templates.TemplateResponse("adminEditSignIn.html", context={"request": request})


def _edit_sign_in_sheet(request, connection, date):
    sign_in_time_ind = 4
    time_today_ind = 5
    the_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    data = []
    with connection.cursor() as cursor:
        query = f"""SELECT
        registry.memberName,
        registry.mentor,
        signinsheet.entryID,
        signinsheet.personID,
        signinsheet.signInTime,
        signinsheet.timeToday
        FROM
        signinsheet
        LEFT JOIN registry USING(personID)
        WHERE DATE(signInTime) = '{the_date}'
        ORDER BY signInTime;"""
        cursor.execute(query)
        raw_data = list(cursor.fetchall())
    for row in raw_data:
        entry = list(row)
        entry[sign_in_time_ind] = row[sign_in_time_ind].strftime("%H:%M:%S")
        entry[time_today_ind] = round(row[time_today_ind] / 60, 2)
        data.append(entry)
    return templates.TemplateResponse('adminEditSignInSheet.html', context={"request": request, "date": date, "data": data})


@app.post("/admin/editSignInSheet", response_class=HTMLResponse)
def admin_edit_sign_in_sheet(request: Request, date: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        return _edit_sign_in_sheet(request, connection, date)


@app.post("/admin/editSignInSheetEditPost", response_class=HTMLResponse)
def admin_edit_sign_in_sheet_edit_post(request: Request, date: str = Form(...), entry_id: str = Form(...), time: str = Form(...), minutes: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    timestamp = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    seconds = int(float(minutes) * 60)
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"""UPDATE signinsheet
            SET signInTime = '{timestamp}', timeToday = {seconds}
            WHERE entryID = '{entry_id}';"""
            cursor.execute(query)
        connection.commit()
        return _edit_sign_in_sheet(request, connection, date)


@app.post("/admin/editSignInSheetDeletePost", response_class=HTMLResponse)
def admin_edit_sign_in_sheet_delete_post(request: Request, date: str = Form(...), entry_id: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"DELETE FROM signinsheet WHERE entryID = '{entry_id}';"
            cursor.execute(query)
        connection.commit()
        return _edit_sign_in_sheet(request, connection, date)


@app.post("/admin/editSignInSheetAddPost", response_class=HTMLResponse)
def admin_edit_sign_in_sheet_add_post(request: Request, date: str = Form(...), person_id: str = Form(...), time: str = Form(...), minutes: str = Form(...)):
    creds = request.cookies.get("admin")
    if not _check_admin_credential(creds):
        return templates.TemplateResponse("adminLogin.html", context={"request": request})

    timestamp = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    seconds = int(float(minutes) * 60)
    connection = pymysql.connect(host="localhost",
                                 user=LOCAL_USER,
                                 password=LOCAL_PASSWORD,
                                 database="attendancedb")
    with connection:
        with connection.cursor() as cursor:
            query = f"INSERT INTO signinsheet (personID, signInTime, timeToday) VALUES ('{person_id}', '{timestamp}', '{seconds}')"
            cursor.execute(query)
        connection.commit()
        return _edit_sign_in_sheet(request, connection, date)
