from elasticsearch import Elasticsearch
es = Elasticsearch()

def is_old_data_available():
    try:
        res = es.get(index="test-index", id=1)
        print(res['_source'])

        es.indices.refresh(index="test-index")

        res = es.search(index="test-index", body={"query": {"match_all": {}}})
        print("Got %d Hits:" % res['hits']['total']['value'])
        for hit in res['hits']['hits']:
            print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
    
    except Exception as e:
        print("notify developer - mail or create tickets - etc" + str(e))
        print("errorELKIntegration")


is_old_data_available()
