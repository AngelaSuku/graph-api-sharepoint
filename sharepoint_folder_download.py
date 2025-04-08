import os
import sys
import requests
import msal
import glob
from datetime import datetime,timedelta
import json
import configparser
# from airflow.exceptions import AirflowException
import pytz

creds_file = r'' # This is used for the credentials file
creds = configparser.ConfigParser()
creds.sections()
creds.read(creds_file)

APP_ID = creds['key']['_value']
CLIENT_SECRET = creds['key']['_value']
SCOPES = ['Sites.ReadWrite.All']
END_POINT = 'https://graph.microsoft.com/v1.0'
tenant_id = ['key']['_value']
Authority='https://login.microsoftonline.com/'+tenant_id
j = json.load(open('token.json')) # add the full path of the file that contains token
access_token = j['access_token']
# print(access_token)

attachment_list = ['key_for_folder_name']
filelist = glob.glob(os.path.join('folder_you_want_to_store_file/','*.*'))

headers = {
    "Authorization" : 'Bearer ' + access_token
}


def download_sharepoint_files_by_name(headers,save_folder='folder_you_want_to_store_file'):
    try:

        files_response = requests.get(END_POINT + '/me/drive/sharedWithMe?allowexternal=true',headers=headers)
        if files_response.status_code in range(200,209):
            shared_files = files_response.json().get('value', [])
            if shared_files:
                for file in shared_files:
                    file_id = file.get('remoteItem', {}).get('id',None)
                    drive_id = file.get('remoteItem', {}).get('parentReference', {}).get('driveId', None)
                    file_name = file.get('name')
                    # print(file_name)
                    name = os.path.splitext(file_name)[0]
                    print(name)
                    updated_date = file.get('remoteItem', {}).get('lastModifiedDateTime', None)
                    created_date = file.get('remoteItem', {}).get('createdDateTime', None)
                    shared_date = file.get('remoteItem', {}).get('shared', {}).get('sharedDateTime', None)
                    file_owner = file.get('createdBy', {}).get('user', {}).get('displayName', None)

                    print('File {0} \n Created Date : {1} \n Updated Date : {2} \n Shared Date  : {3} \n File Owner   : {4}'.format(file_name,created_date,updated_date,shared_date, file_owner))
                    for item in attachment_list:
                        if 'folder' in file.keys() and item in name:
                                file_list = END_POINT + '/drives/{0}/items/{1}/children'.format(drive_id,file_id)
                                file_response = requests.get(file_list, headers=headers)
                                download_pagination(file_response,file_name)
                                url = file_response.json().get('@odata.nextLink',None)
                                while url:
                                    file_response = requests.get(url, headers=headers)
                                    download_pagination(file_response,file_name)
                                    url = file_response.json().get('@odata.nextLink',None)
            else:
                print("No shared files found.")
        else:
            print('Failed to list shared files. Status code: {0}'.format(files_response.status_code))
    except Exception as e:
        print('An error occurred: {0}'.format(str(e)))

def download_pagination(file_response,file_name):
    files = file_response.json().get('value',[])
    for e_file in files:
        download_url = requests.get(e_file.get('@microsoft.graph.downloadUrl', []))
        if download_url.status_code in range(200,209):
            file_path = os.path.join('folder_you_want_to_store_file', e_file.get('name'))
            with open(file_path, 'wb') as f:
                f.write(download_url.content)
                print('File {0} downloaded'.format(e_file.get('name')))
                os.system('chmod 666 "{0}"'.format(file_path))

download_sharepoint_files_by_name(headers)