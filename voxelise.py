import sys, os, subprocess, pathlib, multiprocessing

#CONFIG
VALIDATE_MESH_FILE_EXTENSION = ['.obj']
VALIDATE_VOLUME_FILE_EXTENSION = ['.raw']
NUM_THREADS = multiprocessing.cpu_count() #Can be set manually

def validate_args(mesh_filename, volume_filename, dimension):
    #Validate args
    #Dimension is int
    if not isinstance(dimension, int):
        print("dimension provided to process_mesh is not an int", file=sys.stderr)
        return False

    #File validation
    files = {
        mesh_filename: VALIDATE_MESH_FILE_EXTENSION, 
        volume_filename: VALIDATE_VOLUME_FILE_EXTENSION
    }

    for file, extensions in files.items():
        #Is string
        if not isinstance(file, str):
            print(f"{file} provided to process_mesh is not a string", file=sys.stderr)
            return False
        #Is correct extension
        if pathlib.Path(file).suffix.lower() not in extensions:
            print(f"{file} invalid extension provided to process_mesh. Use: {extensions}", file=sys.stderr)
            return False

    #Mesh file exists
    if not os.path.isfile(mesh_filename):
        print(f"{mesh_filename} provided to process_mesh does not exist", file=sys.stderr)
        return False

    return True

#Voxelise mesh using our c++ program
def process_mesh(mesh_filename, volume_filename, dimension):
    #Validate args
    if not validate_args(mesh_filename, volume_filename, dimension):
        print(f"Arguments failed validation in process_mesh", file=sys.stderr)
        return False

    #Check if it's already been done (Possible if the upload failed afterwards)
    if os.path.isfile(volume_filename):
        print("Mesh has already been voxelised")
        return True

    command = f"./voxelise {mesh_filename} {volume_filename} {dimension} {NUM_THREADS}"
    
    try:
        subprocess.run(command.split(' '))
        return True
    except Exception as ex:
        print(f"Command failed:\n{command}", file=sys.stderr)
        print(ex, file=sys.stderr)
        return False