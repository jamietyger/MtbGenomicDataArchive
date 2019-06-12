import os
from irods.session import iRODSSession
from irods.models import Collection, DataObject
from irods.query import SpecificQuery

           

def irods_generalQuery(path):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        query = session.query(Collection.name, DataObject.id, DataObject.name, DataObject.size)
        results = []
        for result in query:
                if "trash" not in result[Collection.name]:
                        if path in result[Collection.name] or path in result[DataObject.name]:
                                item =dict()
                                item["CollectionName"]=result[Collection.name] #add value to dictionary
                                item["DataObjectName"]=result[DataObject.name] #add value to dictionary
                                item["DataObjectID"]=result[DataObject.id] #add value to dictionary
                                item["DataObjectSize"]=result[DataObject.size] #add value to dictionary
                                print('{}/{} id={} size={}'.format(result[Collection.name], result[DataObject.name], result[DataObject.id], result[DataObject.size]))        
                                results.append(item)

    return results



def irods_specificQuery(term):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file) as session:
        sql = "select data_name, data_id from r_data_main join r_coll_main using (coll_id) where coll_name = '/tempZone/home/alice'"
        alias = 'list_data_name_id'
       
        query = SpecificQuery(session, sql,alias)
        query.register()
        for result in query:
                print('{} {}'.format(result[DataObject.name], alias,result[DataObject.id]))
        _ = query.remove()




searched= irods_specificQuery("my_tb")

 
