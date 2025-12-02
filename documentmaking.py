import os
import json
folder="data"
documents=[]

datasize=0
for filename in os.listdir(folder):
    if filename.endswith(".txt"):
        datasize=datasize+1

print("Size of the datafiles: ",datasize)

for filename in os.listdir(folder):
    if filename.endswith(".txt"):
        filecontent=""
        with open(os.path.join(folder, filename), 'r') as f:
            filecontent=f.read()
        try:
            jsoncontentfile=json.loads(filecontent)

        except:
            print("Error in file: ",filename)
            continue
        

        

