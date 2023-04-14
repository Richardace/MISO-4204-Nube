from celery import shared_task
import zipfile
import pymysql

def returnConection():
    try:
        return pymysql.connect(host='54.211.21.168', port=3306, user='test', passwd='password', db='dbconvert')
    except pymysql.MySQLError as e:
        print(repr(e))
        return None
    
@shared_task(ignore_result=False,name="add_together")
def add_together(a: int, b: int) -> int:
    return a + b


@shared_task(ignore_result=False,name="startConversion")
def startConversion(uid: str,fileName: str, newFormat: str) -> int:

    newFileName = "./processedFiles/"+uid+"."+newFormat
    with zipfile.ZipFile(newFileName, "w") as zf:
        zf.write("./uploads/"+fileName)
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "UPDATE `dbconvert`.`archivos` SET `status` = 'PROCESSED', `processedFile`='{newFileName}' WHERE `fileIdentifier` = '{uid}'";
        sql = sql.format(uid=uid, newFileName=newFileName)
        #print(sql)
        cur.execute(sql)
        conn.commit()
    conn.close()
    return newFileName

