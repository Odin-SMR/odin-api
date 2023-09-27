from .blueprints import register_blueprints
from .api import app

register_blueprints(app)
if __name__ == "__main__":
    app.run()