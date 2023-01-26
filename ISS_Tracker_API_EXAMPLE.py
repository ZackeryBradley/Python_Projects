#This script is meant to track the location of the International Space Station (ISS) by using an API
#once the script recieves the location and our approximate location, it will automate an email encouraging you to look up and view the ISS!

import requests
from datetime import datetime
import smtplib
import time

#type in your respective email address and password below:
MY_EMAIL = "typeyeyouremailhere@gmail.com"
MY_PASSWORD = "type_your_password_here"

#put in your current latitude and longitude positions here:
MY_LAT = 9.701780  #place your latitude here
MY_LONG = 79.862810 #place you longitude here



def is_iss_overhead():
    response = requests.get(url="http://api.open-notify.org/iss-now.json")
    response.raise_for_status() #this code will show us the exception error code in the event the script does not run successful

    data = response.json()

    iss_longitude =longitude = float(data["iss_position"]["longitude"])
    iss_latitude = latitude = float(data["iss_position"]["latitude"])


    #Your position is with +/- 5 degrees of the ISS position
    if MY_LAT - 5 <= iss_latitude <= MY_LAT + 5 and MY_LONG -5 <= iss_longitude <= MY_LONG + 5:
        return True

def is_night():
    parameters = {
        "lat": MY_LAT,
        "lng": MY_LONG,
        "formatted": 0,
    }


    response = requests.get("https://api.sunrise-sunset.org/json", params=parameters)
    response.raise_for_status()
    data = response.json()
    sunrise = int(data["results"]["sunrise"].split("T")[0].split(":")[0])
    sunset = int(data["results"]["sunset"].split("T")[0].split(":")[0])

    time_now = datetime.now().hour

    if time_now >= sunset or time_now <= sunrise:
        return True
        #it's dark

while True:
    time.sleep(60)
    if is_iss_overhead() and is_night():
        connection = smtplib.SMTP("smtp.mail.yahoo.com")
        connection.starttls()
        connection.login(MY_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=f"Subject: Look Up!\n\nThe ISS is above you in the sky!"
        )













