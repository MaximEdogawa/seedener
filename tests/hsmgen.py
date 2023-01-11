import subprocess
hsmgen = "hsmgen" #Keys generate
print(">  ", subprocess.Popen(hsmgen, shell = True, stdout=subprocess.PIPE).stdout.read().decode())

