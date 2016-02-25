import os
from shutil import rmtree, copytree


def copy_dir(foldername=None):
    # remove the last /, if it exists
    if foldername[-1] == '/':
        foldername = foldername[:-1]
    foldername = os.path.expanduser(foldername)
    new_foldername = foldername+"-copy"
    # copy the folder so that we can work on it without worry
    # this will delete the existing copy
    if os.path.isdir(new_foldername):
        rmtree(new_foldername)
    copytree(foldername, new_foldername)
    return new_foldername