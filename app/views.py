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

import os
import zipfile

from irods.session import iRODSSession


app.config["PROJECT_UPLOADS"] = "app/static/project/uploads"
app.config["ALLOWED_PROJECT_EXTENSIONS"] = ["ZIP"]
app.config["MAX_PROJECT_FILESIZE"] = 0.5 * 1024 * 1024


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
            coll = session.collections.create(path) #create metadata with path
            for key in metadata: #for every attribute in metadata
                coll.metadata.add(key,metadata[key])  #add attribute, value to collection
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
                projects[col.id]=metadata #add to projects dict
    print(projects)
    return render_template("public/projects.html", projects=projects)

@app.route("/projects/<projectid>")
def project(projectid):
    
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
                        objects[obj.id]=metadata #add to projects dict
                return col.name,objects

@app.route("/repository")
def repository():

    files = {
    "FI0001": {
        "repository": "SANBI - South Africa",
        "project_id": "AGA000",
        "genome_status": "WGS",
        "format":"BAM",
        "size": "5.21 GB",
        "path": "/projects"
        
    },
    "FI0002": {
 "repository": "SANBI - South Africa",
        "project_id": "AGA000",
        "genome_status": "WGS",
        "format":"BAM",
        "size": "5.21 GB",
        "path": "/projects"
    },
    "FI0003": {
        "repository": "SANBI - South Africa",
        "project_id": "AGA000",
        "genome_status": "WGS",
        "format":"BAM",
        "size": "5.21 GB",
        "path": "/projects"
    }
    }





    return render_template("public/repository.html",files=files)


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
    filemetadata=list(chunk_dict(filemetadata, 4))

    if filemetadata:
        return render_template("/public/file.html",fileid=fileid,item=filemetadata)
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
                        objects=metadata #add to projects dict
                return objects
  



@app.route("/json", methods=["POST"])
def json_example():

    if request.is_json:

        req = request.get_json()

        response_body = {
            "message": "JSON received!",
            "sender": req.get("name")
        }

        res = make_response(jsonify(response_body), 200)

        return res

    else:

        return make_response(jsonify({"message": "Request body must be JSON"}), 400)

@app.route("/guestbook")
def guestbook():
    return render_template("public/guestbook.html")

@app.route("/guestbook/create-entry", methods=["POST"])
def create_entry():

    req = request.get_json()

    print(req)

    res = make_response(jsonify(req), 200)

    return res

@app.route("/query")
def query():

    if request.args:

        # We have our query string nicely serialized as a Python dictionary
        args = request.args

        # We'll create a string to display the parameters & values
        serialized = ", ".join(f"{k}: {v}" for k, v in request.args.items())

        # Display the query string to the client in a different format
        return f"(Query) {serialized}", 200

    else:

        return "No query string received", 200 

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

@app.route("/upload-project", methods=["GET", "POST"])
def upload_project():
  
    if request.method == "POST":

        if request.files:
                
                project = request.files["project"]

                if project.filename == "":
                    print("No filename")
                    return redirect(request.url)

                if allowed_project(project.filename):
                    filename = secure_filename(project.filename)

                    project.save(os.path.join(app.config["PROJECT_UPLOADS"], filename))

                    print("Project saved")
                    print(app.config["PROJECT_UPLOADS"]+"/"+filename)

                    req = request.form #project metadata
                    
                    

                    with zipfile.ZipFile(app.config["PROJECT_UPLOADS"]+"/"+filename,"r") as zip_ref: #unzip file
                        zip_ref.extractall(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/")
                    
                    

                    print("Project Unzipped")
                    irods_createCollection("/tempZone/home/alice/"+req['projectname'],req) #create Collection with metadata submitted
                    print("Collection Created")

                    for root, dirs,files in os.walk(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"):  #for every file in zip
                        print("WORKING WITH FILES") 
                        for filename in files:
                            irods_addObject(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"+filename,"/tempZone/home/alice/"+req['projectname']+"/") #add file to collection


                    addmetadata_objects(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"+"metadata.xlsx","/tempZone/home/alice/"+req['projectname']+"/")
                

                    return redirect("/")

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)

        
    
    return render_template("public/upload_project.html", hide_button=False)

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

@app.route("/get-image/<image_name>")
def get_image(image_name):

    try:
        return send_from_directory(app.config["CLIENT_IMAGES"], filename=image_name, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route("/get-report/<path:path>")
def get_report(path):

    try:
        return send_from_directory(app.config["CLIENT_REPORTS"], filename=path, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route("/jinja")
def jinja():
    # Strings
    my_name = "Julian"

    # Integers
    my_age = 30

    # Lists
    langs = ["Python", "JavaScript", "Bash", "Ruby", "C", "Rust"]

    # Dictionaries
    friends = {
        "Tony": 43,
        "Cody": 28,
        "Amy": 26,
        "Clarissa": 23,
        "Wendell": 39
    }

    # Tuples
    colors = ("Red", "Blue")

    # Booleans
    cool = True

    # Classes
    class GitRemote:
        def __init__(self, name, description, domain):
            self.name = name
            self.description = description 
            self.domain = domain

        def clone(self, repo):
            return f"Cloning into {repo}"

    my_remote = GitRemote(
        name="Learning Flask",
        description="Learn the Flask web framework for Python",
        domain="https://github.com/Julian-Nash/learning-flask.git"
    )

    # Functions
    def repeat(x, qty=1):
        return x * qty



    return render_template(
    "public/jinja.html", my_name=my_name, my_age=my_age, langs=langs,
    friends=friends, colors=colors, cool=cool, GitRemote=GitRemote, 
    my_remote=my_remote, repeat=repeat
    )
