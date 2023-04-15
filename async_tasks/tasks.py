import os
import tarfile
from celery import shared_task
import zipfile
import pymysql
import py7zr

def returnConection():
    try:
        return pymysql.connect(host='54.211.21.168', port=3306, user='test', passwd='password', db='dbconvert')
    except pymysql.MySQLError as e:
        print(repr(e))
        return None
    
@shared_task(ignore_result=False,name="add_together")
def add_together(a: int, b: int) -> int:
    return a + b

def compressAsZip(targetName,sourceDir):
    with zipfile.ZipFile(targetName, "w") as zf:
        zf.write(sourceDir)

def compressAs7z(targetName,sourceDir):
    with py7zr.SevenZipFile(targetName, 'w') as z:
        z.writeall(sourceDir)

def compressAsTarGZ(targetName,sourceDir):
    with tarfile.open(targetName, "w:gz") as tar:
        tar.add(sourceDir, arcname=os.path.basename(sourceDir))

@shared_task(ignore_result=False,name="startConversion")
def startConversion(uid: str,fileName: str, newFormat: str) -> int:

    newFileName = "./processedFiles/"+uid+"."+newFormat
    sourceDir = "./uploads/"+fileName
    if newFormat == "zip":
        compressAsZip(newFileName, sourceDir)
    elif newFormat == "7z":
        compressAs7z(newFileName, sourceDir)
    elif newFormat == "tar.gz":
        compressAs7z(newFileName, sourceDir)
        
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "UPDATE `dbconvert`.`archivos` SET `status` = 'PROCESSED', `processedFile`='{newFileName}' WHERE `fileIdentifier` = '{uid}'";
        sql = sql.format(uid=uid, newFileName=newFileName)
        #print(sql)
        cur.execute(sql)
        conn.commit()
    conn.close()
    return newFileName

