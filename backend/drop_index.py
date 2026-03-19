import pymongo
import certifi

uri = "mongodb+srv://dravidsharathreddy:Dravid%40000@watchoutcluster.xnjv1it.mongodb.net/?appName=WatchoutCluster"
client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
db = client["watchout"]  # Actual DB name used by the backend
cache = db["places_cache"]

try:
    cache.drop_index("place_id_1")
    print("Successfully dropped place_id_1 index")
except Exception as e:
    print(f"Error dropping index: {e}")

client.close()
