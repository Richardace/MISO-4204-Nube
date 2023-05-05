# Imports the 'storage' module from the google.cloud package
# to allow interactions with the Google Cloud Storage.
from google.cloud import storage

# Creates a Client object that allows the script to communicate
# with Google Cloud Storage and perform operations on it (like creating a bucket).
client = storage.Client()

# Creates a new bucket with a specified name
bucket = client.create_bucket("nube_archivos")

# Prints a message indicating the bucket was successfully created.
print("Bucket {} created.".format(bucket.name))
