import requests
import sys
import urllib

#CONFIG
api_base_url = 'https://voxelise-api.mattbuckley.org'


# Download the file from `url` and save it locally under `file_name`:
def download_file(url, filename):
    try:
        urllib.request.urlretrieve(f'{api_base_url}{url}', filename)
        return True
    except Exception as ex:
        print(ex) >> sys.stderr
        return False


def get_meshes():
    try:
        r = requests.get(api_base_url+'/meshes?processed=false')
        return r.json()
    except Exception as ex:
        print('Failed to get meshes', file=sys.stderr)
        print(ex)
        return {'failed': True}

#Returns ID
def create_volume():
    try:
        r = requests.post(api_base_url+'/volumes')
        return r.json()['id']
    except Exception as ex:
        print('Failed to create volume', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False

def link_mesh_volume(mesh_id, volume_id):
    try:
        requests.put(api_base_url+'/volumes/' + volume_id, data={ 'mesh': mesh_id })
        requests.put(api_base_url+'/meshes/' + mesh_id, data={ 'volume': volume_id })
        return True
    except Exception as ex:
        print('Failed to create volume', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False
    

def set_mesh_processed(mesh_id):
    try:
        options = { 'processed': 'true' }
        requests.put(api_base_url+'/meshes/' + mesh_id, data=options)
        return True
    except Exception as ex:
        print('Failed to set mesh to processed', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False


def upload_volume(filename):
    volume_id = create_volume()

    if not volume_id:
        return False
    
    try:
        files = { 'files': (filename, open(filename, 'rb'), 'application/octet-stream') }
        options = {
            'refId': volume_id, # volume Id.
            'ref': "volume", # Model name.
            'field': "file" #// Field name in the User model.
        }
        response = requests.post(api_base_url+'/upload', files=files, data=options)
        code = response.status_code
        
        if code != 200:
            print(f'Failed to upload volume, status code {code}', file=sys.stderr)
        
        return volume_id
    
    except Exception as ex:
            print('Failed to upload volume', file=sys.stderr)
            print(ex, file=sys.stderr)
            return False