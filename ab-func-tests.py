from datetime import datetime
from elasticsearch import Elasticsearch
import urllib.request
es = Elasticsearch()


def feed_index():
    try:
        if(urllib.request.urlopen("http://localhost:5601").getcode() == 200 and 
        urllib.request.urlopen("http://localhost:9200").getcode() == 200):
            doc = {
                'author': 'yogesh',
                'text': 'Am i being fed into index',
                'timestamp': datetime.now(),
                }
            res = es.index(index="integration-test-index", id=2, body=doc)
            print(res['result'] + "SUCCESS")
    
    except Exception as e:
        print("notify developer - mail or create tickets - etc" + str(e))
        print("errorELKFunctional")


feed_index()
