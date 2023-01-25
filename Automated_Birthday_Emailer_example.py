#This script is intended to automatically wish your friend happy birthday!

#here are the structures to a few of the differing smtp email addresses:

# Gmail: smtp.gmail.com
# hotmail: smtp.live.com
# Outlook: outlook.office365.com
# Yahoo: smtp.mail.yahoo.com

import smtplib
import datetime as dt
import pandas
import random

#you would type your email address and password below
MY_EMAIL = "youremailhere@gmail.com"
MY_PASSWORD = "yourpasswordhere"

today = (dt.datetime.now().month, dt.datetime.now().day)

data = pandas.read_csv("birthdays_example.csv")

birthdays_dict = {(data_row.month, data_row.day): data_row for (index, data_row) in data.iterrows()}

if today in birthdays_dict:
    birthday_person = birthdays_dict[today]
    file_path = f"letter_{random.randint(1, 3)}.txt"
    with open(file_path) as letter_file:
        contents = letter_file.read()
        contents = contents.replace("[NAME]", birthday_person["name"])

        with smtplib.SMTP("smtp.mail.yahoo.com") as connection:
            connection.starttls()
            connection.login(MY_EMAIL, MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=birthday_person["email"],
                msg=f"Subject: Happy Birthday!\n\n{contents}I wanted to wish you a happy birthday!\n May all life's blessings be yours, on your birthday and always!"
            )
    )