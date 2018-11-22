import os
import sys
from os import stat
from pwd import getpwuid
import getpass

#
# setperms.py
# 
#  Spawns a subprocess of this script as root to change ownership of a file
#   to allow the current user to write to the file
#
#


TMP_FILE = "file.tmp"

if (len(sys.argv) == 1):
    print("Usage: %s PATH" % (sys.argv[0]))
    sys.argv.append(TMP_FILE)

path = sys.argv[1]

def find_owner(filename):
    return getpwuid(stat(filename).st_uid).pw_name

if (os.geteuid() == 0):
    #hurray we are root
    try:
        with open(TMP_FILE, "r") as tmp_file:
            uid = int(tmp_file.read())
        
        os.chown(path, uid, -1)

        print("Running as SUPER user!")
    except:
        print("Failed to start as SUPER user!")

else:
    owner = find_owner(path)
    user = getpass.getuser()
    
    if (user == owner):
        #print("%s is already owned by %s" % (path, getpass.getuser()) )
        exit()

    print("*************************************************************")
    print("path: %s\nuser: %s\nowner: %s" % (path, user, owner))

    if os.path.isfile(TMP_FILE):
        print("Failed to gain SUPER user privileges!")
    else:
        try:
            #create temporary file
            with open(TMP_FILE, "w") as tmp_file:
                tmp_file.write(str(os.geteuid()))
        except:
            print("Critical failure: Unable to create file " + TMP_FILE + "!")
            exit

        print("Trying to gain SUPER user privileges...")

        os.execvp('sudo', ['sudo', 'python3'] + sys.argv)

# clean up temporary file
if os.path.isfile(TMP_FILE):
    os.remove(TMP_FILE)
