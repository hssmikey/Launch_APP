from flask import Flask, request
# from pymongo import *
import os, sys, subprocess
from docker_helper import create_image, clone_repo, find_dockerfiles
from kubernetes_helper import *
import logging
#import config
import json
import requests

app = Flask(__name__)
app.secret_key = "SUPER SECRET KEY"


logging.basicConfig(filename="backend.log", format='%(levelname)s: %(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# try:
#     client = MongoClient("mongodb+srv://{}:{}@launch-emlpr.gcp.mongodb.net/LaunchDB?retryWrites=true&w=majority".format(config.username,config.password))
#     db = client['LaunchDB']
#     users = db.users
#     logger.info("mongodb set up complete")
#     logger.info("setup users collection")
# except:
#     logger.warning("no connection to mongodb")

try:
    logger.info("Docker username set by environment variables: {}".format(os.environ['DOCKERUSER']))
except:
    logger.warning("Docker username set by hard-coded value: {}".format('stolaunch'))

config_location = None

@app.route('/')
def home():
    logger.debug("GET request to '/'")
    return ("<h1>Hello, World!</h1>")

@app.route('/api/<query>')
def api(query):
    logger.debug("GET request to '/api/{}".format(query))
    return("Placeholder")
# finds all objects in database, then makes jsonfile with all objects
# @app.route('/api/getAll',methods=['GET'])
# def getAllObj():
#     logger.debug("GET request to '/api/getAll")
#     json_data = db.users.find()
#     writeTOJSONFile(json_data)
# def writeTOJSONFile(json_data):
#     file = open("all_objects.json", "w")
#     json_docs = []
#     file.write('[')
#     for document in json_data:
#         json_docs = json.dumps(document, default=json_util.default)
#         json_docs.append(json_docs)
#         file.write(json.dumps(document))
#         file.write(',')
#     file.write(']')
#     return json_docs
# Responds to POST requests that contain JSON data
@app.route('/deploy', methods=['POST'])
@app.route('/deploy/<update>')
def deploy(update=None):
    if request.method == "POST":
        
        json_data = request.get_json()
        key = json_data['key']
        logger.info("Value of the key is: {}".format(key))
        user = json_data['user']
        logger.info("Value of user is {}".format(user))
        repo = json_data['repo']
        db = json_data['db']
        logger.debug("User selected database: {}".format(db))
        images = []     
        if clone_repo(user, repo):
            dockerfiles = find_dockerfiles(user, repo)
            for path_to_dockerfile in dockerfiles:
                logger.info("calling create_image({}, {}, {})".format(repo, user, path_to_dockerfile))
                images.append(create_image(repo, user, key, path_to_dockerfile))
                logger.info("Added image {} to list".format(images[-1]))
            userdir = os.path.expanduser("~") + '/' + user
            if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
                subprocess.call(['rm', '-rf', userdir])
        else:
            logger.debug("clone_repo({}, {}) returned FALSE".format(user, repo))
            return("Something got messed up!")
        deployment_name = repo
        logger.debug("Contents of variable 'images': {}".format(images))
        logger.info("Length of images: {}".format(len(images)))
        try:
            logger.info("Using {} as frontend image open to the world.".format(images[0][0]))
        except:
            logger.info("Should be returning...")
            return "No Dockerfiles found, please try again"
        try:
            if update:
                logger.info("Update exists: {}".format(update))
                delete_deployment(deployment_name, config_location, key, True)
            else:
                ("Update doesn't exist: {}".format(update))
                delete_deployment(deployment_name, config_location,  key)
        except:
            logger.error("Tried to delete deployment, but threw an error")
        create_deployment(create_deployment_object(images, deployment_name, config_location=config_location, key= key), config_location=config_location, key = key)
        logger.info("Creating deployment")
        try:
            port = -1
            for image in images:
                if "frontend" in image[0]:
                    port = int(image[1])
            if port == -1:
                port = int(images[0][1])
            node_port = create_service(deployment_name, port, config_location, key= key)
        except:
            node_port = -1
            logger.critical("Could not create a service for this application.")
        #MongoDB stuff
        try:
            logger.info("inside try for mongo")
            if repo is not None and user is not None:
                user_param = db.users.find({'username': user})
                if user_param:
                   #db.users.update({'username':user},{$push:{'git-repo':repo}})
                   pass
                else:
                    user = {
                        'username': user,
                        'git-repo': [repo]
                    }
                # Attempt to connect to the db
                result = db.users.insert_one(user)
        except:
            logger.info("MongoDB could not be found")
    return("Running on port {}".format(node_port))

# @app.route("/delete/<deployment>", methods=["POST"])
# def delete(deployment):
#     try:
#         delete_deployment(deployment, config_location, key)
#         return("Deleted {}".format(deployment))
#     except:
#         return("Error trying to delete deployment {}. Does it exist?".format(deployment))

# @app.route("/list/<user>/<list_type>")
# def list_items(user, list_type):
#     URL = "https://api.github.com/users/{}/repos".format(user)
#     try:
#         r = requests.get(URL)        
#     except:
#         return "Error getting to GitHub pulling data for user: {}".format(user)
#     repo_json = r.json()
#     repo_ports = {}
#     if list_type == 'ports':
#         try:
#             for repo in repo_json:
#                 repo_ports[repo['name']] = get_node_port_from_repo(repo=repo['name'], config_location=config_location)
#             return repo_ports
#         except:
#             return "Error occured pulling data"
#     if list_type == 'deployments':
#         try:
#             return get_deployments_from_username(user=user, config_location=config_location, key= key)
#         except:
#             return "Error, there either are no deployments for this user or there's a deeper issue..."

if __name__ == '__main__':
    app.debug = True
    app.run(use_reloader=True, debug=True, host='0.0.0.0', port=5001)