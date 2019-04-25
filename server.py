import json
import requests
import os
from pprint import pprint
import urllib.request
from shutil import copyfile
import urllib3
import subprocess

api_base_url = 'https://voxelise-api.mattbuckley.org'
http = urllib3.PoolManager()

def download_mesh(url, filename):
    # Download the file from `url` and save it locally under `file_name`:
    urllib.request.urlretrieve(url, filename)

def process_mesh(mesh_filename, volume_filename):
    #voxelise
    #pwd = os.getcwd()
    #command = "docker run -it --rm -v " + pwd + "/downloads:/downloads pymesh/pymesh voxelize.py /" + mesh_filename + " /" + volume_filename + " --cell-size 1"
    command = f"./voxelise {mesh_filename} {volume_filename} 100"
    print(command)
    subprocess.run(command.split(' ')) #Takes array of strings as argv

#Returns ID
def create_volume():
    r = requests.post(api_base_url+'/volumes')
    return r.json()['id']

def link_mesh_volume(mesh_id, volume_id):
    requests.put(api_base_url+'/volumes/' + volume_id, data={ 'mesh': mesh_id })
    requests.put(api_base_url+'/meshes/' + mesh_id, data={ 'volume': volume_id })

def set_mesh_processed(mesh_id):
    options = { 'processed': 'true' }
    requests.put(api_base_url+'/meshes/' + mesh_id, data=options)

def upload_volume(filename):
    volume_id = create_volume()
    
    files = { 'files': (filename, open(filename, 'rb'), 'application/octet-stream') }
    options = {
        'refId': volume_id, # volume Id.
        'ref': "volume", # Model name.
        'field': "file" #// Field name in the User model.
    }
    r = requests.post(api_base_url+'/upload', files=files, data=options)
    print(r.json())

    return volume_id

r = requests.get(api_base_url+'/meshes?processed=false')
meshes = r.json()

for mesh in meshes:
    mesh_file = mesh['file']
    if (mesh_file):
        mesh_filename = 'downloads/' + mesh_file['name']
        volume_filename = 'downloads/processed/' + mesh_file['name'] + '_100x100x100_uint8.raw'
        download_mesh(api_base_url + mesh_file['url'], mesh_filename)
        process_mesh(mesh_filename, volume_filename)
        volume_id = upload_volume(volume_filename)
        mesh_id = mesh['id']
        set_mesh_processed(mesh['id'])
        link_mesh_volume(mesh['id'], volume_id)
