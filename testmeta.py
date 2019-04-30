import os
from irods.session import iRODSSession
def irods_getCollection1(path):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
            
            coll = session.collections.get(path)
            print (coll.id)
            print("irods Collection Metadata View")

            metadict = dict()
            for meta in coll.metadata.items():
                metadict[meta.name]=meta.value

            print(metadict)
           

def irods_getCollection(path):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
            
            coll = session.collections.get(path)
            print (coll.id)
            print("irods Collection Metadata View")

            metadict = dict()
            for meta in coll.metadata.items():
                metadict[meta.name]=meta.value

            print(metadict)
            coll.metadata.add("KAK","SHEV") 


irods_getCollection("/tempZone/home/alice/my_tb")