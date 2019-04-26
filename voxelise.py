import sys, os, subprocess, pathlib, multiprocessing

#CONFIG
validate_mesh_file_exts = ['.obj']
validate_volume_file_exts = ['.raw']
thread_count = multiprocessing.cpu_count() #Can be set manually

def validate_args(mesh_filename, volume_filename, dimension):
    #Validate args
    #Dimension is int
    if not isinstance(dimension, int):
        print >> sys.stderr, "dimension provided to process_mesh is not an int"
        return False

    #File validation
    files = {
        mesh_filename: validate_mesh_file_exts, 
        volume_filename: validate_volume_file_exts
    }

    for file, extensions in files.items():
        #Is string
        if not isinstance(file, str):
            print >> sys.stderr, f"{file} provided to process_mesh is not a string"
            return False
        #Is correct extension
        if pathlib.Path(file).suffix.lower() not in extensions:
            print(f"{file} provided to process_mesh didn't have a valid extension. Valid extensions: {extensions.split(', ')}", file=sys.stderr)
            return False
    
    #Mesh file exists
    if not os.path.isfile(mesh_filename):
        print >> sys.stderr, f"{mesh_filename} provided to process_mesh does not exist"
        return False
    
    return True


#Voxelise mesh using our c++ program
def process_mesh(mesh_filename, volume_filename, dimension):
    #Validate args
    if not validate_args(mesh_filename, volume_filename, dimension):
        print >> sys.stderr, f"Arguments failed validation in process_mesh"
        return False

    #Check if it's already been done (Possible if the upload failed afterwards)
    if os.path.isfile(volume_filename):
        print("Mesh has already been voxelised")
        return True

    command = f"./voxelise {mesh_filename} {volume_filename} {dimension} {thread_count}"
    
    try:
        subprocess.run(command.split(' '))
        return True
    except Exception as ex:
        print >> sys.stderr, f"Command failed:\n{command}" 
        print >> sys.stderr, ex
        return False