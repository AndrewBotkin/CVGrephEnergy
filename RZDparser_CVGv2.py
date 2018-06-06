# -*- coding: utf-8 -*-
"""
Created on Thu May 17 17:38:14 2018
@author: avbotkin
"""
from bs4 import BeautifulSoup
import requests
import re
import psycopg2
import getpass
import signal
import sys
import time
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
from contextlib import contextmanager

server = '192.168.0.1' # SMTP server
port = 25 # SMTP port
login = "SMTPLogin" # SMTP port
email_pass = "pass" # SMTP pass
from_addr = "RZDNEWS <email@server.com>"
receiver = "reciver@server.com"

fake_send = False
sleep_time = 60*5 # seconds
net_timeout = 20 # seconds
smtp_retry_time = 30 # seconds
smtp_retries_num = 5

def connection_DB_open(data):
    conn = None
    try:
       
        conn = psycopg2.connect(host="192.168.0.1",database="ext", user="username", password="pass")  #here DB connect

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)   
    return conn

def connection_DB_close(conn):
    Ok_status = 'Ok'
    try:
        if conn is not None:
            conn.close()
            Ok_status = 'Ok closed'
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        Ok_status = 'NotOk'
    return Ok_status

roadfeed = []
datefeed = []
timefeed = []
newsfeed = []
linkfeed = []
roadnamefeed = []
roadname = []
urllist = []
roadlist = []
i = 0

urllist.append ("http://vszd.rzd.ru/news/public/ru?STRUCTURE_ID=2")
roadlist.append ("vszd")
roadname.append ("Восточно-Сибирская")
urllist.append ("http://gzd.rzd.ru/news/public/ru?STRUCTURE_ID=11")
roadlist.append ('gzd')
roadname.append ("Горьковская")
urllist.append ('http://dvzd.rzd.ru/news/public/ru?STRUCTURE_ID=60')
roadlist.append ('dvzd')
roadname.append ("Дальневосточная")
urllist.append ('http://zabzd.rzd.ru/news/public/ru?STRUCTURE_ID=39')
roadlist.append ('zabzd')
roadname.append ("Забайкальская")
urllist.append ('http://zszd.rzd.ru/news/public/ru?STRUCTURE_ID=42')
roadlist.append ('zszd')
roadname.append ("Западно-Сибирская")
urllist.append ('http://kzd.rzd.ru/news/public/ru?STRUCTURE_ID=4059')
roadlist.append ('kzd')
roadname.append ("Калининградская")
urllist.append ('http://kras.rzd.ru/news/public/ru?STRUCTURE_ID=24')
roadlist.append ('kras')
roadname.append ("Красноярская")
urllist.append ('http://kbsh.rzd.ru/news/public/ru?STRUCTURE_ID=4523')
roadlist.append ('kbsh')
roadname.append ("Куйбышевская")
urllist.append ('http://mzd.rzd.ru/news/public/ru?STRUCTURE_ID=12')
roadlist.append ('mzd')
roadname.append ("Московская")
urllist.append ('http://ozd.rzd.ru/news/public/ru?STRUCTURE_ID=2')
roadlist.append ('ozd')
roadname.append ("Октябрьская")
urllist.append ('http://privzd.rzd.ru/news/public/ru?STRUCTURE_ID=12')
roadlist.append ('privzd')
roadname.append ("Приволжская")
urllist.append ('http://svzd.rzd.ru/news/public/ru?STRUCTURE_ID=11')
roadlist.append ('svzd')
roadname.append ("Свердловская")
urllist.append ('http://szd.rzd.ru/news/public/ru?STRUCTURE_ID=24')
roadlist.append ('szd')
roadname.append ("Cеверная")
urllist.append ('http://skzd.rzd.ru/news/public/ru?STRUCTURE_ID=9')
roadlist.append ('skzd')
roadname.append ("Северо-Кавказская")
urllist.append ('http://uvzd.rzd.ru/news/public/ru?STRUCTURE_ID=2')
roadlist.append ('uvzd')
roadname.append ("Юго-Восточная")
urllist.append ('http://yuzd.rzd.ru/news/public/ru?STRUCTURE_ID=50')
roadlist.append ('yuzd')
roadname.append ("Южно-Уральская")

conn = None
while i <=15:  #15
    r  = requests.get(urllist[i])
    soup = BeautifulSoup(r.text, "lxml")
    for text in soup.find_all('li'):
            for texts in text.find_all('span', 'CardDateSpan'):
                datefeed.append (repr(texts.contents)[4:-23])
                timefeed.append (repr(texts.contents)[30:-2])
                
            for texta in text.find_all('a', 'news_list_cardLink'):
                newsfeed.append (repr(re.sub('\n        ','',texta.string))[1:-1])
                roadfeed.append (roadlist[i])
                roadnamefeed.append (roadname[i])
                linkoper = texta.get('href')
                if linkoper[0] == '/': 
                    linkfeed.append ('https://'+roadlist[i]+'.rzd.ru'+linkoper)
                else: 
                    linkfeed.append(linkoper)
    i += 1
i = 0
conn = connection_DB_open('DoIt')
cur = conn.cursor()
body = ''
html = "<html>  <head></head>  <body>  <p><b>Новости РЖД</b><br><br>"
roadnamecurr = ''

while i <len(newsfeed):
    sql = """INSERT INTO rzdnewsfeed(roadfeed, datefeed,timefeed,newsfeed,linkfeed, emailed) VALUES(%s,%s,%s,%s,%s,false);"""
    if roadnamefeed[i] != roadnamecurr: 
        html = html +  '<b>{roadname_name}</b><br><br>'.format(roadname_name = roadnamefeed[i])
    roadnamecurr = roadnamefeed[i]
    try:
        print (roadfeed[i]+ datefeed[i])
        cur.execute(sql, (roadfeed[i], datefeed[i],timefeed[i],newsfeed[i],linkfeed[i]))
        conn.commit()   
        body = body +"{road_feed} | {date_feed} {time_feed} | {news_feed} {link}\n\n".format(
          road_feed = roadfeed[i],
          date_feed = datefeed[i],
          time_feed = timefeed[i],
          news_feed = newsfeed[i],
          link = linkfeed[i]
        )             
        html = html +  '{date_feed} {time_feed} | <a href="{link}">{news_feed}</a> <br><br>'.format(
          date_feed = datefeed[i],
          time_feed = timefeed[i],
          news_feed = newsfeed[i],
          link = linkfeed[i]
        )
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        cur.execute("ROLLBACK")
        conn.commit()
    i += 1
html = html + "  </p> </body></html>"      
try:    
        cur.close()    
except (Exception, psycopg2.DatabaseError) as error:
        print(error)       
print (connection_DB_close(conn))
subject = "{title} | {feed_title}".format(
  title = "Новости РЖД",
  feed_title = datetime.date.today())
print(subject)
msg = MIMEMultipart('alternative')
part1 = MIMEText(body, 'plain')
part2 = MIMEText(html, 'html')
msg['Subject'] = subject
msg['From'] = from_addr
msg['To'] = receiver
msg.attach(part1)
msg.attach(part2)

if body == '': fake_send = True

if not fake_send:
          try:
            with SMTP(server, port) as conn:
              conn.starttls()
              conn.login(login, email_pass)
              conn.sendmail(from_addr, [receiver], msg.as_string())
          except Exception as exc:
            print("Failed to send email: {}".format(exc)) 