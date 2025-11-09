import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import json


import pickle
import os
import re

# Scope untuk mengedit Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def find_file_in_drive(file_name, folder_id=None):
    service = authenticate()

    # Query pencarian
    if folder_id:
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    else:
        query = f"name='{file_name}' and trashed=false"

    results = service.files().list(
        q=query,
        spaces='drive',
        fields="files(id, name, webViewLink)",
    ).execute()

    files = results.get('files', [])
    return files  # list of dict: [{'id': '...', 'name': '...', 'webViewLink': '...'}]


# Fungsi autentikasi
def authenticate():
    # Ambil service account JSON dari Streamlit Secrets
    st.text(st.secrets["google_drive"]["service_account_json"][:200])
    key_json = st.secrets["google_drive"]["service_account_json"]
    key_json_fixed = key_json.replace("\n", "\\n")
    key_dict = json.loads(key_json_fixed)
    creds = service_account.Credentials.from_service_account_info(key_dict, scopes=SCOPES)
    
    # Bangun service Google Drive
    service = build('drive', 'v3', credentials=creds)
    return service


# Upload file lokal
def upload_file_to_drive(file_path, folder_id=None):
    service = authenticate()
    
    file_metadata = {'name': os.path.basename(file_path)}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    return file.get('webViewLink')

def convert_google_drive_url_to_direct_link(url):
    # Use a regular expression to find the file ID in the given URL
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    
    if match:
        file_id = match.group(1)
        # Construct the direct access URL
        direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        return direct_url
    else:
        raise ValueError("The provided URL is not a valid Google Drive file link.")
    
# Streamlit UI
def up_to_drive(uploaded_file, filename):
    if uploaded_file is not None:
        new_filename = filename + os.path.splitext(uploaded_file.name)[-1]
        temp_path = f"./{new_filename}"
        # st.write(new_filename) 
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        folder_id = "1X3zJsYGg1NpwNa67oq_hwLzW1zkSUZyj"  # ganti sesuai folder target

        # 🔍 Cari file dengan nama yang sama
        existing_files = find_file_in_drive(new_filename, folder_id)

        if existing_files:
            st.warning(f"File '{new_filename}' sudah ada di Google Drive.")
            file = existing_files[0]
            direct_link = convert_google_drive_url_to_direct_link(file['webViewLink'])
            st.write(f"Link file yang sudah ada: {direct_link}")
        else:
            # 🚀 Upload baru
            link = upload_file_to_drive(temp_path, folder_id)
            st.success("Upload sukses!")
            direct_link = convert_google_drive_url_to_direct_link(link)
            st.write(f"Link file baru: {direct_link}")

        os.remove(temp_path)
        return direct_link
# 
# Fungsi untuk mencari dan mencetak semua file di folder Google Drive
def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents"  # Query untuk mencari file dalam folder tertentu
    try:
        # Mengambil daftar file dari folder yang ditentukan
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        if files:
            print(f"Files in folder {folder_id}:")
            for file in files:
                print(f"File name: {file['name']} (ID: {file['id']})")
        else:
            print("Tidak ada file di folder ini.")
    
    except HttpError as error:
        print(f"An error occurred: {error}")


