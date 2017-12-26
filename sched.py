# -*- coding: utf-8 -*-
import os
import click
import time
import sys
import xlwt
import smtplib
import json
import sqlite3
import cx_Oracle
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.application import MIMEApplication 
from apscheduler.events import EVENT_SCHEDULER_STARTED,EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from configparser import ConfigParser


try:
    import asyncio
except ImportError:
    import trollius as asyncio

conf = ConfigParser()
conf.read('conf.ini', encoding='utf-8')

DbType = {
    'sqlite': sqlite3,
    'oracle': cx_Oracle
}


scheduler = AsyncIOScheduler()

def parser_date(arg):
    return {'run_date': datetime.strptime(arg, '%Y/%m/%d/%H/%M')}

def parser_interval(arg):
    intervals = {'h': 'hours', 'm': 'minutes' }
    return {intervals[arg[-1].lower()] : int(arg[0: -1])}


@click.command()
def run():
    try:
        trigger_type = conf.get('Trigger', 'TriggerType').strip()
        trigger_value = conf.get('Trigger', 'TriggerValue').strip()
        kwargs = {}
        
        if trigger_type == 'date':
            kwargs.update(parser_date(trigger_value))
        elif trigger_type == 'interval':
            kwargs.update(parser_interval(trigger_value))
        elif trigger_type == 'cron':
            kwargs.update(json.loads(trigger_value))
        else:
            raise TypeError('Invalid trigger!')
            
        scheduler.add_job(db_job, trigger_type, id='db_job', **kwargs)
            
    except (Exception) as e:
        click.secho('System Error: %s' % e , fg='red', bold=True)
        scheduler.shutdown()
        sys.exit(0)
 
    scheduler.add_listener(job_listener, EVENT_SCHEDULER_STARTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    scheduler.start()

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


def job_listener(event):
    if EVENT_JOB_ERROR == event.code:
        click.secho('The %s error: %s' % (event.job_id, event.exception), fg='red', bold=True)
    elif EVENT_SCHEDULER_STARTED == event.code:
        click.secho('The job scheduler started!')
    elif EVENT_JOB_EXECUTED == event.code:
        click.secho('The %s executed successfully!' % event.job_id)
    else:
        pass


def db_job():
    click.secho('The task is being carried out', fg='cyan', bold=True)

    files = conf.get('Script', 'RunFile')

    try:
        conn = getattr(DbType.get(conf.get('DB','DbType')), 'connect')(conf.get('Script', 'ConnStr'))

        for f_path in files.split(','):
            f_path = f_path.strip()
            if not os.path.exists(f_path):
                continue
            with open(f_path) as f:
                try:
                    f_name, f_ext = os.path.splitext(os.path.basename(f_path))
                    cursor = conn.cursor()
                    cursor.execute(f.read())
                    fields = cursor.description
                    results = cursor.fetchall()

                    workbook = xlwt.Workbook()
                    sheet = workbook.add_sheet(f_name,cell_overwrite_ok=True)
                    for field in range(0, len(fields)):
                        sheet.write(0, field, fields[field][0])

                    for row in range(1,len(results)+1):
                        for col in range(0,len(fields)):
                            sheet.write(row, col, u'%s' % results[row-1][col])        
                    workbook.save(os.path.join(conf.get('Export', 'ExportPath'), '%s.xls' % f_name))
                except (Exception) as e:
                    click.secho('The Script [%s] Error: %s' % (f_name, e), fg='red', bold=True)
                finally:
                    cursor.close()
    except (Exception) as e:
        click.secho('The DB Conn Error: %s' % e, fg='red', bold=True)
    finally:
        conn.close()

    if conf.get('Email', 'Sender') and conf.get('Email', 'To'):
        mail_job()


def mail_job():
    msg = MIMEMultipart()
    msg['Accept-Language'] = 'zh-CN'
    msg['Accept-Charset'] = 'ISO-8859-1,utf-8'
    msg['Subject'] = conf.get('Email', 'Subject')
    msg['From'] = conf.get('Email', 'Sender')
    msg['To'] = conf.get('Email', 'To')

    #正文
    part = MIMEText(conf.get('Email', 'SenderContent')) 
    msg.attach(part) 

    exp_dir= conf.get('Export', 'ExportPath')

    for file_name in os.listdir(exp_dir):
        if file_name.find('.xls') == -1:
            continue
        exp_file = os.path.join(exp_dir, file_name)
        #xlsx类型附件 
        part = MIMEApplication(open(exp_file,'rb').read()) 
        part.add_header('Content-Disposition', 'attachment', filename=('gbk', '', file_name)) 
        msg.attach(part) 

    server = getattr(smtplib, conf.get('Email', 'SmtpSsl'))(conf.get('Email','SmtpServer'), conf.get('Email','SmtpPort'))
    server.login(conf.get('Email', 'Sender'), conf.get('Email', 'SenderPass'))
    server.send_message(msg)
    server.quit()


if __name__ == '__main__':
    run()


#python sched.py --script /home/tom/Workspace/WoodFrog/README.md --trigger interval 2m
