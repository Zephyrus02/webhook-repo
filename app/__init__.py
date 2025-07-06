from flask import Flask
from app.extensions import mongo
from app.webhook.routes import webhook
from app.api.routes import api
from app.main.routes import main


# Creating our flask app
def create_app():

    app = Flask(__name__)
    
    # Configure MongoDB
    app.config["MONGO_URI"] = "mongodb://localhost:27017/github_webhooks"
    mongo.init_app(app)
    
    # registering all the blueprints
    app.register_blueprint(webhook)
    app.register_blueprint(api)
    app.register_blueprint(main)
    
    return app
