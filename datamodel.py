"""A simple datamodel implementation"""

from flask import Flask, request
from flask.views import MethodView, View


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

class DataModel(Flask):

    def __init__(self, name):
        super(DataModel, self).__init__(name)
        self.add_url_rule(
            '/',
            view_func=IndexView.as_view('indexview'))
        self.add_url_rule(
            '/applications',
            view_func=ApplicationView.as_view('applications'))

def main():
    app = DataModel(__name__)
    app.run(debug=True)

if __name__ == "__main__":
    main()
