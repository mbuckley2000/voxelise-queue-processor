import json
import requests
import os
import sys
from pprint import pprint
import urllib
from shutil import copyfile
import pathlib
import subprocess
from time import sleep

#Our modules
import voxelise
import voxelise_api

#CONFIG
mesh_dir = 'downloads'
processed_dir = 'downloads/processed'
dimension = 100 #OUTPUT VOLUME DIM (3D)
upload_max_attempts = 3
link_max_attempts = 5 #Linking uploaded volume to mesh

#Creates directories if they don't exist
#Arg: list of strings (directory names)
def check_and_create_directories(directories):
    for directory in directories:
        if not isinstance(directory, str):
            print >> sys.stderr, "Invalid argument provided to check_and_create_directories. Must be list of strings."
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
        if not len(string) > 0:
            print(f"Mesh {string} property is zero length: {mesh_id}")
            return False

    return True


#Main program start
def server():
    while True:
        #Sleep a bit to avoid over pinging the server
        sleep(1)

        #Verify directories
        check_and_create_directories([mesh_dir, processed_dir])

        #Get unprocessed meshes from API
        meshes = voxelise_api.get_meshes()
        if 'failed' in meshes:
            print("Failed to retreive meshes")
            continue

        if len(meshes) == 0:
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
            volume_file_name = f'{prefix}_{dimension}x{dimension}x{dimension}_uint8.raw'
            
            #Work out file paths
            mesh_file_path = f'{mesh_dir}/{mesh_file_name}'
            volume_file_path = f'{processed_dir}/{volume_file_name}'

            #Download file
            if not voxelise_api.download_file(mesh_file_url, mesh_file_path):
                print(f"Failed to download mesh file: {mesh_id}")
                continue

            #Voxelise
            if not voxelise.process_mesh(mesh_file_path, volume_file_path, dimension):
                print(f"Failed to voxelise mesh: {mesh_id}")
                continue

            #Upload volume to API
            for attempt in range(upload_max_attempts):
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
            for attempt in range(link_max_attempts):
                if voxelise_api.link_mesh_volume(mesh_id, volume_id) and voxelise_api.set_mesh_processed(mesh_id):
                    print(f"Successfully processed {mesh_id}")
                    break
                #Wait one second for each retry before retrying
                sleep(1 * attempt)


server() #RUN SERVER