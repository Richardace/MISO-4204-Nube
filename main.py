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
from flask import send_file
import re

app = create_app()
celery_app = app.extensions["celery"]
key = "estoesunsecreto"

@app.route("/")
def hello():
    return "<h1 style='color:blue'>eHello There!</h1>"

#SingUp
@app.post("/api/auth/signup") 
def register() -> dict[str,object]:
    usuario = ""
    try: 
        usuario = request.json["usuario"]
        if(usuario == ""):
            return {"message":"El usuario no puede ser vacio!"}, 400        
    except:
        return {"message":"Hubo un problema valor del usuario"}, 400
        
    correo = ""
    try:
        correo = request.json["correo"]
        if(correo == ""):
            return {"message":"El correo no puede ser vacio!"}, 400  
    except:
         return {"message":"Hubo un problema valor del correo"}, 400
    
    contrasena = ""
    try:
        contrasena = request.json["contrasena"]
        if(contrasena == ""):
            return {"message":"La contrasena no puede ser vacio!"}, 400
    except:
        return {"message":"Hubo un problema valor del contrasena"}, 400
    
    contrasena2 = ""
    try:
        contrasena2 = request.json["contrasena2"]
        if(contrasena2 == ""):
            return {"message":"La contrasena2 no puede ser vacio!"}, 400
    except:
        return {"message":"Hubo un problema valor del contrasena2"}, 400
    
    if(contrasena != contrasena2):
        return {"message":"La contraseñas no son iguales"}, 400
    
    conn = returnConection()
    result = any
    print("SUCCESS: Connection to RDS MySQL instance succeeded")
    with conn.cursor() as cur:
        sql = "SELECT `id` FROM `usuarios` where `usuario` = %s or `correo` = %s;"
        cur.execute(sql,(usuario, correo))
        result = cur.fetchone()
        print(result)        
    
    if result is None:
        # Ejemplo de uso        
        if(validar_contraseña(contrasena) == False):
            return {"message":"La contraseña no cumple con los requisitos mínimos de seguridad.\
                    Longitud mínima de 8 caracteres\
                    Al menos una letra mayúscula\
                    Al menos una letra minúscula\
                    Al menos un número\
                    Al menos un carácter especial (como !, @, #, $, %, etc.) "}, 400
            
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
        return {"message":"El usuario o correo ya existe"}, 404

import re

def validar_contraseña(contraseña):
    # Expresión regular para validar una contraseña segura
    regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,}$"
    
    # Comprobar si la contraseña coincide con la expresión regular
    if re.match(regex, contraseña):
        print("La contraseña es segura")
        return True
    else:
        print("La contraseña no cumple con los requisitos mínimos de seguridad")
        return False

@app.post("/api/auth/login")
def login() -> dict[str,object]:
    usuario = ""
    try: 
        usuario = request.json["usuario"]
        if(usuario == ""):
            return {"message":"El usuario no puede ser vacio!"}, 400        
    except:
        return {"message":"Hubo un problema valor del usuario"}, 400
    
    contrasena = ""
    try:
        contrasena = request.json["contrasena"]
        if(contrasena == ""):
            return {"message":"La contrasena no puede ser vacio!"}, 400
    except:
        return {"message":"Hubo un problema valor del contrasena"}, 400
       
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

#Consultar Archivo
@app.get("/api/tasks/<id_task>")
def consultarTarea(id_task: str) -> dict[str, object]:
    userId = getUserId()
    result = any
    if userId == None:
      return {"message":"Unauthorized"}, 401
    
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "SELECT * FROM `archivos` where `id` = '{id_task}';"
        sql = sql.format(id_task = id_task)
        cur.execute(sql)
        result = cur.fetchone()
        print(result)
    conn.close()
    if result is not None:
        return {
        "id": result[0],
        "status": result[1],
        "timestamp": result[2],
        "fileName": result[3],
        "newFormat":  result[4],
        "fileIndetifier": result[5],
        "processedFile":  result[6],
        "userId": result[7]
       }
    else:
        return {"message":"Tare no exite"}, 404     
   
     
#Eliminar un Archivo
@app.delete("/api/tasks/<id_task>")
def eliminarTarea(id_task: str) -> dict[str, object]:
    userId = getUserId()
    result = any
    if userId == None:
       return {"message":"Unauthorized"}, 401
    
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "DELETE FROM `archivos` where `id` = '{id_task}' AND `status` = '{status}' ;"
        sql = sql.format(id_task = id_task, status = "PROCESSED")
        result = cur.execute(sql)
        print(result)
        conn.commit()        
        conn.close()
    if result == 1:
       return {"message":"Tare Eliminada"} 
    else:
       return {"message":"Tarea no siponible"}, 404

@app.get("/api/tasks")
def getTasks() -> dict[str, object]:

    userId = getUserId()
    if userId == None:
        return {"message":"Unauthorized"}, 401
    
    max = request.json["max"]
    order = request.json["order"]
    
    conn = returnConection()
    result = any
    with conn.cursor() as cur:
        #sql = "SELECT * FROM dbconvert.archivos"
        sql = "SELECT * FROM dbconvert.archivos where userId = " + str(userId)
        
        if(order != ""):
            if(int(order) == 0):
                sql = sql + " order by id asc"
            else:
                sql = sql + " order by id desc"
        
        if(max != ""):
            max = int(max)
            sql = sql + " LIMIT " + str(max)

        cur.execute(sql)
        result = cur.fetchall()

    if result is None:
        return {"message": "No Existen Registros de Tareas"}          
    else:
        dict = []
        for i in range(len(result)):
            tarea = {}
            tarea['id'] = result[i][0]
            tarea['status'] = result[i][1]
            tarea['timestamp'] = result[i][2]
            tarea['fileName'] = result[i][3]
            tarea['newFormat'] = result[i][4]
            tarea['fileIdentifier'] = result[i][5]
            tarea['processedFile'] = result[i][6]
            tarea['userId'] = result[i][7]

            dict.append(tarea)

    conn.close()
    return json.dumps(dict, default=str)

@app.get("/api/files/<filename>")
def downloadFile(filename: str) -> dict[str, object]:

    userId = getUserId()
    if userId == None:
        return {"message":"Unauthorized"}, 401

    conn = returnConection()
    result = any
    with conn.cursor() as cur:
        sql = "SELECT * FROM dbconvert.archivos where fileName='" + filename + "'"
        cur.execute(sql)
        result = cur.fetchone()
    
    if(result[1] == "UPLOADED"):
        return {"message": "El Archivo aun no esta listo para ser descargado."}  

    if result is None:
        return {"message": "No existe el archivo especificado"}          
    else:
        return send_file(result[6])

def returnConection():
    try:
        return pymysql.connect(host='54.211.21.168', port=3306, user='test', passwd='password', db='dbconvert')
    except pymysql.MySQLError as e:
        print(repr(e))
        return None

if __name__ == "__main__":
    app.run(host='0.0.0.0')