from flask import Flask, render_template #flask is the framework while Flask is a python class
app = Flask(__name__) #create instance of flask - name is special variable
@app.route('/') #mapped to home url
def home():
    return render_template('index.html')

@app.route('/projects') #mapped to home url
def projects():
    return render_template('projects.html')

@app.route('/projects/<project_id>')
def project_page(project_id):
   return render_template('project.html', projectid = project_id)


@app.route('/repository') #mapped to home url
def repository():
    return render_template('repository.html')

@app.route('/repository/files/<file_id>')
def file_page(file_id):
   return render_template('file.html', fileid = file_id)




if __name__ == '__main__': #main is assigned to script when executed. If elsewhere script called hello.py
    app.run(debug=True) #to trace errors but false in production
