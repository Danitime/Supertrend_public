import smtplib
import config

from datetime import datetime

newmsg = ""

def send(subject):
    global newmsg

    user = config.USER
    pwd = config.PWD
    mail_text = f"Hi! Diese Mail wurde am {datetime.now().date()} um {datetime.now().time()} verschickt.\n {newmsg}"
    #subject = "Python Mail :)"

    MAIL_FROM = user
    RCPT_TO = "insert_reciver_mail_here"
    DATA = 'From:%s\nTo:%s\nSubject:%s\n\n%s' % (MAIL_FROM, RCPT_TO, subject, mail_text)

    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(user, pwd)
    server.sendmail(MAIL_FROM, RCPT_TO, DATA)
    reset_msg()
    server.quit

def append_msg(msg):
    global newmsg

    newmsg = "\n".join((newmsg, msg))

def reset_msg():
    global newmsg

    newmsg = ""