from datetime import datetime
from elasticsearch import Elasticsearch

def make_functional_tests_elasticsearch():
	try:
		es = Elasticsearch()
		doc = {
			'author': 'balasubramanian',
			'text': 'Elasticsearch in Airbus: is Cool',
			'timestamp': datetime.now(),
			}
		res = es.index(index="test-index", id=1, body=doc)
		print(res['result'])
		
		# res = es.get(index="test-index", id=1)
		# #print(res['_source'])

		# es.indices.refresh(index="test-index")

		# res = es.search(index="test-index", body={"query": {"match_all": {}}})
		# print("Got %d Hits:" % res['hits']['total']['value'])
		# for hit in res['hits']['hits']:
			# print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
	
	except Exception as e:
		print("STOP dont mess the PROD environment")
		#email and escalate and stop CD in the pipeline
		#print (e)


make_functional_tests_elasticsearch()
