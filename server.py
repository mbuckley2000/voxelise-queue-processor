import os
import sys
import pathlib
from time import sleep

#Our modules
import voxelise
import voxelise_api

#CONFIG
MESH_DIR = 'downloads'
VOLUME_DIR = 'downloads/processed'
VOXELISATION_DIMENSION = 100 #OUTPUT VOLUME DIM (3D)
MAX_UPLOAD_ATTEMPTS = 3
MAX_LINKING_ATTEMPTS = 5 #Linking uploaded volume to mesh

#Creates directories if they don't exist
#Arg: list of strings (directory names)
def check_and_create_directories(directories):
    for directory in directories:
        if not isinstance(directory, str):
            print("Invalid argument provided to check_and_create_directories. Must be list of strings.", file=sys.stderr)
            exit(1)
        if not os.path.isdir(directory):
            #Create directory
            print(f"Creating directory: {directory}")
            os.makedirs(directory)


def validate_mesh(mesh):
    mesh_file = mesh['file']
    mesh_file_name = mesh_file['name']
    mesh_file_url = mesh_file['url']
    mesh_id = mesh['id']

    #Validate strings
    strings = [mesh_file, mesh_file_name, mesh_file_url, mesh_id]
    for string in strings:
        if not string:
            print(f"Mesh had no {string} property: {mesh_id}")
            return False

    return True


#Main program start
def server():
    while True:
        #Sleep a bit to avoid over pinging the server
        sleep(1)

        #Verify directories
        check_and_create_directories([MESH_DIR, VOLUME_DIR])

        #Get unprocessed meshes from API
        meshes = voxelise_api.get_meshes()
        if 'failed' in meshes:
            print("Failed to retreive meshes")
            continue

        if not meshes:
            #print("There are no unprocessed meshes")
            continue

        for mesh in meshes:
            mesh_id = mesh['_id']

            if not mesh_id or not validate_mesh(mesh):
                print(f"Mesh failed validation: {mesh_id}")
                continue

            mesh_file = mesh['file']
            mesh_file_name = mesh_file['name']
            mesh_file_url = mesh_file['url']

            #Work out the volume file name
            ext_length = len(pathlib.Path(mesh_file_name).suffix)
            prefix = mesh_file_name[:-ext_length] #Remove extension
            volume_file_name = f'{prefix}_{VOXELISATION_DIMENSION}x{VOXELISATION_DIMENSION}x{VOXELISATION_DIMENSION}_uint8.raw'
            
            #Work out file paths
            mesh_file_path = f'{MESH_DIR}/{mesh_file_name}'
            volume_file_path = f'{VOLUME_DIR}/{volume_file_name}'

            #Download file
            if not voxelise_api.download_file(mesh_file_url, mesh_file_path):
                print(f"Failed to download mesh file: {mesh_id}")
                continue

            #Voxelise
            if not voxelise.process_mesh(mesh_file_path, volume_file_path, VOXELISATION_DIMENSION):
                print(f"Failed to voxelise mesh: {mesh_id}")
                continue

            #Upload volume to API
            for attempt in range(MAX_UPLOAD_ATTEMPTS):
                volume_id = voxelise_api.upload_volume(volume_file_path)
                if volume_id:
                    break
                #Wait one second for each retry before retrying
                sleep(1 * attempt)
            
            #Failed to upload even after retries
            if not volume_id:
                print(f"Failed to upload volume: {mesh_id}")
                continue
            
            #Link uploaded volume to mesh and set it to processed
            for attempt in range(MAX_LINKING_ATTEMPTS):
                if voxelise_api.link_mesh_volume(mesh_id, volume_id) and voxelise_api.set_mesh_processed(mesh_id):
                    print(f"Successfully processed {mesh_id}")
                    break
                #Wait one second for each retry before retrying
                sleep(1 * attempt)


server() #RUN SERVER
