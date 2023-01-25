#This script is intended to automatically send the recipient a motivational quote every Monday.

#here are the structures to a few of the differing smtp email addresses:

# Gmail: smtp.gmail.com
# hotmail: smtp.live.com
# Outlook: outlook.office365.com
# Yahoo: smtp.mail.yahoo.com

import smtplib
import datetime as dt
import random

#you would type your email address and password below
My_EMAIL = "youremailhere@gmail.com"
MY_PASSWORD = "yourpasswordhere"


#getting the datetime of the script to ensure emails are sent on the correct date
now = dt.datetime.now()
weekday = now.weekday()
if weekday == 0:
    with open("quotes.txt") as quote_file:
        all_quotes = quote_file.readlines()
        quote = random.choice(all_quotes)

    print(quote)
    with smtplib.SMTP("smtp.mail.yahoo.com") as connection:
        connection.starttls()
        connection.login(My_EMAIL, MY_PASSWORD)
        connection.sendmail(
            from_addr=My_EMAIL,
            to_addrs=My_EMAIL,
            msg=f"Subject: Monday Motivation\n\n{quote}"
        )