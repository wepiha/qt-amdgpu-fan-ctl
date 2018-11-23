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
    exit()

path = sys.argv[1]

def find_owner(filename):
    return getpwuid(stat(filename).st_uid).pw_name

if (os.geteuid() == 0):
    print("Done!")
    
    try:
        print("Trying to set file owner... ", end='')
        with open(TMP_FILE, "r") as tmp_file:
            uid = int(tmp_file.read())
        
        os.chown(path, uid, -1)
        print("Done!")

    except Exception as e:
        print("Error! Failed to chown, the error was:\n" + str(e))

else:
    owner = find_owner(path)
    user = getpass.getuser()
    uid = str(os.geteuid())

    if (user == owner):
        #print("%s is already owned by %s" % (path, getpass.getuser()) )
        exit()

    print("*************************************************************")
    print("path: %s\nuser: %s (uid: %s)\nowner: %s" % (path, user, uid, owner))

    if os.path.isfile(TMP_FILE):
        print("Failed!")
    else:
        try:
            #create temporary file
            with open(TMP_FILE, "w") as tmp_file:
                tmp_file.write(uid)
        except Exception as e:
            print("Error!\nFailed to create temporary file, the error was:\n" + str(e))
            exit

        print('Respawning using sudo...', end=' ')
        sys.stdout.flush()
        os.execvp('sudo', ['sudo', 'python3'] + sys.argv)

# clean up temporary file
if os.path.isfile(TMP_FILE):
    os.remove(TMP_FILE)

print("*************************************************************")
