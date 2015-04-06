""" testing webapp"""
from datamodel.datamodel import DataModel
import unittest

class FlaskrTestCase(unittest.TestCase):
    """Flask testcase"""

    def setUp(self):
        self.data = DataModel(__name__)
        self.app = self.data.test_client()

    def test_index(self):
        """testing index"""
        response = self.app.get('/')
        self.assertEqual(b'Hello, World! 1', response.data)

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


    def test_no_applications_reg(self):
        """testing no appsregistered"""
        response = self.app.get('applications')
        self.assertEqual(b'No apps registered', response.data)

if __name__ == '__main__':
    unittest.main()
