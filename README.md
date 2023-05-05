# MISO-4204-Nube
## Integrantes del Grupo
|  Nombres  | Correo  |  
|---|---|
| Leidy Beltrán Romero  | lt.beltranr1@uniandes.edu.co  |
| Santiago Lozano R  |  ssa.lozanolo@uniandes.edu.co |
| Richard Alexander Acevedo Ramírez   | r.acevedor@uniandes.edu.co   | 
| Oscar Arley Sanchez | oa.sanchez2@uniandes.edu.co |
## Cloud Conversion Tool

Esta es una api rest la cual permite realizar la conversión y comprensión de archivos. Las siguiente son las funcionalidades que se han incluido.

## Escenarios de pruebas
### 1. EndPoints
-Url servicio desplegado http://34.111.221.117/
| Endpoint     | Metodos | Descripción  |
|--------------|---------|--------------|
| signup   | Post |Permite crear una cuenta de usuario, con los campos usuario, correo electrónico y contraseña. El usuario y el correo electrónico deben ser únicos en la plataforma, la contraseña debe seguir unos lineamientos mínimos de seguridad, además debe ser solicitada dos veces para que el usuario confirme que ingresa la contraseña correctamente.       |
| login   | Post | Permite recuperar el token de autorización para consumir los recursos del API suministrando un nombre de usuario y una contraseña correcta de una cuenta registrada.   |
| tasks  | GET |Permite recuperar todas las tareas de compresion de un usuario autorizado en la aplicación.     |
| tasks  | POST  | Permite crear una nueva tarea de compresion de archivo. El usuario requiere autorización.   |
| tasks/<int:id_task> | GET  |Permite recuperar la información de una tarea en la aplicación. El usuario requiere autorización.    |
| tasks/<int:id_task> | DELETE | Permite eliminar una tarea en la aplicación. El usuario requiere autorización.  |
| files/filename    | GET | Permite recuperar el archivo original o procesado   |

# Stack Tecnológico
- Python: 3.11.3 
- MySql: 8.0.32
- Celery: 5.2.7
- Flask: 2.2.3
- Gunicorn: 20.1.0
- Redis: 4.5.4
- Werkzeug: 2.2.3
- Gevent: 22.10.2
- Pymysql: 1.0.3
- Pyjwt: 2.6.0

## Documentación de servicios
[Postman](https://github.com/Richardace/MISO-4204-Nube/wiki/Postman)
