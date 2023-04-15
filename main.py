import json
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
import hashlib
import jwt

app = create_app()
celery_app = app.extensions["celery"]
key = "estoesunsecreto"

@app.route("/")
def hello():
    return "<h1 style='color:blue'>eHello There!</h1>"

#SingUp
@app.post("/api/auth/signup") 
def register() -> dict[str,object]:
    usuario = request.json["usuario"]
    correo = request.json["correo"]
    contrasena = request.json["contrasena"]
    conn = returnConection()
    result = any
    print("SUCCESS: Connection to RDS MySQL instance succeeded")
    with conn.cursor() as cur:
        sql = "SELECT `id` FROM `usuarios` where `usuario` = %s;"
        cur.execute(sql,(usuario))
        result = cur.fetchone()
        print(result)        
    
    #usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
    #return {"user":usuario, "correo": correo, "contrasena":contrasena}
    if result is None:
        contrasena_encriptada = hashlib.md5(request.json["contrasena"].encode('utf-8')).hexdigest()
        with conn.cursor() as cur:
            sql = "INSERT INTO `usuarios` (`id`, `usuario`, `correo`, `contrasena`) VALUES (null, '{usuario}', '{correo}', '{pwd}');"
            sql = sql.format(usuario = usuario, correo = correo, pwd = contrasena_encriptada)
            cur.execute(sql)
            eventId = cur.lastrowid
            print(eventId)
            conn.commit()    
        
        conn.close()
        return {"mensaje": "usuario creado exitosamente"}
    else:
        conn.close()
        return {"message":"El usuario ya existe"}, 404

@app.post("/api/auth/login")
def login() -> dict[str,object]:
    usuario = request.json["usuario"]
    contrasena = request.json["contrasena"]
    
    contrasena_encriptada = hashlib.md5(contrasena.encode('utf-8')).hexdigest()
    conn = returnConection()
    result = any
    print("SUCCESS: Connection to RDS MySQL instance succeeded")
    with conn.cursor() as cur:
        sql = "SELECT `id` FROM `usuarios` where `usuario` = %s AND `contrasena` = %s;"
        cur.execute(sql,(usuario, contrasena_encriptada))
        result = cur.fetchone()
        print(result)
    
    if result is not None:
        encoded = jwt.encode({"userId": result[0]}, key, algorithm="HS256")
        return {"token": encoded}
    else:
        return {"message":"Usuario o contraseña incorrectos!"}, 404     
    
def getUserId():
    try: 
        token = request.headers.get('Authorization')
        decodedToken = jwt.decode(token.replace("Bearer ", ""), options={"verify_signature": False})
        userId = decodedToken.get("userId")
        return userId
    except:
        return None
    

#SUBIR ARCHIVO
@app.post("/api/tasks")
def uploadFile() -> dict[str, object]:
    userId = getUserId()
    if userId == None:
        return {"message":"Unauthorized"}, 401
    
    uid = str(uuid.uuid4())
    newFormat = request.form.get("newFormat", type=str)
    f = request.files['fileName']
    fileName = f.filename
    f.save("./uploads/"+fileName)
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "INSERT INTO `archivos` (`id`, `status`, `timestamp`, `fileName`, `newFormat`, `fileIdentifier`,`userId`) VALUES (null, '{status}', '{timestamp}', '{fileName}', '{newFormat}', '{fileIdentifier}', '{userId}');"
        sql = sql.format(status = "UPLOADED", timestamp = datetime.now(), fileName=fileName, newFormat=newFormat,fileIdentifier=uid, userId=userId)
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


