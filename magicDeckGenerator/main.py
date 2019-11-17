import pickle, random, gc, csv, time
from cardVectorizer import Vectorizor
from sklearn.manifold import TSNE, SpectralEmbedding, MDS
from sklearn.decomposition import PCA
from gensim.utils import simple_preprocess
import numpy as np

#v = Vectorizor()
#dS = DeckScraper(v)
#dS.prime() # This is slooooow to start

def build_card_csv(model_dimensionality, save=False):
    print("Building")
    cv = Vectorizor()
    v = Vectorizor(model_dimensionality)
    v.load_training_sequence()
    cards = v.build_clean_array(False)
    data = [c.simple_vec for c in cards]
    if save:
        with open('./models/card' + str(model_dimensionality) + '.csv', mode='w+') as csv_file: 
            writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for d in data:
                writer.writerow(d)
    else: 
        return data

def learn(data, model_dimensionality, algorithm, file_name=None):
    gc.collect()
    t = time.time()
    if (algorithm == "TSNE"):
        alg = TSNE(n_components=2)
    elif (algorithm == "MDS"):
        alg = MDS(n_components=2)
    elif (algorithm == "SpectralEmbeddingNN"):
        alg = SpectralEmbedding(n_components=2, affinity="nearest_neighbors")
    elif (algorithm == "SpectralEmbeddingRBF"):
        alg = SpectralEmbedding(n_components=2, affinity="rbf")
    else:
        alg = PCA(n_components=2)

    print(algorithm)
    first_pass = alg.fit_transform(np.array(data))
    if file_name:
        url = './models/final/card' + file_name + str(model_dimensionality) + "d" + '.csv'
    else:
        url = './models/final/card' + algorithm + str(model_dimensionality) + "d" + '.csv'

    with open(url, mode='w+') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for d in first_pass:
            writer.writerow(d)

def readInData(model_dimensionality, first_pass=True, alg=None):
    if alg:
        file_name = './models/card'+ alg + str(model_dimensionality) +'d.csv'
    else: 
        file_name = './models/card' + str(model_dimensionality) + '.csv'
    data = []
    with open(file_name, 'rU') as f:  #opens PW file
        reader = csv.reader(f)
        for rec in csv.reader(f, delimiter=','): #reads csv into a list of lists
            data.append([float(x) for x in rec])
        f.close()

    if (not first_pass):
        data = np.array(data)
        mean = np.mean(data)
        std = np.std(data)
        card_data = []
        with open("./models/cardData.csv", 'rU') as f:  #opens PW file
            reader = csv.reader(f)
            for rec in csv.reader(f, delimiter=','): #reads csv into a list of lists
                card_data.append([(int(float(x)) * mean) / std for x in rec])
            f.close()
        print(card_data[0])
        data = np.concatenate((data, np.array(card_data)), axis=1)
    return data

dimen = [3,4,5,6,7,10,25,50]
algs = ['TSNE', "SpectralEmbeddingRBF"]

for alg in algs[1:]:
    for i in dimen:
        for a in algs:
            data = readInData(i, False, a)
            learn(data, i, alg, alg + str(a))


print(readInData(5, False)[0])

def saveCardData():
    cv = Vectorizor()
    v = Vectorizor(2)
    v.load_training_sequence()
    cards = v.build_clean_array(False)
    card_values = []
    for c in cards:
        card_values.append([c.card_type[0], c.card_type[1], c.get_color_identity(), c.get_cmc(), \
        c.get_toughness(), c.get_power()])

    with open('./models/cardData.csv', mode='w+') as csv_file: 
            writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for d in card_values:
                writer.writerow(d)

def scrape_sites():
    try:
        obj = pickle.load( open( "./models/pickledLinks.p", "rb" ) )
        poss_links = obj["to_scrape"]
        dS.seen = obj["seen"]
        if len(poss_links) > 0:
            random.shuffle(poss_links)
            print("Ingesting ", len(poss_links), " links")
            dS.to_scrape = poss_links
        else:
            print("Building new scrape model")
            dS.build()
        while(len(dS.to_scrape) > 0):
            dS.generate_card_pool()

    except:
        obj = {"seen" : dS.seen, "to_scrape": dS.to_scrape}
        pickle.dump( obj, open( "./models/pickledLinks.p", "wb" ) )
        raise
