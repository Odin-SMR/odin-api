"""A simple datamodel implementation"""

from flask import Flask
from flask import request

applist = list()
app = Flask(__name__)

@app.route('/')
def index():
    """the first page"""
    return "Hello, World!"

@app.route('/applications', methods=['GET', 'POST'])
def apps():
    """register and display apps"""
    if request.method == 'POST':
        applist.append(request.form['name'])
        return 'registered'
    else:
        if applist == []:
            return 'No apps registered'
        else:
            return "\n".join(applist)


if __name__ == "__main__":
    app.run()
