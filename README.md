# Intro
This project is an attendance tracker, designed to run on a Raspberry Pi or compatible platform. Using a bar code or QR code reader, users can sign in and out. Users can also access a website interface to view how long they have been signed in for. Admins can also view all sign ins and export it to csv to work with the data in a more raw form.

Tutorial on how to use it available [here](https://youtu.be/DIAiHQ99u1s).

# Materials
 - USB Barcode/QR Code scanner (I used [this one](https://www.amazon.com/dp/B09HK3BD5Y))
 - Raspberry Pi or compatible system (I used an Orange Pi Zero2 with an Ubuntu Focal image with a 4.9 kernel.)
 - Access to a 3D printer (convenient for printing a case, I ended up using an Ender 3 Neo)
 - LEDs (1 red, 1 green)
 - Cables
 - Dupont crimper and connectors
 - Soldering equipment
 - Internet Connection :)

# Technologies

In this, I use:
 - **Python** as my language of choice
 - **MySQL** as the database
 - **Pymysql** as the database API for python
 - **FastAPI** as the website backend
 - **Uvicorn** as the website listener
 - **Jinja** and **Markdown** as text rendering helpers
 - **Chart.js** as the renderer of the graphs
 - **Cron** to backup the project

# Setup (Debian-based Linux Dist)
We are going to be installing using pip install, then setting up scripts to run this application on startup.

Login as root, then follow the steps here:

## Installing software needed
```
apt-get install git
mkdir /app
cd /app
git clone https://github.com/ElementalAlly/attendanceProject.git
```

These will set up the files for the install.

```
apt-get install python3.8-venv
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

### If you are using an Orange Pi
```
git clone https://github.com/rm-hull/OPi.GPIO.git
pip install -e OPi.GPIO/
```

Since I used an Orange Pi Zero2, I used this library to interact with GPIO for the LEDs.

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

### /app/attendanceProject/attendancetracker/.env
```
user="root"
password="<enter password>"
admin="<enter password>"
```

Now, finally, we will test the modules.

```
cd ..
source venv/bin/activate
attendancetracker
```

This should bring up an interface where you can enter an ID, and it is "signed in" or 'signed out".

Adjust a few files:
 - /app/attendanceProject/attendancetracker/\_\_main\_\_.py (GPIO library and ports, depending on your specific device)
 - /app/attendanceProject/attendancetracker/static/images/favicon.png (icon on the website)
 - /app/attendanceProject/attendancetracker/app/pages/home.md (name of the team)

## Hostname

```
nano /etc/hostname
```

### /etc/hostname

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

into the shell. If your hostname is displayed, you have set your hostname correctly!

## Backing up the database

We will be using a private github repository to backup the repository. To set this up:

 - Find or make a github account to hold the backup.
 - Create a private repo
 - Create a fine-tuned personal access token and copy it down
 - Give the token permissions to the private repo: commit statuses, contents, merge queues, pull requests, all read and write
 - On your orangepi, change directory to /app/ and use the following command: `git clone https://<token here>@github.com/<github username here>/<repo name>.git`
 - cd into the repository, and run these commands:

```
touch backupdb.sql
git add .
git commit -m "initial commit"
git push
```

Now, you can test the backup by running:

```
cd /app/attendanceProject/
/bin/sh ./backupdb.sh <your repo name> <your mysql password>
```

This should update the backup in the repository.

## Automatically backing up the database

To automatically back up the database, we will be using cron to run the update script daily.

Run the following:

```
sudo apt update && sudo apt install cron
sudo systemctl enable cron
crontab -e
```

This should bring you into an editor selection. Select the editor you are most comfortable with, or nano for ease.

At the end of the comments, add this entry to the cron table:

```
0 23  * * * /bin/sh /app/attendanceProject/backupdb.sh <your repo name> <your mysql password>
```

This will backup the database once per day.

## Starting scripts on boot:

```
nano /lib/systemd/system/getty@tty1.service.d/20-autologin.conf
```
### /lib/systemd/system/getty@tty1.service.d/20-autologin.conf
```
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
```

Back to the shell, for the other half of the auto script.

```
nano ~/.profile
```

### ~/.profile (end of file)
```
sleep 5
/app/attendanceProject/venv/bin/attendancetracker
```

We sleep to let the mysql service start on boot.

Finally, we will be changing rc.local, which runs before sign-in, and with root privileges:

```
nano /etc/rc.local
```

### /etc/rc.local (end of file)
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

You should also be able to access the website from http://hostname.local/ (whatever your hostname is).

That should be the set up on the software side!

## Restoring from backup

If the system ever corrupts or breaks, follow the setup guide above with a few modifications:

In the section "Backing up the database", after cloning the repository, don't try to create an initial commit. Instead, run the following command:

```
mysql < /app/<backup repo name>/backupdb.sql -u root -p <mysql password>
```

This should have restored the last backup the system had of the database. Complete the setup from there as normal.

## Wiring

To wire this, the LEDs should look like something like this:

![circuit diagram][circuit-diagram]

[circuit-diagram]: https://github.com/ElementalAlly/attendanceProject/raw/master/docs/CircuitDiagram.png

I would recommend using dupont connectors to connect the pins to their endpoints, then soldering the rest of the connections.

## Printing the Case

If you are using an Orange Pi Zero2, this case will work perfectly without modification. If you used any other model, you will likely need to make modifications to the [cad here][cad-files].

The stl files are in this repo, in 3DModels, if you happen to be using an Orange Pi Zero2.

### NOTE: The Orange Pi Zero2 case was not my work. All of the credit goes to pierloca [here][top-case] and silver-alx [here][bottom-case].

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

If you have only connected a barcode scanner to the device, then you can just use that to scan in the ids. On top of that, I have created a qr code you can use to exit the program and shutdown the system cleanly:

![qr code for "end_program(enter)shutdown now"][qrcode]

Simply scan this QR code and the device will cleanly power off.

[labels]: https://docs.google.com/document/d/1k0Df5FH6akm-81Zu7FDYv9DlAC7-eb6PGO5RTfAWU4o/edit?usp=sharing
[qrcode]: https://github.com/ElementalAlly/attendanceProject/raw/master/docs/qrCode.png

Finally, let's dive into the website.

# Website:

Upon opening the website, you will be greeted with this home screen:

![home screen](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/HomePage.png)

From here, I strongly recommend you register a name with the ID you used to sign in, at the registration page:

![registration screen](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/RegisterScreen.png)

Enter your name, ID, then click the button. This will give you a screen that looks like this:

![registration screen, filled](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/RegisterScreenFilled.png)

Next, you can go to reports, to view the report of your attendance through certain times, which looks like this:

![reports screen](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/ReportScreen.png)

Once you fill out the fields with your desired information, you can get a report that looks something like this:

![reports screen, filled](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/ReportScreenFilled.png)

# Admin:

There is one more feature of this system: the admin reports. If you need to view all the reports or if you would like to export them to a csv file, go to http://hostname.local/admin/ to view the admin home screen.

![admin home screen](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/AdminHome.png)

Click on "Auto generated reports" to find all of the reports, in the style of the single report generation:

![admin reports screen](https://github.com/ElementalAlly/attendanceProject/raw/master/docs/AdminReports.png)

Click on "Dump to CSV (excel spreadsheets)" to get a dump of the database with all known sign ins and the registry.

# Generate QR Code IDs

Install python on a laptop or workstation with access to a printer, at least version 3.11.0.
Open terminal or command prompt, and clone this repository: `git clone https://github.com/ElementalAlly/attendanceBackups.git`
cd into the make-id folder in the repository.

Decide what prefix you would want on your ids.
Replace attendanceProject/app/logo.jpg with your own logo.jpg.
Decide what id number range you want, for how many people you expect to make new ids for.
Run this command:

```
python make-id-cards.py --prefix "<insert prefix here>" --range <minimum> <maximum+1> --duplicate
```

From here, the qr-page files will contain the pages you need to print.
For some suggestions:
 - Keep your prefixes short.
 - Print the pages single-sided on colored cardstock.
 - Have the id grantees sign both duplicates of their id, and have them take one and keep one near the scanner.
