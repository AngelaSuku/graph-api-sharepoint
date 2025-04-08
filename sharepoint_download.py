import os
import sys
import requests
import msal
import glob
from datetime import datetime,timedelta
import json
import configparser
from airflow.exceptions import AirflowException
import pytz

creds_file =r'' # This is used for the credentials file
creds = configparser.ConfigParser()
creds.sections()
creds.read(creds_file)

APP_ID = creds['key']['_value']
CLIENT_SECRET = creds['key-api']['_value']
SCOPES = ['Sites.ReadWrite.All']
END_POINT = 'https://graph.microsoft.com/v1.0'
tenant_id = creds['key']['_value'] # add your tenant id
Authority='https://login.microsoftonline.com/'+tenant_id
j = json.load(open('token.json')) # add the full path of the file that contains token
access_token = j['access_token']
# print(access_token)

file_naming = sys.argv[1]
attachment_list = [file_naming]
filelist = glob.glob(os.path.join('folder_you_want_to_store_file','*.*'))

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
                    file_name = file.get('name')
                    # print(file_name)
                    name = os.path.splitext(file_name)[0]
                    updated_date = file.get('remoteItem', {}).get('lastModifiedDateTime', None)
                    created_date = file.get('remoteItem', {}).get('createdDateTime', None)
                    shared_date = file.get('remoteItem', {}).get('shared', {}).get('sharedDateTime', None)
                    file_owner = file.get('createdBy', {}).get('user', {}).get('displayName', None)

                    # ------ Convert the UTC
                    est_timezone = pytz.timezone('US/Eastern')
                    updated_date_utc = datetime.fromisoformat(updated_date[:-1]).replace(tzinfo=pytz.utc)
                    updated_date_est = updated_date_utc.astimezone(est_timezone)

                    updated_date_ = updated_date_est.strftime('%Y-%m-%d')
                    sharepoint_file = datetime.fromisoformat(updated_date_est.strftime('%Y-%m-%d %H:%M:%S'))

                    for item in attachment_list:
                        if item in name: 
                            drive_id = file.get('remoteItem', {}).get('parentReference', {}).get('driveId', None)
                            print('Downloading file:' + file_name)
                            print('File {0} \n Created Date : {1} \n Updated Date : {2} \n Shared Date  : {3} \n File Owner   : {4}\n Sharepoint File: {5}'.format(file_name,created_date,updated_date,shared_date, file_owner, sharepoint_file))
                            item_information = END_POINT + '/drives/{0}/items/{1}/'.format(drive_id,file_id)

                            if 'folder' in file.keys():
                                folder_list = END_POINT + '/drives/{0}/items/{1}/children'.format(drive_id,file_id)
                                folder_list_response = requests.get(folder_list, headers=headers)
                                files = folder_list_response.json().get('value',[])
                                for file in files:
                                    file_name = file.get('name')
                                    if 'Automation' in file_name:
                                        print(file_name)
                                        drive_id = file.get('parentReference', {}).get('driveId', None)
                                        file_id = file.get('id', None)
                                        folder_list = END_POINT + '/drives/{0}/items/{1}/children'.format(drive_id,file_id)
                                        folder_list_response = requests.get(folder_list, headers=headers)
                                        subfiles = folder_list_response.json().get('value',[])
                                        for subfile in subfiles:
                                            file_name = subfile.get('name')
                                            if 'amazon_key' in file_name:
                                                print(file_name)
                                                download_url = requests.get(subfile.get('@microsoft.graph.downloadUrl', []))
                                                if download_url.status_code in range(200,209):
                                                    file_name, file_extension = os.path.splitext(file_name)
                                                    file_name = "{0}_{1}{2}".format(file_name,datetime.now().strftime("%Y-%m-%d"),file_extension)
                                                    file_path = os.path.join('/var/working/amazonkey/input',file_name)
                                                    with open(file_path, 'wb') as f:
                                                        f.write(download_url.content)
                                                        print('File {0} downloaded'.format(file_name))
                                                        os.system('chmod 666 "{0}"'.format(file_path))
                            else:
                                
                                item_response = requests.get(item_information, headers=headers)
                                download_data = item_response.json().get('@microsoft.graph.downloadUrl', [])
                                download_url = requests.get(download_data)
                                if download_url.status_code in range(200,209):
                                    file_path = os.path.join(save_folder, file_name)
                                    with open(file_path, 'wb') as f:
                                        f.write(download_url.content)
                                        print('File {0} downloaded'.format(file_name))
                                        os.system('chmod 666 "{0}"'.format(file_path))
                                else:
                                    raise AirflowException('Failed to download {0}. Status code: {1}'.format(file_name, download_url.status_code))


            else:
                print("No shared files found.")
        else:
            raise AirflowException('Failed to list shared files. Status code: {0}'.format(files_response.status_code))
    except Exception as e:
        raise AirflowException('An error occurred: {0}'.format(str(e)))

download_sharepoint_files_by_name(headers)