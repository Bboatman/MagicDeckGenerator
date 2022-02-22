import os, pip, json

path = os.getcwd() 
path += "/magicDeckGenerator/models"

try:  
    os.mkdir(path)
except OSError:  
    print ("Creation of the directory %s failed" % path)
else:  
    print ("Successfully created the directory %s " % path)

try:
    pip.main(["install", "-r", "requirements.txt"])
except SystemExit as e:
    pass

import urllib.request
from requests import get

print('Beginning file download with urllib2...')

url = 'https://api.scryfall.com/bulk-data/oracle-cards' 
try:
    resp = get(url)
    downloadLoc = json.loads(resp.text)["download_uri"]
    urllib.request.urlretrieve(downloadLoc, path + "/scryfall-default-cards.json")  
except:
    print("Issue connecting to card ref download") 
