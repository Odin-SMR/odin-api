""" testing webapp"""
from datamodel.datamodel import DataModel
#from datamodel import DataModel
import unittest, tempfile
import io, os.path

fullpath=os.path.realpath(__name__)
folderpath=os.path.dirname(fullpath)
y=str.split(folderpath,'/datamodel')
databasepath=y[0]+'/lib/database/test'

class FlaskrTestCase(unittest.TestCase):
    """Flask testcase"""

    def setUp(self):
        self.data = DataModel(__name__)
        self.app = self.data.test_client()

#1
    def test_index(self):
        """testing index"""
        response = self.app.get('/')
        self.assertEqual(b'Hello, World! 1', response.data)

#2
    def Xtest_two_applications_reg(self):
        """adding two apps"""
        response = self.app.post(
            '/applications',
            data=dict(name="prod1")
        )
        response = self.app.post(
            '/applications',
            data=dict(name="prod2")
        )
        response = self.app.get('applications')
        self.assertEqual(b'prod1\nprod2', response.data)

#3
    def test_three_applications_reg(self):
        """adding two apps"""
        response = self.app.post(
            '/applications',
            data=dict(name="prod1")
        )
        response = self.app.post(
            '/applications',
            data=dict(name="prod2")
        )
        response = self.app.post(
            '/applications',
            data=dict(name="prod3")
        )
        response = self.app.get('applications')
        self.assertEqual(b'prod1\nprod2\nprod3', response.data)

#4
    def test_no_applications_reg(self):
        """testing no appsregistered"""
        response = self.app.get('applications')
        self.assertEqual(b'No apps registered', response.data)

#5
    def test_get_scalar(self):
        """testing the transmission of the scalar 1"""
        response = self.app.get('/get_scalar')
        self.assertEqual(b'1',response.data)

#6
    def test_get_vector(self):
        """testing the transmission of a vector"""
        response = self.app.get('/get_vector')
        self.assertEqual(b'[1, 2, 3, 4, 5, 6.66]',response.data)

#7 
    def test_list_files(self):
        """testing to list the files in the database (actually just tests that the URI doesn't respond with an error...)"""
        response = self.app.get('/list_files')
        self.assertEqual(type(response.data),bytes)

#8 
    def test_create_file(self):
        """Tests the URI that creates a file"""
        tf=tempfile.NamedTemporaryFile()
        fn=tf.name
        filename=str.split(fn,'tmp/')[1]    
        response=self.app.post('/create_file',data={'filename':filename})
        self.assertEqual(b'file created',response.data)

#9 
    def test_download_file(self):
        """Tests to create a file on the server and download it"""
        tf=tempfile.NamedTemporaryFile()
        fn=tf.name
        filename=str.split(fn,'tmp/')[1]    
        response=self.app.post('/create_file',data={'filename':filename})
        response=self.app.post('/get_file',data={'filename':filename})
        f=open(databasepath+'/'+filename,'wb')
        f.write(response.data)
        f.close
        self.assertTrue(os.path.isfile(databasepath+'/'+filename))

#10 
    def test_upload_file(self):
        """Tests to create a local file and upload it"""
        tf=tempfile.NamedTemporaryFile()
        fn=tf.name
        filename=str.split(fn,'tmp/')[1]    
        f=open(databasepath+'/'+filename,'wb')
        test_string=b'this is just a test string'
        f.write(test_string)
        f.close
        f=open(databasepath+'/'+filename,'rb')
        response=self.app.post('/upload',data={'file':(f,filename)})
        self.assertEqual(response.data,b'file uploaded')


if __name__ == '__main__':
    unittest.main()
