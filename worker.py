from concurrent.futures import TimeoutError
import json
from google.cloud import pubsub_v1
import os
import tarfile
from celery import shared_task
import zipfile
import pymysql
import py7zr
from google.cloud import storage

project_id = "parabolic-hook-383716"
subscription_id = "my-sub"
timeout = None

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    message.ack()
    print(f"Received {message}.")
    data = json.loads(message.data)
    print(data)
    startConversion(data.get("uid"), data.get("filename"), data.get("newFormat"))
    
def getFile(filename):
    storage_client = storage.Client(project_id)
    bucket = storage_client.bucket("nube_archivos")
    blob = bucket.blob(filename)
    location = "./receivedFiles/"+filename
    blob.download_to_filename(location)
    print("Downloaded storage object {} to local file {}.".format(filename, location))

def upload_blob(source_file_name, destination_blob_name):
    storage_client = storage.Client(project_id)
    bucket = storage_client.bucket("nube_archivos")
    blob = bucket.blob(destination_blob_name)
    generation_match_precondition = 0
    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def returnConection():
    try:
        return pymysql.connect(host='35.239.100.2', port=3306, user='root', passwd='<f{Q=re(t_}v/F<#', db='dbconvert')
    except pymysql.MySQLError as e:
        print(repr(e))
        return None
    
def compressAsZip(targetName,sourceDir):
    with zipfile.ZipFile(targetName, "w") as zf:
        zf.write(sourceDir)

def compressAs7z(targetName,sourceDir):
    with py7zr.SevenZipFile(targetName, 'w') as z:
        z.writeall(sourceDir)

def compressAsTarGZ(targetName,sourceDir):
    with tarfile.open(targetName, "w:gz") as tar:
        tar.add(sourceDir, arcname=os.path.basename(sourceDir))

def startConversion(uid: str, fileName: str, newFormat: str) -> int:
    getFile(fileName)
    exitFile = uid+"."+newFormat
    newFileName = "./processedFiles/"+exitFile
    sourceDir = "./receivedFiles/"+fileName
    if newFormat == "zip":
        compressAsZip(newFileName, sourceDir)
    elif newFormat == "7z":
        compressAs7z(newFileName, sourceDir)
    elif newFormat == "tar.gz":
        compressAs7z(newFileName, sourceDir)
    upload_blob(newFileName, "./processedFiles/"+exitFile)
    os.remove(sourceDir)
    os.remove(newFileName)
    conn = returnConection()
    with conn.cursor() as cur:
        sql = "UPDATE `dbconvert`.`archivos` SET `status` = 'PROCESSED', `processedFile`='{newFileName}' WHERE `fileIdentifier` = '{uid}'";
        sql = sql.format(uid=uid, newFileName=newFileName)
        #print(sql)
        cur.execute(sql)
        conn.commit()
    conn.close()
    return newFileName


streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

# Wrap subscriber in a 'with' block to automatically call close() when done.
with subscriber:
    try:
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.

