"""Tests for Swagger/OpenAPI documentation via flasgger"""

import unittest


class TestSwagger(unittest.TestCase):
    def test_flasgger_installed(self):
        """Test that flasgger is installed and can be imported"""
        try:
            import flasgger

            self.assertTrue(True)
        except ImportError:
            self.fail("flasgger should be installed")

    def test_app_has_swagger(self):
        """Test that the Flask app has Swagger initialized"""
        from odinapi.api import create_app, TestConfig

        app = create_app(TestConfig())
        # Check that flasgger has been initialized
        self.assertTrue(hasattr(app, "swag"))
