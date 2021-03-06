#!/usr/bin/env python

import signal
import sys
import argparse
from threading import Lock, Thread, Condition, Event
import string
from random import randint, choice
import time
import sys
import json
try:
    from elasticsearch import Elasticsearch
    from elasticsearch.connection import create_ssl_context
except:
    print("errorELK")
    print ("failure handling mechanisms - ticket, mail etc")
    sys.exit(1)
import urllib3
urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument("--es_address", nargs='+', help="The address of your cluster (no protocol or port)", required=True)
parser.add_argument("--indices", type=int, help="The number of indices to write to for each ip", required=True)
parser.add_argument("--documents", type=int, help="The number different documents to write for each ip", required=True)
parser.add_argument("--clients", type=int, help="The number of clients to write from for each ip", required=True)
parser.add_argument("--seconds", type=int, help="The number of seconds to run for each ip", required=True)
args = parser.parse_args()

NUMBER_OF_INDICES = args.indices
NUMBER_OF_DOCUMENTS = args.documents
NUMBER_OF_CLIENTS = args.clients
NUMBER_OF_SECONDS = args.seconds

# timestamp placeholder
STARTED_TIMESTAMP = 0

# Placeholders
success_bulks = 0
failed_bulks = 0
total_size = 0
indices = []
documents = []
documents_templates = []
es = None  # Will hold the elasticsearch session

# Thread safe
success_lock = Lock()
fail_lock = Lock()
size_lock = Lock()
shutdown_event = Event()

# Helper functions
def increment_success():
    # First, lock
    success_lock.acquire()
    global  success_bulks
    try:
        # Increment counter
        success_bulks += 1

    finally:  # Just in case
        # Release the lock
        success_lock.release()


def increment_failure():
    # First, lock
    fail_lock.acquire()
    global failed_bulks
    try:
        # Increment counter
        failed_bulks += 1

    finally:  # Just in case
        # Release the lock
        fail_lock.release()


def increment_size(size):
    # First, lock
    size_lock.acquire()

    try:
        # Using globals here
        global total_size

        # Increment counter
        total_size += size

    finally:  # Just in case
        # Release the lock
        size_lock.release()


def has_timeout(STARTED_TIMESTAMP):
    # Match to the timestamp
    if (STARTED_TIMESTAMP + NUMBER_OF_SECONDS) > int(time.time()):
        return False

    return True


# Just to control the minimum value globally (though its not configurable)
def generate_random_int(max_size):
    try:
        return randint(1, max_size)
    except:
        print("Not supporting {0} as valid sizes!".format(max_size))
        print("errorELK")
        print ("failure handling mechanisms - ticket, mail etc")
        sys.exit(1)


# Generate a random string with length of 1 to provided param
def generate_random_string(max_size):
    return ''.join(choice(string.ascii_lowercase) for _ in range(generate_random_int(max_size)))


# Create a document template
def generate_document():
    temp_doc = {}

    # Iterate over the max fields
    for _ in range(generate_random_int(100)):
        # Generate a field, with random content
        temp_doc[generate_random_string(10)] = generate_random_string(1000)

    # Return the created document
    return temp_doc


def fill_documents(documents_templates):
    # Generating 10 random subsets
    for _ in range(10):

        # Get the global documents
        global documents

        # Get a temp document
        temp_doc = choice(documents_templates)

        # Populate the fields
        for field in temp_doc:
            temp_doc[field] = generate_random_string(1000)

        documents.append(temp_doc)


def client_worker(es, indices, STARTED_TIMESTAMP):
    # Running until timeout
    while (not has_timeout(STARTED_TIMESTAMP)) and (not shutdown_event.is_set()):

        curr_bulk = ""

        for _ in range(1000):
            # Generate the bulk operation
            curr_bulk += "{0}\n".format(json.dumps({"index": {"_index": choice(indices), "_type": "stresstest"}}))
            curr_bulk += "{0}\n".format(json.dumps(choice(documents)))

        try:
            # Perform the bulk operation
            es.bulk(body=curr_bulk)

            # Adding to success bulks
            increment_success()

            # Adding to size (in bytes)
            increment_size(sys.getsizeof(str(curr_bulk)))

        except:

            # Failed. incrementing failure
            increment_failure()


def generate_clients(es, indices, STARTED_TIMESTAMP):
    # Clients placeholder
    temp_clients = []

    # Iterate over the clients count
    for _ in range(NUMBER_OF_CLIENTS):
        temp_thread = Thread(target=client_worker, args=[es, indices, STARTED_TIMESTAMP])
        temp_thread.daemon = True

        # Create a thread and push it to the list
        temp_clients.append(temp_thread)

    # Return the clients
    return temp_clients


def generate_documents():
    # Documents placeholder
    temp_documents = []

    # Iterate over the clients count
    for _ in range(NUMBER_OF_DOCUMENTS):
        # Create a document and push it to the list
        temp_documents.append(generate_document())

    # Return the documents
    return temp_documents


def generate_indices(es):
    # Placeholder
    temp_indices = []

    # Iterate over the indices count
    for _ in range(NUMBER_OF_INDICES):
        # Generate the index name
        temp_index = generate_random_string(16)

        # Push it to the list
        temp_indices.append(temp_index)

        try:
            # And create it in ES with the shard count and replicas
            es.indices.create(index=temp_index, body={"settings": {"number_of_shards": 3,
                                                                   "number_of_replicas": 1}})

        except Exception as e:
            print("Could not create index. Is your cluster ok?")
            print(e)
            print("errorELK")
            print ("failure handling mechanisms - ticket, mail etc")
            sys.exit(1)

    # Return the indices
    return temp_indices


def cleanup_indices(es, indices):
    # Iterate over all indices and delete those
    for curr_index in indices:
        try:
            # Delete the index
            es.indices.delete(index=curr_index, ignore=[400, 404])

        except:
            print("Could not delete index: {0}. Continue anyway..".format(curr_index))


def print_stats(STARTED_TIMESTAMP):
    # Calculate elpased time
    elapsed_time = (int(time.time()) - STARTED_TIMESTAMP)

    # Calculate size in MB
    size_mb = total_size / 1024 / 1024

    # Protect division by zero
    if elapsed_time == 0:
        mbs = 0
    else:
        mbs = size_mb / float(elapsed_time)

    # Print stats to the user
    print("Elapsed time: {0} seconds".format(elapsed_time))
    print("")


def print_stats_worker(STARTED_TIMESTAMP):
    # Create a conditional lock to be used instead of sleep (prevent dead locks)
    lock = Condition()

    # Acquire it
    lock.acquire()

    # Print the stats every 30 seconds
    while (not has_timeout(STARTED_TIMESTAMP)) and (not shutdown_event.is_set()):

        # Wait for timeout
        lock.wait(30)

        # To avoid double printing
        if not has_timeout(STARTED_TIMESTAMP):
            # Print stats
            print_stats(STARTED_TIMESTAMP)


def main():
    clients = []
    all_indices = []
    auth = None 
    context = None

    # Set the timestamp
    STARTED_TIMESTAMP = int(time.time())

    for esaddress in args.es_address:
        print("")
        print("Starting initialization of {0}".format(esaddress))
        try:
            es = Elasticsearch(
                esaddress,
                http_auth=auth,
                ssl_context=context,
                timeout=60)
        except Exception as e:
            print("Could not connect to elasticsearch!")
            print(e)
            print("errorELK")
            print ("failure handling mechanisms - ticket, mail etc")
            sys.exit(1)

        # Generate docs
        documents_templates = generate_documents()
        fill_documents(documents_templates)

        print("Done!")
        print("Creating indices.. ")

        indices = generate_indices(es)
        all_indices.extend(indices)

        try:
            es.cluster.health(wait_for_status='green', master_timeout='600s', timeout='600s')
        except Exception as e:
            print("Cluster timeout....")
            print("Cleaning up created indices.. "),

            cleanup_indices(es, indices)
            continue

        print("Generating documents and workers.. ")  # Generate the clients
        clients.extend(generate_clients(es, indices, STARTED_TIMESTAMP))

        print("Done!")


    print("Starting the test. Will print stats every {0} seconds.".format(30))
    print("The test would run for {0} seconds, but it might take a bit more "
          "because we are waiting for current bulk operation to complete. \n".format(NUMBER_OF_SECONDS))

    # Run the clients!
    for d in clients:
        d.start()

    # Create and start the print stats thread
    stats_thread = Thread(target=print_stats_worker, args=[STARTED_TIMESTAMP])
    stats_thread.daemon = True
    stats_thread.start()

    for c in clients:
       while c.is_alive():
            try:
                c.join(timeout=0.1)
            except KeyboardInterrupt:
                print("")
                print("Ctrl-c received! Sending kill to threads...")
                shutdown_event.set()
                
                # set loop flag true to get into loop
                flag = True
                while flag:
                    #sleep 2 secs that we don't loop to often
                    sleep(2)
                    # set loop flag to false. If there is no thread still alive it will stay false
                    flag = False
                    # loop through each running thread and check if it is alive
                    for t in threading.enumerate():
                        # if one single thread is still alive repeat the loop
                        if t.isAlive():
                            flag = True
                            
                print("Cleaning up created indices.. "),
                cleanup_indices(es, all_indices)

    print("\nTest is done! Final results:")
    print_stats(STARTED_TIMESTAMP)

    print("Cleaning up created indices.. "),

    cleanup_indices(es, all_indices)

    print("LOADTEST-DONE")

try:
    main()

except Exception as e:
    print("")
    print(e.message)
    print("errorELK")
    print ("failure handling mechanisms - ticket, mail etc")
    sys.exit(1)
