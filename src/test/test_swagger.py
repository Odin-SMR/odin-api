import unittest

from odinapi.utils.swagger import Swagger, SwaggerSpecView


class TestSwagger(unittest.TestCase):
    def test_parameters(self):
        """Test to add parameters to swagger spec"""
        swagger = Swagger()
        swagger.add_parameter(
            "testparam",
            "query",
            int,
            required=True,
            default=0,
            description="A test param",
        )
        param = swagger.get_parameters()["testparam"]
        expected = {
            "name": "testparam",
            "in": "query",
            "type": "integer",
            "default": 0,
            "description": "A test param",
        }
        self.assertEqual(param, expected)

        swagger = Swagger()
        swagger.add_parameter("testparam", "path", str, string_format="date")
        expected = {
            "name": "testparam",
            "in": "path",
            "required": True,
            "type": "string",
            "format": "date",
        }
        self.assertEqual(swagger.get_parameters()["testparam"], expected)

    def test_response(self):
        """Test creation of custom response spec"""
        swagger = Swagger()
        swagger.add_response("BadQuery", "Unsupported query", {"Error": str})
        response = swagger.get_response("BadQuery")
        expected = {
            "description": "Unsupported query",
            "schema": {
                "type": "object",
                "properties": {"Error": {"type": "string"}},
            },
        }
        self.assertEqual(response, expected)

    def test_type_response(self):
        """Test generation of response spec for a data type"""
        swagger = Swagger()
        swagger.add_type("testtype", {"key1": [float], "key2": str})
        response = swagger.get_type_response(
            "testtype", description="Return a test type", extra=str
        )
        expected = {
            "description": "Return a test type",
            "schema": {
                "type": "object",
                "properties": {
                    "Count": {"type": "integer"},
                    "Type": {"type": "string"},
                    "Data": {"$ref": "#/definitions/testtype"},
                    "extra": {"type": "string"},
                },
                "required": ["Data", "Type", "Count"],
            },
        }
        self.assertEqual(response, expected)

        # Test with is_list
        response = swagger.get_type_response(
            "testtype", description="Return a list of test type", is_list=True
        )
        expected = {
            "description": "Return a list of test type",
            "schema": {
                "type": "object",
                "properties": {
                    "Count": {"type": "integer"},
                    "Type": {"type": "string"},
                    "Data": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/testtype"},
                    },
                },
                "required": ["Data", "Type", "Count"],
            },
        }
        self.assertEqual(response, expected)

    def test_mixed_type_response(self):
        """Test generation of mixed type response spec"""
        swagger = Swagger()
        swagger.add_type("type1", {"key1": [float], "key2": str})
        swagger.add_type("type2", {"key1": str})
        response = swagger.get_mixed_type_response(
            [("type1", False), ("type2", True)], description="Return a mixed type"
        )
        expected = {
            "description": "Return a mixed type",
            "schema": {
                "properties": {
                    "Count": {"type": "integer"},
                    "Type": {"type": "string"},
                    "Data": {
                        "required": ["type1", "type2"],
                        "properties": {
                            "type1": {
                                "type": "object",
                                "required": ["Data", "Type", "Count"],
                                "properties": {
                                    "Count": {"type": "integer"},
                                    "Type": {"type": "string"},
                                    "Data": {"$ref": "#/definitions/type1"},
                                },
                            },
                            "type2": {
                                "type": "object",
                                "required": ["Data", "Type", "Count"],
                                "properties": {
                                    "Count": {"type": "integer"},
                                    "Type": {"type": "string"},
                                    "Data": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/definitions/type2",
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
        self.assertEqual(response, expected)

    def test_make_properties(self):
        """Test generation of properties spec"""
        properties = Swagger.make_properties(
            {
                "key1": int,
                "key2": [float],
                "subkey": {"key3": str},
                "subkey2": [{"key4": str}],
                "key5": [[float]],
            }
        )
        expected = {
            "type": "object",
            "properties": {
                "key1": {"type": "integer"},
                "key2": {"type": "array", "items": {"type": "number"}},
                "subkey": {
                    "type": "object",
                    "properties": {"key3": {"type": "string"}},
                },
                "subkey2": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"key4": {"type": "string"}},
                    },
                },
                "key5": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                },
            },
        }
        self.assertEqual(properties, expected)

    def test_get_path_definition(self):
        """Test generation of spec for a path/endpoint"""
        swagger = Swagger()
        swagger.add_parameter("param1", "path", str, string_format="date")
        swagger.add_parameter("param2", "query", int)
        swagger.add_type("type1", {"key1": str})
        swagger.add_response("BadQuery", "Unsupported query", {"Error": str})

        path = swagger.get_path_definition(
            ["test_tag"],
            ["param1", "param2"],
            {
                200: swagger.get_type_response("type1"),
                400: swagger.get_response("BadQuery"),
            },
            summary="A test path",
            description="This is a test path.",
        )
        expected = {
            "get": {
                "description": "This is a test path.",
                "parameters": [
                    {"$ref": "#/parameters/param1"},
                    {"$ref": "#/parameters/param2"},
                ],
                "responses": {
                    "200": {
                        "description": "",
                        "schema": {
                            "properties": {
                                "Count": {"type": "integer"},
                                "Type": {"type": "string"},
                                "Data": {"$ref": "#/definitions/type1"},
                            },
                            "required": ["Data", "Type", "Count"],
                            "type": "object",
                        },
                    },
                    "400": {
                        "description": "Unsupported query",
                        "schema": {
                            "type": "object",
                            "properties": {"Error": {"type": "string"}},
                        },
                    },
                },
                "summary": "A test path",
                "tags": ["test_tag"],
            }
        }
        self.assertEqual(path, expected)


class TestRuleToSwaggerPath:
    def test_static_rule(self):
        assert SwaggerSpecView.rule_to_swagger_path("/foo/bar", "v3") == "/foo/bar"

    def test_set_version(self):
        assert (
            SwaggerSpecView.rule_to_swagger_path("/<version>/foo/bar", "v3")
            == "/v3/foo/bar"
        )

    def test_rule_with_variable(self):
        assert SwaggerSpecView.rule_to_swagger_path("/foo/<bar>", "v3") == "/foo/{bar}"
