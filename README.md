# Intro
Hello! This project is an attendance designed for a small system-on-a-chip (like a Raspberry Pi). This system uses a database to track the amount of time members of a team have been at meetings.

# Materials
Barcode scanner
System-on-a-chip (I used an Orange Pi, but Raspberry Pis probably could be used.)
Access to a 3D printer (convenient for printing a case)
Internet Connection :)

# Setup (Debian-based Linux Dist)
We are going to be installing using pip install, then setting up scripts to run this application on startup.

## Steps
```
apt-get install git
mkdir /app
cd /app
git clone https://github.com/ElementalAlly/attendanceProject.git
```

These will set up the files for the install.

```
apt-get install python3.10-venv
python3 -m venv venv
source venv/bin/activate
```

This will activate a venv, allowing us to use pip.

```
pip install --upgrade pip
```

Without the latest version of pip, pyproject.toml won't work.

```
pip install -e .
git clone https://github.com/rm-hull/OPi.GPIO.git
pip install -e OPi.GPIO/
```

This installs the attendancetracker module, so running the script is easy.

## Now, to set up mysql:

```
deactivate
apt-get install mysql-server mysql-client
mysql
```

Now, we are in the mysql interface.

```
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '<enter password here>';
FLUSH PRIVILEGES;
quit;
```

Remember that password.

Next, to set up the database:

```
mysql < attendancedb_init.sql -u root -p <password>
```

Finally, we need a .env file for the local mysql user.

```
cd attendanceProject/attendancetracker/
<editor> .env
```

### .env file:
```
user="root"
password="<enter password>"
```

Now, finally, we will test the modules.

```
cd ..
source venv/bin/activate
attendancetracker
```

This should bring up an interface where you can enter an ID, and it is "signed in" or 'signed out".

Adjust a few files:
   /app/attendanceProject/attendancetracker/__main__.py (GPIO)
   /app/attendanceProject/attendancetracker/static/images/favicon.png (icon on the website)
   /app/attendanceProject/attendancetracker/app/pages/home.md (name of the team)

Test the website
```
ifconfig (remember the IP address of the interface you've used, whether that is eth0 for wired connections, or wlan0 for wireless connections.)
cd attendancetracker
apt-get install ufw
uvicorn app.main:app --reload --port 80 --host 0.0.0.0
```

From another computer on the same network, you should be able to connect to the ip address from a web browser.

## Not Required, but this will start the scripts on boot.

```
cd /lib/systemd/system/getty@tty1.service.d
<editor> 20-autologin.conf
```

## 20-autologin.conf
```
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
```

```
cd ~
<editor> .profile
```

## .profile (end of file)
```
sleep 5
/app/attendanceProject/venv/bin/attendancetracker
```

Finally, we will be changing rc.local, which runs before sign-in, and with root privileges:

```
cd /etc/
<editor> rc.local
```

## rc.local (end of file)
```
cd /app/attendanceProject/attendancetracker
/app/attendanceProject/venv/bin/uvicorn app.main:app --host 0.0.0.0 --reload --port 80 &
exit 0
```

## To test all of this:
```
shutdown -r now
```

After the boot, it should have this:

```
What is your id?

```

Finally, we can set up the hostname on the device and broadcast it, to make accessing reports and registration easier:

```
<editor> /etc/hostname
```

## Hostname:
```
<hostname you want>
```

Then:

```
apt-get install avahi-daemon
```

This is the hostname set up. You can check this by putting:

```
hostname
```

into the shell. If your hostname is displayed, you are all set!

```
shutdown -r now
```

Then, you should be able to access the host from <hostname>.local.

That should be the set up on the software side!

## Wiring

To wire this, the LEDs should look like someone like this:
![circuit diagram][circuit-diagram]

[circuit-diagram]: https://github.com/ElementalAlly/attendanceProject/raw/master/CircuitDiagram.png

# Technologies

In this, I use:
 - **MySQL** as the database
 - **Pymysql** as the database API for python
 - **FastAPI** as the website API
 - **Uvicorn** as the website listener
 - **Jinja** and **Markdown** as rendering helpers

## Scripts:
Say ~ is wherever attendanceProject is:

~/attendancetracker/\_\_main\_\_.py (sign in/sign out logic)
~/attendancetracker/app/main.py (website logic)
