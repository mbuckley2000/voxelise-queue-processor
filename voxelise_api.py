"""
Handles interaction with the Voxelise API
"""

import sys
import urllib
import requests

# CONFIG
API_BASE_URL = 'https://voxelise-api.mattbuckley.org'


def download_file(url, filename):
    """
    Downloads a file from the API

    Args:
        url: URL of file to download IN THE API (e.g. /meshes/bunny.obj)
        filename: Filename of the downloaded mesh

    Returns:
        True upon success, false upon failure
    """
    try:
        urllib.request.urlretrieve(f'{API_BASE_URL}{url}', filename)
        return True
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False


def get_meshes():
    """
    Retreives all unprocessed meshes from API

    Returns:
        ON SUCCESS: List of meshes
        ON FAILURE: Dictionary with 'failed': True property
    """
    try:
        response = requests.get(API_BASE_URL+'/meshes?processed=false')
        return response.json()
    except Exception as ex:
        print('Failed to get meshes', file=sys.stderr)
        print(ex)
        return {'failed': True}


def create_volume():
    """
    Creates a new volume item in the API

    Returns:
        ON SUCCESS: ID of new volume
        ON FAILURE: False
    """
    try:
        r = requests.post(API_BASE_URL+'/volumes')
        return r.json()['id']
    except Exception as ex:
        print('Failed to create volume', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False


def link_mesh_volume(mesh_id, volume_id):
    """
    Links a mesh to a volume (and vice versa) in the API

    Args:
        mesh_id: ID of the mesh in the API
        volume_id: ID of the volume in the API

    Returns:
        ON SUCCESS: True
        ON FAILURE: False
    """
    try:
        requests.put(API_BASE_URL+'/volumes/' +
                     volume_id, data={'mesh': mesh_id})
        requests.put(API_BASE_URL+'/meshes/' + mesh_id,
                     data={'volume': volume_id})
        return True
    except Exception as ex:
        print('Failed to create volume', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False


def set_mesh_processed(mesh_id):
    """
    Sets a mesh's 'processed' property to true in the API

    Args:
        mesh_id: ID of the mesh in the API

    Returns:
        ON SUCCESS: True
        ON FAILURE: False
    """
    try:
        options = {'processed': 'true'}
        requests.put(API_BASE_URL+'/meshes/' + mesh_id, data=options)
        return True
    except Exception as ex:
        print('Failed to set mesh to processed', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False


def upload_volume(filename):
    """
    Uploads a volume file to the API, creates a Volume item for it, and then links them

    Args:
        filename: File to upload

    Returns:
        ON SUCCESS: Uploaded volume ID
        ON FAILURE: False
    """
    volume_id = create_volume()

    if not volume_id:
        return False

    try:
        files = {'files': (filename, open(filename, 'rb'),
                           'application/octet-stream')}
        options = {
            'refId': volume_id,  # volume Id.
            'ref': "volume",  # Model name.
            'field': "file"  # Field name in the User model.
        }
        response = requests.post(
            API_BASE_URL+'/upload', files=files, data=options)
        code = response.status_code

        if code != 200:
            print(
                f'Failed to upload volume, status code {code}', file=sys.stderr)

        return volume_id

    except Exception as ex:
        print('Failed to upload volume', file=sys.stderr)
        print(ex, file=sys.stderr)
        return False
