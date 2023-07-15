# Intro
This project is an attendance tracker, designed to run on a Raspberry Pi or compatible platform. Using a bar code or QR code reader, users can sign in and out. Users can also access a website interface to view how long they have been signed in for. Admins can

# Materials
 - USB Barcode/QR Code scanner (I used [this one](https://www.amazon.com/dp/B09HK3BD5Y))
 - Raspberry Pi or compatible system (I used an Orange Pi Zero2 with an Ubuntu Focal image with a 4.9 kernel.)
 - Access to a 3D printer (convenient for printing a case, I ended up using an Ender 3 Neo)
 - LEDS (1 red, 1 green)
 - Cables
 - Dupont crimper and connectors
 - Internet Connection :)

# Technologies

In this, I use:
 - **Python** as my language
 - **MySQL** as the database
 - **Pymysql** as the database API for python
 - **FastAPI** as the website API
 - **Uvicorn** as the website listener
 - **Jinja** and **Markdown** as rendering helpers

# Setup (Debian-based Linux Dist)
We are going to be installing using pip install, then setting up scripts to run this application on startup.

## Installing software needed
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

This activates the venv we just set up, allowing us to set up the module.

```
pip install --upgrade pip
```

Without the latest version of pip, pyproject.toml won't work.

```
pip install -e .
```

This installs the attendancetracker module, so running the script is easy.

### If you are using an orangepi
```
git clone https://github.com/rm-hull/OPi.GPIO.git
pip install -e OPi.GPIO/
```

Since I used an Orange Pi zero2, I used this library to interact with GPIO for the leds.

## Setting up mysql

```
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
nano .env
```

### .env
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
 - /app/attendanceProject/attendancetracker/__main__.py (GPIO library and ports, depending on your specific device)
 - /app/attendanceProject/attendancetracker/static/images/favicon.png (icon on the website)
 - /app/attendanceProject/attendancetracker/app/pages/home.md (name of the team)

## Hostname

```
nano /etc/hostname
```

### hostname

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


## Starting scripts on boot:

```
nano /lib/systemd/system/getty@tty1.service.d/20-autologin.conf
```
https://docs.google.com/document/d/1k0Df5FH6akm-81Zu7FDYv9DlAC7-eb6PGO5RTfAWU4o/edit?usp=sharing
### 20-autologin.conf
```
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
```

Back to the shell, for the other half of the auto script.

```
nano .profile
```

### .profile (end of file)
```
sleep 5
/app/attendanceProject/venv/bin/attendancetracker
```

We sleep to let the mysql service start on boot.

Finally, we will be changing rc.local, which runs before sign-in, and with root privileges:

```
nano /etc/rc.local
```

### rc.local (end of file)
```
cd /app/attendanceProject/attendancetracker
/app/attendanceProject/venv/bin/uvicorn app.main:app --host 0.0.0.0 --reload --port 80 &
```

## To test all of this:
```
shutdown -r now
```

After the boot, it should have this:

```
What is your id?

```

You should also be able to access the host from hostname.local (whatever your hostname is).

That should be the set up on the software side!

## Wiring

To wire this, the LEDs should look like something like this:

![circuit diagram][circuit-diagram]

[circuit-diagram]: https://github.com/ElementalAlly/attendanceProject/raw/master/docs/CircuitDiagram.png

## Printing the Case

If you are using an Orange Pi zero2, this case will work perfectly without modification. If you used any other model, you will likely need to make modifications to the [cad here][cad-files].

The stl files are in this repo, in 3DModels, if you happen to be using an Orange Pi zero2.

### NOTE: The Orange Pi zero2 case was not my work. All of the credit goes to pierloca [here][top-case] and silver-alx [here][bottom-case].

[cad-files]: https://cad.onshape.com/documents/cdb46c01e6ede9460f1eefde/w/d5b10b1233e1596de3d425d7/e/f95f9c48b9db4eb6acbf2c91?renderMode=0&uiState=64b30701daacca2840efeaff
[top-case]: https://www.thingiverse.com/thing:5394637
[bottom-case]: https://www.thingiverse.com/thing:5022392

# Usage:

The main script looks like this:

```
What is your id?

```

To regularly use this, simply type in an id and press enter. Say my ID is 3. The script will look something like this:

```
What is your id?
3
Signed in!
What is your id?
```

This indicates that you have signed in, and an entry of a sign in has been put into the database. Upon another entry of the same ID within the same day, the output will look something like this:

```
What is your id?
3
Signed in!
What is your id?
3
Signed out!
What is your id?
```

This indicates a successful sign out, and the time between the sign in and sign out times is recorded. Finally, if you want to end the script from running, simply type in "end\_program" when it asks you for an id, and it should exit.

```
What is your id?
end_program
```

Although you can use a display with this system, it has been designed to not require one. If you wired the green and red LEDs up and adjusted the ports and library to fit your device, then you can just use the red and green status LEDs to see what is going on.
Upon a successful boot, both the red and green LEDs will light up for 1 second, then both turn off. Upon a sign in, the green LED will light up for 1 second. Upon a sign out, the red LED will light up for 1 second.

If you have only connected a barcode scanner to the device, then you can just use that to scan in the ids. On top of that, I have created a qr code you can use to exit the program and shutdown the system cleanly, linked [here][labels]. Simply scan this QR code and the device will cleanly power off.
[labels]: https://docs.google.com/document/d/1k0Df5FH6akm-81Zu7FDYv9DlAC7-eb6PGO5RTfAWU4o/edit?usp=sharing

Finally, let's dive into the website.

# Website:

Upon opening the website, you will be greeted with this home screen:

![home screen][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/HomePage.png]

From here, I strongly recommend you register a name with the ID you used to sign in, at the registration page:

![registration screen][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/RegisterScreen.png]

Enter your name, ID, then click the button. This will give you a screen that looks like this:

![registration screen, filled][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/RegisterScreenFilled.png]

Next, you can go to reports, to view the report of your attendance through certain times, which looks like this:

![reports screen][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/ReportScreen.png]

Once you fill out the fields with your desired information, you can get a report that looks something like this:

![reports screen, filled][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/ReportScreenFilled.png]

# Admin:

There is one more feature of this device. That is the admin reports. If you need to view all the reports or if you would like to export them in csv, you can. Go to hostname.local/admin to view the admin home screen.

![admin home screen][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/AdminHome.png]

Click on "Auto generated reports" to find all of the reports, in the style of the other report generation:

![admin reports screen][https://github.com/ElementalAlly/attendanceProject/raw/master/docs/AdminReports.png]

Click on "Dump to CSV (excel spreadsheets)" to get a dump of the database with all known sign ins and the registry.
