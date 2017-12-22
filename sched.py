# -*- coding: utf-8 -*-
import click
from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


"""
triggers: 描述一个任务何时被触发，有按日期、按时间间隔、按cronjob描述式三种触发方式
"""


"""
job stores: 
任务持久化仓库,默认保存任务在内存中,也可将任务保存都各种数据库中,
任务中的数据序列化后保存到持久化数据库,从数据库加载后又反序列化.
"""
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}

"""
executors:
执行任务模块,当任务完成时executors通知schedulers,schedulers收到后会发出一个适当的事件.
"""
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

"""
schedulers:
任务调度器,控制器角色,通过它配置job stores和executors,添加、修改和删除任务.
"""
scheduler = BackgroundScheduler(
    jobstores=jobstores, 
    executors=executors, 
    job_defaults=job_defaults, 
    timezone=utc
)


@click.group()
def cli():
    pass


@cli.command()
def check_task():
    tasks = ['A','B','C']
    for task in tasks:
        click.echo(task)


@cli.command()
@click.option('--name', help='input task name , please.')
@click.option('--script', help='input script path , please.')
def add_task(name, script):
    if name and script:
        click.echo('%s, path:%s' % (name, script))
        
    else:
        click.echo('please, input task name & script path')
    


@cli.command()
@click.option('--name', help='input task name , please.')
@click.option('--script', help='input script path , please.')
def alter_task(name, script):
    click.echo('%s, path:%s' % (name, script))


@cli.command()
@click.option('--name', help='input task name , please.')
def del_task(name):
    click.echo(name)


@cli.command()
@click.option('--name', help='input task name , please.')
def run_task(name):
    job = scheduler.add_job(name, 'interval', minutes=2)
    scheduler.start(paused=True)
    click.echo(job)



if __name__ == '__main__':
    cli()