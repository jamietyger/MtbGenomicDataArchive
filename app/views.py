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
from os.path import basename

import pandas as pd

import os
import zipfile
from zipfile import ZipFile

from irods.session import iRODSSession
from irods.models import Collection, DataObject, CollectionMeta
from irods.column import Criterion

from datetime import datetime #date time import


app.config["PROJECT_UPLOADS"] = "app/static/project/uploads"
app.config["PROJECT_DOWNLOADS"] = "app/static/project/downloads"
app.config["ALLOWED_PROJECT_EXTENSIONS"] = ["ZIP"]
app.config["MAX_PROJECT_FILESIZE"] = 0.5 * 1024 * 1024

@app.route("/search/<searchitem>")
def search(searchitem):
    results = irods_search(searchitem)
    #print(results)
    return render_template("public/search.html", searchitem=searchitem,results=results)

@app.route('/search', methods=['POST'])
def getsearch():
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
        query = session.query(Collection.name,DataObject)
        results = {}
        for result in query:
            if "trash" not in result[Collection.name]:
                if term in result[Collection.name]: #or term in result[CollectionMeta.value]:
                    item =dict()
                    item["CollectionName"]=result[Collection.name].split('/')[-1] #add value to dictionary
                    item["CollectionPath"]=result[Collection.name]
                    item["CollectionID"]=irods_getCollection(result[Collection.name]).id
                    item["CollectionOriginID"]=irods_getCollection(item["CollectionPath"].rsplit('/', 1)[0]).id
                    item["DataObjectName"]=result[DataObject.name] #add value to dictionary
                    item["DataObjectID"]=result[DataObject.id] #add value to dictionary
                    item["DataObjectSize"]=humanbytes(result[DataObject.size]) #add value to dictionary       
                    results[result[DataObject.id]]=item
     
                         
        queryZone = session.query(Collection, CollectionMeta).filter(Criterion('=', CollectionMeta.name, 'repository')).filter(Criterion('like', CollectionMeta.value, term))
        for result in queryZone:
            if "trash" not in result[Collection.name]:
                item =dict()
                item["CollectionName"]=result[Collection.name].split('/')[-1] #add value to dictionary
                item["CollectionID"]=irods_getCollection(result[Collection.name]).id
                item["CollectionPath"]=result[Collection.name]
                col2 = session.collections.get(result[Collection.name])#use collection name to get collection data
                colmeta = col2.metadata.items()
                metadata= irodsmetaJSON(colmeta) #convert metadata to JSON
                item["CollectionHost"]=metadata["host"]
                item["CollectionDate"]=metadata["dateAdded"]
                item["CollectionOriginID"]=irods_getCollection(result[Collection.name]).id      
                results[result[Collection.name]]=item
    

    return results        

'''
Previous getrepo() function

def getrepo():
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        query = session.query(Collection, DataObject)
        results = {}
        for result in query:
            if "trash" not in result[Collection.name]:
                item =dict()
                item["CollectionName"]=result[Collection.name].split('/')[-1] #add value to dictionary
                item["CollectionPath"]=result[Collection.name]
                item["CollectionID"]=irods_getCollection(result[Collection.name]).id
                item["CollectionOriginID"]=irods_getCollection(item["CollectionPath"].rsplit('/', 1)[0]).id
                item["DataObjectName"]=result[DataObject.name] #add value to dictionary
                item["DataObjectID"]=result[DataObject.id] #add value to dictionary
                item["DataObjectSize"]=humanbytes(result[DataObject.size]) #add value to dictionary  
                results[result[DataObject.id]]=item

    return results
'''
def getrepo():
    username = "alice"
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        coll = session.collections.get("/tempZone/home/alice") #get all collections 
         
        results = dict() #make projects dict
        for col in coll.subcollections: 
            col2=session.collections.get(col.path) #get collection
            #print(col.path)
            colmeta=col2.metadata.items() #get metadata
            metadata= irodsmetaJSON(colmeta) #convert metadata to JSON
            metadata['path']=app.config["PROJECT_UPLOADS"]+"/"+metadata['projectname']
            results[col.id]=metadata #add to projects dict

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
                metadata['path']=app.config["PROJECT_UPLOADS"]+"/"+metadata['projectname']
                projects[col.id]=metadata #add to projects dict
                #print(metadata)
    return render_template("public/projects.html", projects=projects)

@app.route("/projects/<projectid>")
def project(projectid):
    projectname,objects,thePath = get_project(projectid)
    df = pd.read_excel(app.config["PROJECT_UPLOADS"]+"/"+projectname+"/metadata.xlsx")#using pandas to read xslx from path
    dict = df.to_dict()#convert excel xlsx to python dictionary
    #print(dict)
    if objects:
        return render_template("/public/project.html", projectid=projectid,projectname=projectname,samples=dict)
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
        #print(coll.subcollections)

        for col in coll.subcollections:
            #print(col.id)
            if (str(col.id) == str(projectid)):
                #print(col.path)
                col2=session.collections.get(col.path) #get collection
                colmeta=col2.metadata.items() #get metadata
                metadata= irodsmetaJSON(colmeta) #convert metadata to JSON
                metadata['path']=app.config["PROJECT_UPLOADS"]+"/"+metadata['projectname']
                objects[col.id]=metadata #add to objects dict
                return col.name,objects,col.path

@app.route("/projects/<projectid>/<sampleid>")
def objectfile(projectid,sampleid):
    projectname,objects,origin = get_project(projectid)
    df = pd.read_excel(app.config["PROJECT_UPLOADS"]+"/"+projectname+"/metadata.xlsx")#using pandas to read xslx from path
    dict = df.to_dict()#convert excel xlsx to python dictionary
    print(dict)
    

    if objects:
        return render_template("/public/sample.html",sampleid=sampleid,samplename=projectname,files=dict, origin=origin)
    else:
        return redirect("/")

'''
Previous get_project(projectid)

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
        #print(coll.subcollections)

        for col in coll.subcollections:
            print(col.id)
            if (str(col.id) == str(projectid)):
                
                for sample in col.subcollections:
                  
                    print(col)
                    if len(sample.metadata.items())!=0:
                        objmeta=sample.metadata.items() #get metadata
                        metadata= irodsmetaJSON(objmeta) #convert metadata to JSON
                        metadata['samplename']= sample.name
                        objects[sample.id]=metadata #add to projects dict
                return col.name,objects
'''


@app.route("/download-project/<projectname>")
def download_project(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
 
    shutil.make_archive(app.config["PROJECT_UPLOADS"]+"/"+projectname, 'zip', path)



    try:
        return send_file(path[len("app/"):]+".zip", attachment_filename=projectname+".zip")
    except Exception as e:
	    return str(e)


@app.route("/download-sample/<projectname>/<samplename>")
def download_samplet(projectname,samplename):
    colpath="/tempZone/home/alice/"+projectname+"/"+samplename
    
    col = irods_getCollection(colpath)
    objmeta=col.metadata.items() #get metadata
    metadata= irodsmetaJSON(objmeta) #convert metadata to JSON
    files =[metadata['BAMfilename'],metadata['VCFfilename'],metadata['FASTQ_r1filename'],metadata['FASTQ_r2filename']]
    filepath=app.config["PROJECT_UPLOADS"]+"/"+projectname
    dfilepath=app.config["PROJECT_DOWNLOADS"]
    #create a ZipFile object
    zipObj = ZipFile(dfilepath+"/"+samplename+".zip", 'w')
 
    # Add multiple files to the zip
    for sfile in files:
        if sfile != "NULL":
            zipObj.write(filepath[:]+"/"+sfile,basename(filepath[:]+"/"+sfile))
  
 
    # close the Zip File
    zipObj.close()
   
    try:
        return send_file(dfilepath[len("app/"):]+"/"+samplename+".zip", attachment_filename=samplename+".zip")
    except Exception as e:
	    return str(e)

@app.route("/download-samplefile/<projectname>/<samplefilename>")
def download_samplefile(projectname,samplefilename):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname

    try:
        return send_file(path[len("app/"):]+"/"+samplefilename, attachment_filename=samplefilename)
    except Exception as e:
	    return str(e)

@app.route("/download-metadata/<projectname>")
def download_metadata(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    try:
        return send_file(path[len("app/"):]+"/metadata.xlsx", attachment_filename=projectname+".xlsx")
    except Exception as e:
	    return str(e)

@app.route("/download-bamdata/<projectname>")
def download_bamdata(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    try:
        return send_file(path[len("app/"):]+"/SAWC123.bam", attachment_filename="SAWC123.bam")
    except Exception as e:
	    return str(e)

@app.route("/download-vcfdata/<projectname>")
def download_vcfdata(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    try:
        return send_file(path[len("app/"):]+"/SAWC123.vcf", attachment_filename="SAWC123.vcf")
    except Exception as e:
	    return str(e)

@app.route("/download-fastq-r1data/<projectname>")
def download_fastq_r1data(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    try:
        return send_file(path[len("app/"):]+"/SAWC123_r1.fastq", attachment_filename="SAWC123_r1.fastq")
    except Exception as e:
	    return str(e)

@app.route("/download-fastq-r2data/<projectname>")
def download_fastq_r2data(projectname):
    path=app.config["PROJECT_UPLOADS"]+"/"+projectname
    print(path)
    try:
        return send_file(path[len("app/"):]+"/SAWC123_r2.fastq", attachment_filename="SAWC123_r2.fastq")
    except Exception as e:
	    return str(e)

@app.route("/repository")
def repository():
    results = getrepo()
    #print(results)
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
            
            for i in range (0,len(header_values)):
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

'''
Previous

@app.route("/projects/<projectid>/<sampleid>")
def objectfile(projectid,sampleid):
    
    samplemetadata = get_sample(projectid,sampleid)
    samplename=samplemetadata['samplename']
    origin = samplemetadata['origin'].split('/')[-2]
    files ={}
    if samplemetadata['BAMfilename']!="NULL":
        files['BAM File']=samplemetadata['BAMfilename']
    if samplemetadata['VCFfilename']!="NULL":
        files['VCF File']=samplemetadata['VCFfilename']
    if samplemetadata['FASTQ_r1filename']!="NULL":
        files['FASTQ - r1']=samplemetadata['FASTQ_r1filename']
    if samplemetadata['FASTQ_r2filename']!="NULL":
        files['FASTQ - r2']=samplemetadata['FASTQ_r2filename']
   
    samplemetadata.pop('samplename', None)
    samplemetadata=list(chunk_dict(samplemetadata, 4))

    if samplemetadata:
        return render_template("/public/sample.html",sampleid=sampleid,samplename=samplename,item=samplemetadata,files=files,origin=origin)
    else:
        return redirect("/")
'''



def get_sample(projectid,fileid):
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
                for sample in col.subcollections:
                    if (str(sample.id) == str(fileid)):
                        objmeta=sample.metadata.items() #get metadata
                        metadata= irodsmetaJSON(objmeta) #convert metadata to JSON
                        metadata['samplename']= sample.name
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

    date = datetime.now() #date object for date added    
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
                    createsample_collections(app.config["PROJECT_UPLOADS"]+"/"+req['projectname']+"/","/tempZone/home/alice/"+req['projectname']+"/") 

                

                    return redirect("/")

                else:
                    print("That file extension is not allowed")
                    return redirect(request.url)

        
    
    return render_template("public/upload_project.html", hide_button=False, date_time=str(date))

def createsample_collections(originpath,collection):
    samples_metadata = convert_csv(originpath+"metadata.xlsx")
    
    username = "alice"   #login
    passw="alicepass"
    try:
        env_file = os.environ['IRODS_ENVIRONMENT_FILE']
    except KeyError:
            env_file = os.path.expanduser('~/.irods/irods_environment.json')
    with iRODSSession(irods_env_file=env_file ,host='localhost', port=1247, user=username, password=passw, zone='tempZone') as session:
        for sample in samples_metadata: 
            col_path=collection+str(samples_metadata[sample]['sample_id'])

            samples_metadata[sample]['origin']=collection
            irods_createCollection(col_path,samples_metadata[sample])

            if str(samples_metadata[sample]['BAMfilename'])!="NULL":
                session.data_objects.put(originpath+str(samples_metadata[sample]['BAMfilename']),col_path+"/")

            if str(samples_metadata[sample]['VCFfilename'])!="NULL":
                session.data_objects.put(originpath+str(samples_metadata[sample]['VCFfilename']),col_path+"/")

            if str(samples_metadata[sample]['FASTQ_r1filename'])!="NULL":
                session.data_objects.put(originpath+str(samples_metadata[sample]['FASTQ_r1filename']),col_path+"/")

            if str(samples_metadata[sample]['FASTQ_r2filename'])!="NULL":
                session.data_objects.put(originpath+str(samples_metadata[sample]['FASTQ_r2filename']),col_path+"/")
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
            obj = session.data_objects.get(collection+files) #get file
            for key in files_metadata[files]: #for every attribute in metadata
                obj.metadata.add(key,str(files_metadata[files][key]))  #add attribute, value to file

