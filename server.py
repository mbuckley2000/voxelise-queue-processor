"""
Continuously checks Voxelise API for unprocessed meshes.
Downloads, voxelises, and reuploads them to the API.
"""
import os
import sys
import pathlib
from time import sleep

# Our modules
import voxelise
import voxelise_api

# CONFIG
MESH_DIR = 'downloads'
VOLUME_DIR = 'downloads/processed'
VOXELISATION_DIMENSION = 100  # OUTPUT VOLUME DIM (3D)
MAX_UPLOAD_ATTEMPTS = 3
MAX_LINKING_ATTEMPTS = 5  # Linking uploaded volume to mesh
RETRY_TIME = 1
SLEEP_INTERVAL = 1


def check_and_create_directories(directories):
    """
    Checks if the supplied directories exist, and creates them recursively if not

    Args:
        directories: List of strings, directories to create

    Returns:
        SUCCESS: True
        FAILURE: False
    """
    try:
        for directory in directories:
            if not isinstance(directory, str):
                print(
                    "Invalid argument provided to check_and_create_directories. Must be list of strings.", file=sys.stderr)
                exit(1)
            if not os.path.isdir(directory):
                # Create directory
                print(f"Creating directory: {directory}")
                os.makedirs(directory)

        return True
    except Exception as ex:
        print(ex, file=sys.stderr)
        return False


def validate_mesh(mesh):
    """
    Validates the structure of the given mesh, because it was retreived from the API

    Args:
        mesh: Mesh to check
    Returns:
        VALID: True
        INVALID: False
    """
    mesh_file = mesh['file']
    mesh_file_name = mesh_file['name']
    mesh_file_url = mesh_file['url']
    mesh_id = mesh['id']

    # Validate strings
    strings = [mesh_file, mesh_file_name, mesh_file_url, mesh_id]
    for string in strings:
        if not string:
            print(f"Mesh had no {string} property: {mesh_id}")
            return False

    return True


def get_volume_filename(mesh_filename):
    """
    Calculates the output volume filename from the mesh filename

    Args:
        mesh_filename: Mesh file name

    Returns:
        Volume filename
    """
    # Work out the volume file name
    ext_length = len(pathlib.Path(mesh_filename).suffix)
    prefix = mesh_filename[:-ext_length]  # Remove extension
    return f'{prefix}_{VOXELISATION_DIMENSION}x{VOXELISATION_DIMENSION}x{VOXELISATION_DIMENSION}_uint8.raw'


def upload_volume_to_api(volume_file_path):
    """
    Uploads the given volume to the API and retries upon failure

    Args:
        volume_file_path: Volume to upload

    Returns:
        Uploaded volume ID
    """
    # Upload volume to API
    for attempt in range(MAX_UPLOAD_ATTEMPTS):
        volume_id = voxelise_api.upload_volume(volume_file_path)
        if volume_id:
            break
        # Wait RETRY_TIME for each retry before retrying
        sleep(RETRY_TIME * attempt)

    return volume_id


def link_volume_to_mesh(mesh_id, volume_id):
    """
    Links the API volume to the API mesh, retries upon failure

    Args:
        mesh_id: API mesh ID
        volume_id: API volume ID

    Returns:
        Success: True
        Failure: False
    """
    # Link uploaded volume to mesh and set it to processed
    for attempt in range(MAX_LINKING_ATTEMPTS):
        if voxelise_api.link_mesh_volume(mesh_id, volume_id) and voxelise_api.set_mesh_processed(mesh_id):
            return True
        # Wait RETRY_TIME for each retry before retrying
        sleep(RETRY_TIME * attempt)

    return False


def process_meshes(meshes):
    """
    Processes a list of meshes

    Args:
        meshes: list of meshes
    """
    for mesh in meshes:
        mesh_id = mesh['_id']

        if not mesh_id or not validate_mesh(mesh):
            print(f"Mesh failed validation: {mesh_id}")
            continue

        mesh_file = mesh['file']
        mesh_filename = mesh_file['name']
        mesh_file_url = mesh_file['url']

        volume_filename = get_volume_filename(mesh_filename)

        # Work out file paths
        mesh_file_path = f'{MESH_DIR}/{mesh_filename}'
        volume_file_path = f'{VOLUME_DIR}/{volume_filename}'

        # Download file
        if not voxelise_api.download_file(mesh_file_url, mesh_file_path):
            print(f"Failed to download mesh file: {mesh_id}")
            continue

        # Voxelise
        if not voxelise.process_mesh(mesh_file_path, volume_file_path, VOXELISATION_DIMENSION):
            print(f"Failed to voxelise mesh: {mesh_id}")
            continue

        # Upload volume to API
        volume_id = upload_volume_to_api(volume_file_path)
        if not volume_id:
            print(f"Failed to upload volume: {mesh_id}")
            continue

        # Link uploaded volume to mesh and set it to processed
        if not link_volume_to_mesh(mesh_id, volume_id):
            print(f"Failed to link volume to mesh: {mesh_id}")
            continue

        print(f"Successfully processed mesh {mesh_id}")


# Main program start
def server():
    """
    Continuously checks Voxelise API for unprocessed meshes.
    Downloads, voxelises, and reuploads them to the API.
    """
    while True:
        # Sleep a bit to avoid over pinging the server
        sleep(SLEEP_INTERVAL)

        # Verify directories
        if not check_and_create_directories([MESH_DIR, VOLUME_DIR]):
            print("Unable to check / create directories", file=sys.stderr)
            continue

        # Get unprocessed meshes from API
        meshes = voxelise_api.get_meshes()

        if 'failed' in meshes:
            print("Failed to retreive meshes")
            continue

        if not meshes:
            #print("There are no unprocessed meshes")
            continue

        process_meshes(meshes)


server()  # RUN SERVER
