"""A simple datamodel implementation"""

from flask import Flask, request, send_from_directory
from flask.views import MethodView, View
import os.path

fullpath=os.path.realpath(__name__)
folderpath=os.path.dirname(fullpath)
y=str.split(folderpath,'/datamodel')
databasepath=y[0]+'/lib/database'

class IndexView(View):
#    methods = ['GET']
    number_of_views = 0
    def dispatch_request(self):
        IndexView.number_of_views += 1
        return 'Hello, World! {0}'.format(IndexView.number_of_views)

class ApplicationView(MethodView):
    applist = list()

    def post(self):
        self.applist.append(request.form['name'])
        return 'registered'

    def get(self):
        if self.applist == []:
            return 'No apps registered'
        else:
            return "\n".join(self.applist)

class Scalar(View):
    methods=['GET']
    def dispatch_request(self):
        a=1
        return str(a)

class Vector(View):
    methods=['GET']
    def dispatch_request(self):
        a=[1,2,3,4,5,6.66]
        return str(a)

class CreateFile(View):
    methods=['POST']
    def dispatch_request(self):
        fname=request.form['filename']
        if os.path.isfile(databasepath+'/'+fname):
            return 'file already exists in database' 
        else:
           create_file(fname)
           return 'file created'

def create_file(filename):
    fname=databasepath+'/'+filename
    file=open(fname,'w')
    file.write('Some text and some numbers: 123455667')
    file.close()

class ListFilesDatabase(View):
    methods=['GET']
    def dispatch_request(self):
        lista=os.listdir(databasepath)
        return str(lista)

class GetFile(View):
    methods=['POST']
    def dispatch_request(self):
        fname=request.form['filename']
        if os.path.isfile(databasepath+'/'+fname):
            return send_from_directory(directory=databasepath,filename=fname)
        else:
            return 'file does not exist in database'

class Upload(View):
    methods=['POST']
    def dispatch_request(self):
        file=request.files['file']
        file.save(databasepath+'/'+file.filename)
        return 'file uploaded'

class DataModel(Flask):
    def __init__(self, name):
        super(DataModel, self).__init__(name)
        self.add_url_rule('/',view_func=IndexView.as_view('indexview'))
        self.add_url_rule('/applications',view_func=ApplicationView.as_view('applications'))
        self.add_url_rule('/list_files',view_func=ListFilesDatabase.as_view('listfilesdatabase'))
        self.add_url_rule('/get_file',view_func=GetFile.as_view('getfile'))
        self.add_url_rule('/create_file',view_func=CreateFile.as_view('createfile'))
        self.add_url_rule('/get_scalar',view_func=Scalar.as_view('scalar'))
        self.add_url_rule('/get_vector',view_func=Vector.as_view('vector'))
        self.add_url_rule('/upload',view_func=Upload.as_view('uploading'))

def main():
    app = DataModel(__name__)
    app.run(debug=True)

if __name__ == "__main__":
    main()

