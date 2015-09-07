"""A simple datamodel implementation"""

from flask import Flask, request, send_file
from flask import render_template, jsonify, abort
from flask.views import MethodView




class ViewIndex(MethodView):
    """View of all scans"""

    def get(self):
        return "hello"



class DataModel(Flask):
    def __init__(self, name):
        super(DataModel, self).__init__(name)
        self.add_url_rule(
            '/index.html',
            view_func=ViewIndex.as_view('index')
            )
def main():
    """Default function"""
    app = DataModel(__name__)
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    main()

