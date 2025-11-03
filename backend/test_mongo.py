from pymongo import MongoClient
import certifi, ssl, pymongo

uri = "mongodb+srv://<user>:<pass>@avikgpt.8rwxnsk.mongodb.net/?retryWrites=true&w=majority&appName=AvikGPT"

print("PyMongo:", pymongo.version)
print("OpenSSL:", ssl.OPENSSL_VERSION)
print("CA file:", certifi.where())

client = MongoClient(
    uri,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=20000,
    connectTimeoutMS=20000,
)
print(client.admin.command("ping"))
