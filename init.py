import os, pip, sys, argparse

path = os.getcwd() 
path += "/magicDeckGenerator/models"
parser=argparse.ArgumentParser()

parser.add_argument('--dbname', help='Psql Database Name')
parser.add_argument('--dbhost', help='Database host location')
parser.add_argument('--dbuser', help='Psql Username')
parser.add_argument('--dbpass', help='Password for psql user')

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

import urllib.request
from django.core.management.utils import get_random_secret_key

print('Beginning file download with urllib2...')

url = 'https://archive.scryfall.com/json/scryfall-default-cards.json'  
urllib.request.urlretrieve(url, path + "/scryfall-default-cards.json")  

with open(".env", "w+") as f:
    f.write("PGUSER={}\n".format(args.dbuser))
    f.write("PGHOST={}\n".format(args.dbhost if args.dbhost else "localhost" ))
    f.write("PGPASSWORD={}\n".format(args.dbpass))
    f.write("PGDATABASE={}\n".format(args.dbname))
    f.write("DJANGO_SECRET={}\n".format(get_random_secret_key()))
    f.close()