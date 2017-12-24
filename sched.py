# -*- coding: utf-8 -*-
import os
import click
import time
import sys
from apscheduler.events import EVENT_SCHEDULER_STARTED,EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler


try:
    import asyncio
except ImportError:
    import trollius as asyncio

scheduler = AsyncIOScheduler()

@click.command()
@click.option('--script', 
                prompt='script path', 
                help='input script path, please!')
@click.option('--trigger', 
                nargs=2, 
                # type=click.Choice(['date','interval','cron']), 
                prompt='mode of operation', 
                help='input mode of operation, please!')
@click.argument('email', nargs=-1)
def run(script, trigger, email):

    click.secho('%s :::: %s' % (script, trigger), fg='cyan', bold=True)

    try:
        with open(script) as f:
            sf = f.readlines

        if trigger:
            raise TypeError()
    except (IOError):
        click.secho('file not exist' , fg='red', bold=True)
        scheduler.shutdown()
        sys.exit(0)
    except (TypeError):
        click.secho('1111111111111' , fg='red', bold=True)
        scheduler.shutdown()
        sys.exit(0)

    
    scheduler.add_listener(job_listener, EVENT_SCHEDULER_STARTED | EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    scheduler.add_job(db_job, 'interval', id='2231', seconds=3)
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
    time.sleep(2)
    click.secho('The task is being carried out', fg='cyan', bold=True)


def mail_job():
    pass


if __name__ == '__main__':
    run()


#python sched.py --script D:\Workspace\VSCodeWorkspace\WoodFrog\test.py --trigger df df