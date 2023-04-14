import zipfile
from flask import Flask
from celery import Celery, Task
from flask import request
from async_tasks import *
from celery.result import AsyncResult
from celery import shared_task
from async_tasks import tasks
from factory import *
import pymysql
import uuid
from datetime import datetime


app = create_app()
celery_app = app.extensions["celery"]

@app.route("/")
def hello():
    return "<h1 style='color:blue'>eHello There!</h1>"

#SUBIR ARCHIVO
@app.post("/api/tasks")
def uploadFile() -> dict[str, object]:
    uid = str(uuid.uuid4())
    newFormat = request.form.get("newFormat", type=str)
    f = request.files['fileName']
    fileName = f.filename
    f.save("./uploads/"+fileName)
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "INSERT INTO `archivos` (`id`, `status`, `timestamp`, `fileName`, `newFormat`, `fileIdentifier`) VALUES (null, '{status}', '{timestamp}', '{fileName}', '{newFormat}', '{fileIdentifier}');"
        sql = sql.format(status = "UPLOADED", timestamp = datetime.now(), fileName=fileName, newFormat=newFormat,fileIdentifier=uid)
        cur.execute(sql)
        eventId = cur.lastrowid
        print(eventId)
        conn.commit()
    conn.close()
    taskId = tasks.startConversion.delay(uid, fileName, newFormat)
    return {"uid": uid, "taskId": taskId.id}


@app.post("/add")
def start_add() -> dict[str, object]:
    a = request.form.get("a", type=int)
    b = request.form.get("b", type=int)
#    a = 12
#    b = 13
    result = tasks.add_together.delay(a, b)
    return {"result_id": result.id}

@app.get("/result/<id>")
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": str(result.result),
        "a": result.status
    }


@app.get("/list_tasks")
def getTasks() -> dict[str, object]:

    conn = returnConection()
    print("SUCCESS: Connection to RDS MySQL instance succeeded")
    with conn.cursor() as cur:
        sql = "INSERT INTO dbconvert.usuarios VALUES (null, 'Santy', 'Santy', 'Sany')"
        cur.execute(sql)
        eventId = cur.lastrowid
        print(eventId)
        conn.commit()
    conn.close()
    print("hola")
    return {"result_id": "hola"}

def returnConection():
    try:
        return pymysql.connect(host='54.211.21.168', port=3306, user='test', passwd='password', db='dbconvert')
    except pymysql.MySQLError as e:
        print(repr(e))
        return None

if __name__ == "__main__":
    app.run(host='0.0.0.0')


