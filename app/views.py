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



def irods_put(username,passw,filen,path):
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
        env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        session.collections.create(path)
        session.data_objects.put(filen,path)
        print("irods put")


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
    projects = {
    "AGA000": {
        "name": "My First TB Project",
        "host": "Pathogen",
        "country": "ZA",
        "date":"27/03/2019"
        
    },
    "AGA001": {
        "name": "My Second TB Project",
        "host": "Human",
        "country": "ZA",
        "date":"27/03/2019"
    },
    "AGA002": {
       "name": "My Third TB Project",
        "host": "Human",
        "country": "ZA",
        "date":"27/03/2019"
    }
}




    return render_template("public/projects.html", projects=projects)

@app.route("/projects/<projectid>")
def project(projectid):
    projects = {
    "AGA000": {
        "genome_id": "1295720.3",
        "genome_name": "Mycobacterium tuberculosis TKK_02_0004",
        "genome_status": "WGS",
        "strain": "TKK_02_0004",
        "sample_source": "sputum",
        "sample_country": "ZA",
        "sample_geographic_location": "Tygerberg Hospital, Western Cape",
        "sample_collection_date": "2014-04-29",
        "sequencing_country": "USA",
        "sequencing_centre": "Broad Institute",
        "sequencing_platform": "Illumina",
        "sequencing_completion_date": "2014-12-08",
        "phenotypic_method": "MGIT960",
        "host_name": "Human",
        "contigs": "6",
        "genome_length": "4405060",
        "gc_content": "65.6",
        "date_uploaded": "2014-12-08"
    }

}

    item = None
    if projectid in projects:
        item = projects[projectid]
        return render_template("/public/project.html", projectid=projectid,item=item)
    else:
        return redirect("/")



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
    samples_list = []
    header_values = []
    # Iterate through each row in worksheet and fetch values into dict
    for rownum in range(0, sh.nrows):
        
        if rownum == 0:
            header_values = sh.row_values(rownum)
            
        else:
            sample = OrderedDict()
            row_values = sh.row_values(rownum)
            
            for i in range (len(header_values)):
                sample[header_values[i]] = row_values[i]
            samples_list.append(sample)
    # Serialize the list of dicts to JSON
    j = json.dumps(samples_list)

    return samples_list






@app.route("/files/<sampleid>")
def files(sampleid):

    files1 = convert_csv(app.config["PROJECT_UPLOADS"]+"/"+"Tuberculosis-SANBI"+"/metadata.xlsx")
    
    print(files1[0])
    print(files1[0]['sample_id'])

    item = None
    if sampleid == files1[0]['sample_id']:
        print("I AM HERE")
        item = files1[0]
        print (item)
        return render_template("/public/file.html", fileid=sampleid,item=item)
    else:
        return redirect("/")



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

                    req = request.form
                    
                    

                    with zipfile.ZipFile(app.config["PROJECT_UPLOADS"]+"/"+filename,"r") as zip_ref:
                        zip_ref.extractall(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/")
                    
                    

                    print("Project Unzipped")

                    for root, dirs, files in os.walk(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"):  
                        for filename in files:
                            irods_put("alice","alicepass",app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/"+filename,"/tempZone/home/alice/"+req['projectname']+"/")

                    

                    
                   
                    return redirect("/")

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)

        
    
    return render_template("public/upload_project.html", hide_button=False)


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
