import os, pip, sys, argparse

path = os.getcwd() 
path += "/magicDeckGenerator/models"
parser=argparse.ArgumentParser()

parser.add_argument('--loadCards', help='Download new card information from scryfall')

args=parser.parse_args(sys.argv[1:])

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

try:
    import nltk
    print("trying to install nltk")
    nltk.download('stopwords')
    nltk.download('punkt')
except Exception as e:
    raise e

import urllib.request
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


url = 'https://api.scryfall.com/bulk-data/oracle-cards' 
print('Beginning file download with urllib2...')
try:
    resp = get(url)
    downloadLoc = json.loads(resp.text)["download_uri"]
    urllib.request.urlretrieve(downloadLoc, path + "/scryfall-default-cards.json")  
except:
    print("Issue connecting to card ref download") 
