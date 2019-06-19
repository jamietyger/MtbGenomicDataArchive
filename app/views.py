from app import app
from flask import render_template
from flask import request, redirect
from flask import jsonify, make_response
from werkzeug.utils import secure_filename
from flask import send_file, send_from_directory, safe_join, abort
import xlrd
from collections import OrderedDict
import simplejson as json
import pprint
import shutil
from flask import Flask, url_for

import os
import zipfile

from irods.session import iRODSSession
from irods.models import Collection, DataObject



app.config["PROJECT_UPLOADS"] = "app/static/project/uploads"
app.config["ALLOWED_PROJECT_EXTENSIONS"] = ["ZIP"]
app.config["MAX_PROJECT_FILESIZE"] = 0.5 * 1024 * 1024

@app.route("/search/<searchitem>")
def search(searchitem):
    results = irods_search(searchitem)
    return render_template("public/search.html", searchitem=searchitem,results=results)

@app.route('/search', methods=['POST'])
def getsearch():
    print (request.form['searched'])
    return redirect(url_for('search', searchitem=request.form['searched']))


def humanbytes(B):
   'Return the given bytes as a human friendly KB, MB, GB, or TB string'
   B = float(B)
   KB = float(1024)
   MB = float(KB ** 2) # 1,048,576
   GB = float(KB ** 3) # 1,073,741,824
   TB = float(KB ** 4) # 1,099,511,627,776

   if B < KB:
      return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
   elif KB <= B < MB:
      return '{0:.2f} KB'.format(B/KB)
   elif MB <= B < GB:
      return '{0:.2f} MB'.format(B/MB)
   elif GB <= B < TB:
      return '{0:.2f} GB'.format(B/GB)
   elif TB <= B:
      return '{0:.2f} TB'.format(B/TB)

def irods_search(term):
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
                        if term in result[Collection.name] or term in result[DataObject.name]:
                                item =dict()
                                item["CollectionName"]=result[Collection.name].split('/')[-1] #add value to dictionary
                                item["CollectionID"]=irods_getCollection(result[Collection.name]).id
                                item["DataObjectName"]=result[DataObject.name] #add value to dictionary
                                item["DataObjectID"]=result[DataObject.id] #add value to dictionary
                                item["DataObjectSize"]=humanbytes(result[DataObject.size]) #add value to dictionary
                                print('{}/{} id={} size={}'.format(result[Collection.name], result[DataObject.name], result[DataObject.id], result[DataObject.size]))        
                                results.append(item)

    return results        


def getrepo():
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
                            item =dict()
                            item["CollectionName"]=result[Collection.name].split('/')[-1] #add value to dictionary
                            item["CollectionID"]=irods_getCollection(result[Collection.name]).id
                            item["DataObjectName"]=result[DataObject.name] #add value to dictionary
                            item["DataObjectID"]=result[DataObject.id] #add value to dictionary
                            item["DataObjectSize"]=humanbytes(result[DataObject.size]) #add value to dictionary
                                        
                            results.append(item)

    return results        

def irods_getCollection(path):
    username = "alice"  #login creds
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE'] #get irods environment file
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session: #create irods session in zone
            
            coll = session.collections.get(path) #get collection with path
    return coll

def irodsmetaJSON(metadata):
    metadict = dict()
    for meta in metadata: #for every metadata attribute
        metadict[meta.name]=meta.value  #add value to dictionary
    return metadict

def irods_createCollection(path,metadata):
    username = "alice" #login creds
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
            coll = session.collections.create(path) #create collection with path
            for key in metadata: #for every attribute in metadata
                coll.metadata.add(key,str(metadata[key]))  #add attribute, value to collection
            print("irods Collection Created Complete")


def irods_addObject(filen,Colpath):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        session.data_objects.put(filen,Colpath) #add file to Collection Path
        print("irods Added Object")


@app.route("/")
def index():
    return render_template("public/index.html")

@app.route("/about")
def about():
    return """
    <h1 style='color: red;'>I'm a red H1 heading!</h1>
    <p>This is a lovely little paragraph</p>
    <code>Flask is <em>awesome</em></code>
    """

@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():

    if request.method == "POST":

        req = request.form
        print(req)

        missing = list()

        for k, v in req.items():
            if v == "":
                missing.append(k)

        if missing:
            feedback = f"Missing fields for {', '.join(missing)}"
            return render_template("public/sign_up.html", feedback=feedback)

        return redirect(request.url)

    return render_template("public/sign_up.html")

@app.route("/projects")
def projects():
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
            
            coll = session.collections.get("/tempZone/home/alice") #get all collections 
         
            projects = dict() #make projects dict
            for col in coll.subcollections: 
                col2=session.collections.get(col.path) #get collection
                colmeta=col2.metadata.items() #get metadata
                metadata= irodsmetaJSON(colmeta) #convert metadata to JSON
                print("BEFORE")
                metadata['path']=app.config["PROJECT_UPLOADS"]+"/"+metadata['projectname']
                projects[col.id]=metadata #add to projects dict
    print(projects)
    return render_template("public/projects.html", projects=projects)

@app.route("/projects/<projectid>")
def project(projectid):
    print("SPECIFIC PROJECT")
    projectname,objects = get_project(projectid)
    print(objects)

    if objects:
        return render_template("/public/project.html", projectid=projectid,projectname=projectname,files=objects)
    else:
        return redirect("/")


def get_project(projectid):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        coll = session.collections.get("/tempZone/home/alice")
        objects = dict() #make projects dict
        for col in coll.subcollections:
            if (str(col.id) == str(projectid)):
                for obj in col.data_objects:
                    if len(obj.metadata.items())!=0:
                        objmeta=obj.metadata.items() #get metadata
                        metadata= irodsmetaJSON(objmeta) #convert metadata to JSON
                        metadata['filename']= obj.name
                        metadata['format']=obj.name.split('.')[-1]
                        metadata['filesize']= humanbytes(obj.size)
                        objects[obj.id]=metadata #add to projects dict
                return col.name,objects

@app.route("/download-project/<projectname>")
def download_project(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    print("HELLOT")
    shutil.make_archive(app.config["PROJECT_UPLOADS"]+"/"+projectname, 'zip', path)

    print(path+".zip")
    print(path[len("app/"):])

    try:
        return send_file(path[len("app/"):]+".zip", attachment_filename=projectname+".zip")
    except Exception as e:
	    return str(e)


@app.route("/download-file/<projectname>/<filename>")
def download_file(projectname,filename):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
  
    print(path+".zip")
    print(path[len("app/"):])

    try:
        return send_file(path[len("app/"):]+"/"+filename, attachment_filename=filename)
    except Exception as e:
	    return str(e)



@app.route("/download-metadata/<projectname>")
def download_metadata(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
  
    print(path+".zip")
    print(path[len("app/"):])

    try:
        return send_file(path[len("app/"):]+"/metadata.xlsx", attachment_filename=projectname+".xlsx")
    except Exception as e:
	    return str(e)

@app.route("/repository")
def repository():
    results = getrepo()
    return render_template("public/repository.html",results=results)


def convert_csv(filepath):
    wb = xlrd.open_workbook(filepath)
    sh = wb.sheet_by_index(0) 
    # List to hold dictionaries
    header_values = []
    # Iterate through each row in worksheet and fetch values into dict
    samples = dict()
    for rownum in range(0, sh.nrows):
        
        if rownum == 0:
            header_values = sh.row_values(rownum)
            
        else:
            samplemeta = dict()
            row_values = sh.row_values(rownum)
            
            for i in range (1,len(header_values)):
                samplemeta[header_values[i]] = row_values[i]
            samples[row_values[0]]=samplemeta
    # Serialize the list of dicts to JSON
    

    return samples


def chunk_dict(d, chunk_size):
    r = {}
    for k, v in d.items():
        if len(r) == chunk_size:
            yield r
            r = {}
        r[k] = v
    if r:
        yield r


@app.route("/projects/<projectid>/<fileid>")
def objectfile(projectid,fileid):
    
    filemetadata = get_file(projectid,fileid)
    filename=filemetadata['filename']
    filemetadata.pop('filename', None)
    filemetadata=list(chunk_dict(filemetadata, 4))

    if filemetadata:
        return render_template("/public/file.html",filedid=fileid,filename=filename,item=filemetadata)
    else:
        return redirect("/")


def get_file(projectid,fileid):
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        coll = session.collections.get("/tempZone/home/alice")
        objects = dict() #make projects dict
        for col in coll.subcollections:
            if (str(col.id) == str(projectid)):
                for obj in col.data_objects:
                    if (str(obj.id) == str(fileid)):
                        objmeta=obj.metadata.items() #get metadata
                        metadata= irodsmetaJSON(objmeta) #convert metadata to JSON
                        metadata['filename']= obj.name
                        objects=metadata #add to projects dict
                return objects
  





def allowed_project(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_PROJECT_EXTENSIONS"]:
        return True
    else:
        return False

def allowed_project_filesize(filesize):

    if int(filesize) <= app.config["MAX_PROJECT_FILESIZE"]:
        return True
    else:
        return False

### Uploading Project

#Takes in Zip file


@app.route("/upload-project", methods=["GET", "POST"])
def upload_project():
  
    if request.method == "POST": #If project being uploaded

        if request.files:
                
                project = request.files["project"] #get files

                if project.filename == "":  #check if project file has no name
                    print("No filename")
                    return redirect(request.url)

                if allowed_project(project.filename): #make sure project size is acceptable
                    filename = secure_filename(project.filename)

                    project.save(os.path.join(app.config["PROJECT_UPLOADS"], filename))

                    print("Project saved")    #SAVE PROJECT to Disk
                    print(app.config["PROJECT_UPLOADS"]+"/"+filename)

                    req = request.form #project metadata
                    
                    

                    with zipfile.ZipFile(app.config["PROJECT_UPLOADS"]+"/"+filename,"r") as zip_ref: #unzip file
                        zip_ref.extractall(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/")
                    
                    

                    print("Project Unzipped")
                    irods_createCollection("/tempZone/home/alice/"+req['projectname'],req) #create Project Collection with metadata submitted
                    print("Collection Created")

                    # create Collection for each sample in metadata
                    createsample_collections(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"+"metadata.xlsx","/tempZone/home/alice/"+req['projectname']+"/") 

                

                    return redirect("/")

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)

        
    
    return render_template("public/upload_project.html", hide_button=False)

def createsample_collections(metadata,collection):
    samples_metadata = convert_csv(metadata)
    username = "alice"   #login
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        for sample in samples_metadata: 
            print(collection+str(samples_metadata[sample]['sample_id']))
            irods_createCollection(collection+str(samples_metadata[sample]['sample_id']),samples_metadata[sample])
            #obj = session.data_objects.get(collection+sample) #get sample
            #for key in samples_metadata[sample]: #for every attribute in metadata
             #   obj.metadata.add(key,str(samples_metadata[sample][key]))  #add attribute, value to file





def addmetadata_objects(metadata,collection):
    files_metadata = convert_csv(metadata)
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        for files in files_metadata:
            print(collection+files)
            obj = session.data_objects.get(collection+files) #get file
            for key in files_metadata[files]: #for every attribute in metadata
                obj.metadata.add(key,str(files_metadata[files][key]))  #add attribute, value to file

