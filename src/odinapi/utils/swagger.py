"""
Provide class for handling of swagger type definitions, responses and
parameters.

Example usage:

    from swagger import SWAGGER
    SWAGGER.add_parameter('myparam', 'path', str, required=True)
    SWAGGER.add_parameter('myparam2', 'query', str)
    SWAGGER.add_type('mytype_v4', {key1: str, key2: float})
    SWAGGER.add_type('mytype_v5', {key1: str, key2: [float]})
    SWAGGER.add_response('BadQuery', 'Unsupported query', {'Error': str})

    class MyView(BaseView):
        TAGS = ['level2']
        PARAMETERS = ['myparam', 'myparam2']
        RESPONSES_V4 = {
            200: SWAGGER.get_type_response('mytype_v4'),
            400: SWAGGER.get_response('BadQuery')}
        RESPONSES_V5 = {
            200: SWAGGER.get_type_response('mytype_v5', is_list=True),
            400: SWAGGER.get_response('BadQuery')}

        @register_versions('swagger', ['v4'])
        def _swagger_def(self, version):
            return SWAGGER.get_path_definition(
                self.TAGS, self.PARAMETERS, self.RESPONSES_V4)

        @register_versions('swagger', ['v5'])
        def _swagger_def_v5(self, version):
            return SWAGGER.get_definition(
                self.TAGS, self.PARAMETERS, self.RESPONSES_V5)
"""

import re

from flask import current_app, jsonify
from flask.views import MethodView
from odinapi.views.baseview import BaseView


class Swagger(object):
    """Class for handling of swagger type definitions, responses and
    parameters.

    See also http://swagger.io/specification/
    """

    TYPE2SWAGGER = {
        int: 'integer',
        float: 'number',
        basestring: 'string',
        unicode: 'string',
        str: 'string',
        list: 'array'
    }

    def __init__(self):
        self.types = {}
        self.responses = {}
        self.parameters = {}

    def get_parameters(self):
        return self.parameters

    def get_definitions(self):
        return self.types

    def get_responses(self):
        return self.responses

    def get_response(self, name):
        return self.responses[name]

    def get_path_definition(self, tags, parameters, responses, summary='',
                            description=''):
        """Return swagger GET definition for a path.

        Args:
          tags ([str]): List of tags for the path.
          parameters ([str]): List of parameter names.
          responses ({int: dict}): Dict with status code as key and response
            spec as value.
          summary (str): Short summary of the path.
          description (str): Description of the path.
        """
        for param in parameters:
            if param not in self.parameters:
                raise ValueError('Missing parameter definition for %s' % param)
        definition = {
            'description': description,
            'parameters': [{'$ref': '#/parameters/%s' % param}
                           for param in parameters],
            'responses': {str(status_code): response
                          for status_code, response in responses.items()},
            'summary': summary,
            'tags': tags,
        }
        return {'get': definition}

    def get_type_response(self, type_name, description='', is_list=False,
                          **kwargs):
        """Return swagger response definition for a certain type.

        Args:
          type_name (str): The return type of the response.
          description (str): The response description.
          is_list (bool): Whether the response contains a list of data.
          **kwargs: Extra data added to the standard return format.

        The type definitions will be wrapped into the odin api standard
        return format:

            {
              Data: {...}, # from type name
              Type: string,
              Count: int
              kwarg1: kwargs[kwarg1],
              ...
            }

        The swagger definition will look like this:

            {
              "description": <description>,
              "schema": {...}
            }
        """
        data = self.types[type_name]
        if is_list:
            data = {'type': 'array', 'items': data}

        schema = self.make_properties(kwargs)
        schema['required'] = ['Data', 'Type', 'Count']
        schema['properties'].update({
            'Type': {'type': 'string'},
            'Count': {'type': 'integer'},
            'Data': data})
        return {'description': description, 'schema': schema}

    def get_mixed_type_response(self, types, description=''):
        """Return swagger response definition for a mixed type.

        Args:
          types ([(str, bool)]): List of tuples with type name and a boolean
            whether it is a list or not.
          description (str): The response description.

        The type definitions will be wrapped into the odin api standard
        return format:

            {
              Data: {...}, # from the types
              Type: string,
              Count: int
            }

        The swagger definition will look like this:

            {
              "description": <description>,
              "schema": {...}
            }
        """
        schema = {'properties': {
            'Type': {'type': 'string'},  # TODO: Will always be 'mixed'
            'Count': {'type': 'integer'},  # TODO: Will always be None
            'Data': {
                'required': [type_name for type_name, _ in types],
                'properties': {
                    typ: self.get_type_response(typ, is_list=is_list)['schema']
                    for typ, is_list in types}
            }
        }}
        return {'description': description, 'schema': schema}

    def add_type(self, name, properties):
        """Add a type definition.

        Args:
          name (string): Name of the type.
          properties (dict): Dict that maps key name to type, see
            `make_properties`.
        """
        if name in self.types:
            raise ValueError('The type %r already exists' % name)
        self.types[name] = self.make_properties(properties)

    def add_parameter(self, name, location, typ, required=False,
                      string_format=None, default=None, description=None,
                      collection_format=None):
        """Add an endpoint parameter.

        Args:
          name (str): Parameter name.
          location (str): Parameter location, for example 'query' and 'path'.
          typ (type): Parameter value type.
          required (bool): True if the parameter is required.
          string_format (str): Format if the type is string. Example: 'date'.
          default (?): The default value of the parameter.
          description (string): Parameter description.
          collection_format (string): Format used for adding elements in query.

        The swagger definition will look like this:

            {
              "collectionFormat": <collection_format>,
              "default": <default>,
              "description": <description>,
              "format": <string_format>,
              "in": <location>,
              "name": <name>,
              "required": <required>,
              "type": <typ>,
            }
        """
        if name in self.parameters:
            raise ValueError('The parameter %r already exists' % name)
        self.parameters[name] = {
            'name': name,
            'in': location,
            'type': self.get_swagger_type(typ)
        }
        if default is not None:
            self.parameters[name]['default'] = default
        if required and default is None:
            self.parameters[name]['required'] = True
        if string_format:
            self.parameters[name]['format'] = string_format
        if description:
            self.parameters[name]['description'] = description
        if isinstance(typ, list):
            if collection_format:
                self.parameters[name]['collectionFormat'] = collection_format
            self.parameters[name]['items'] = self.make_properties(typ[0])

    def add_response(self, name, description, properties):
        """Add a swagger response with custom schema.

        Args:
          name (str): The name of the response.
          description (str): Response description.
          properties (dict): Dict that maps key name to type for the
            response data.

        The swagger definition will look like this:

            {
              "description": <description>,
              "schema": {...}
            }

        where schema is generated from the properties. See `make_properties`
        for a properties example.
        """
        if name in self.responses:
            raise ValueError('The response %r already exists' % name)
        self.responses[name] = {
            'description': description,
            'schema': self.make_properties(properties)
        }

    @staticmethod
    def make_properties(properties):
        """Create swagger schema from the properties.

        Args:
          properties (type): Dict, list or a supported type.

        Example:

            {
              'key1': int,
              'key2': [float],
              'subkey': {'key3': str},
              'subkey2': [{'key4': str}]
            }

        These properties will result in this swagger schema:

            {
              "properties": {
                "key1": {"type": "integer"},
                "key2": {
                  "type": "array",
                  "items": {"type": "number"}
                },
                "subkey": {
                  "properties": {"key3": {"type": "string"}}
                },
                "subkey2": {
                  "type": "array",
                  "items": {
                    "properties": {"key4": {"type": "string"}}
                  }
                }
              }
            }
        """
        if isinstance(properties, dict):
            return {'properties': {
                key: Swagger.make_properties(val)
                for key, val in properties.items()}}
        elif isinstance(properties, list):
            return {
                "type": "array",
                "items": Swagger.make_properties(properties[0])}
        else:
            return {"type": Swagger.get_swagger_type(properties)}

    @staticmethod
    def get_swagger_type(typ):
        if isinstance(typ, list):
            return Swagger.TYPE2SWAGGER[list]
        else:
            return Swagger.TYPE2SWAGGER[typ]


SWAGGER = Swagger()


def is_base_view(endpoint):
    """Return True if the endpoint handler is a BaseView."""
    klass = endpoint.__dict__.get('view_class', None)
    try:
        return issubclass(klass, BaseView)
    except TypeError:
        return False


class SwaggerSpecView(MethodView):
    """View for generating swagger spec from the BaseView endpoints."""

    def __init__(self, title, description='', terms_of_service=''):
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        super(SwaggerSpecView, self).__init__()

    @staticmethod
    def rule_to_swagger_path(rule):
        """/path/<param> -> /path/{param}"""
        rule = str(rule)
        for arg in re.findall('(<([^<>]*:)?([^<>]*)>)', rule):
            rule = rule.replace(arg[0], '{%s}' % arg[2])
        return rule

    def collect_path_specifications(self, version):
        paths = {}
        for rule in current_app.url_map.iter_rules():
            endpoint = current_app.view_functions[rule.endpoint]
            if is_base_view(endpoint):
                path = self.rule_to_swagger_path(rule)
                path_spec = endpoint.view_class().swagger_spec(version)
                if path_spec:
                    paths[path] = path_spec
        return paths

    def get(self, version):
        """GET swagger definition for a certain version of the API."""
        param = SWAGGER.get_parameters()
        param['version']['default'] = version
        return jsonify({
            "swagger": "2.0",
            "info": {
                "version": version,
                "title": self.title,
                "description": self.description,
                "termsOfService": self.terms_of_service,
            },
            "basePath": '/rest_api/{}/'.format(version),
            "paths": self.collect_path_specifications(version),
            "definitions": SWAGGER.get_definitions(),
            "parameters": param,
            "responses": SWAGGER.get_responses()
        })
