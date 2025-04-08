import os
import sys
import requests
import msal
import glob
from datetime import datetime,timedelta
import json
import configparser


creds_file =r'' # This is used for the credentials file
creds = configparser.ConfigParser()
creds.sections()
creds.read(creds_file)

APP_ID = creds['key']['_value']
CLIENT_SECRET = creds['key']['_value']
SCOPES = ['Sites.ReadWrite.All']
END_POINT = 'https://graph.microsoft.com/v1.0'
tenant_id = creds['key']['_value']
Authority='https://login.microsoftonline.com/'+tenant_id
j = json.load(open('token.json')) # add the full path of the file that contains token
access_token = j['access_token']
# print(access_token)

headers = {
	"Authorization" : 'Bearer ' + access_token,
    "Content-Type" : 'application/json'
}

local_file = sys.argv[1]
sharepoint_folder = sys.argv[2]

def create_backup(headers,drive_id,folder_id,file_name,local_file):
    try:
        new_filename, file_extension = os.path.splitext(os.path.basename(file_name))
        new_filename = "{0}_{1}{2}".format(new_filename,datetime.now().strftime("%Y-%m-%d"),file_extension)
        item_information = END_POINT + '/drives/{0}/items/{1}:/Backup/{2}:/createUploadSession'.format(drive_id,folder_id,new_filename)
        item_response = requests.post(item_information, headers=headers)

        if item_response.status_code in range(200,209):
            print('Upload URL was created!')
            upload_url = item_response.json().get('uploadUrl',None)
            if upload_url:
                print(upload_url)
                CHUNK_SIZE = 10 * 1024 * 1024
                total_size = os.path.getsize(local_file)
                with open(local_file, 'rb') as fd:
                    start = 0
                    while True:
                        chunk = fd.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        bytes_read = len(chunk)
                        end = start + bytes_read - 1
                        upload_range = f'bytes {start}-{end}/{total_size}'
                        percentage = (end / total_size) * 100
                        print('upload: {}% '.format(int(percentage)))
                        requests.put(upload_url, headers={'Content-Length': str(bytes_read), 'Content-Range': upload_range}, data=chunk).raise_for_status()
                        start += bytes_read

    except Exception as e:
        print('An error occurred: {0}'.format(str(e)))


def upload_files_sharepoint(headers,local_file,sharepoint_folder):
    try:
        files_response = requests.get(END_POINT + '/me/drive/sharedWithMe?allowexternal=true',headers=headers)
        formatted_json = json.dumps(files_response.json(), indent=4)
        # print(formatted_json)
        if files_response.status_code in range(200,209):
            shared_files = files_response.json().get('value', [])
            if shared_files:
                for file in shared_files:

                    folder_id = file.get('remoteItem', {}).get('id', None)
                    folder_name = file.get('name')

                    if file.get('folder',None) is not None and folder_name == sharepoint_folder:

                        print(folder_name , ' is a folder !')
                        drive_id = file.get('remoteItem', {}).get('parentReference', {}).get('driveId', None)
                        file_name = os.path.basename(local_file)
                        if 'amazon' in file_name:
                            create_backup(headers,drive_id,folder_id,file_name,local_file)
                        if 'Amazon' in sharepoint_folder:
                            item_information = END_POINT + '/drives/{0}/items/{1}:/Automation (Do Not Delete or Modify)/{2}:/createUploadSession'.format(drive_id,folder_id,file_name)
                        else: 
                            item_information = END_POINT + '/drives/{0}/items/{1}:/{2}:/createUploadSession'.format(drive_id,folder_id,file_name)
                        item_response = requests.post(item_information, headers=headers)

                        if item_response.status_code in range(200,209):
                            upload_url = item_response.json().get('uploadUrl',None)

                            if upload_url:
                                print(upload_url)
                                CHUNK_SIZE = 10 * 1024 * 1024
                                total_size = os.path.getsize(local_file)
                                with open(local_file, 'rb') as fd:
                                    start = 0
                                    while True:
                                        chunk = fd.read(CHUNK_SIZE)
                                        if not chunk:
                                            break
                                        bytes_read = len(chunk)
                                        end = start + bytes_read - 1
                                        upload_range = f'bytes {start}-{end}/{total_size}'
                                        percentage = (end / total_size) * 100
                                        print('upload: {}% '.format(int(percentage)))
                                        requests.put(upload_url, headers={'Content-Length': str(bytes_read), 'Content-Range': upload_range}, data=chunk).raise_for_status()
                                        start += bytes_read
                            else : 
                                print('Upload url was not generated !')

            else:
                print("No shared files found.")
        else:
            print('Failed to list shared files. Status code: {0}'.format(files_response.status_code))

    except Exception as e:
        print('An error occurred: {0}'.format(str(e)))


def main():
    upload_files_sharepoint(headers,local_file,sharepoint_folder)

if __name__ == '__main__':
  main()
