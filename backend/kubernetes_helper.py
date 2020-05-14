# Functions used to create, update, and delete deploymenets

from kubernetes import client, config
import logging
import os
import re
from os import path
import yaml
from google.auth import compute_engine
from google.cloud.container_v1 import ClusterManagerClient
from google.oauth2 import service_account

logging.basicConfig(filename="backend.log", format='%(levelname)s: %(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

namespace = 'default'

def google_authenticate(project_id, zone, cluster_id, key):
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    try:
        fw = open('key.json', 'r')
        fw.close()
        print("key.json exists")
    except:
        fw = open('key.json', 'w')
        fw.write(key)
        fw.close()
        print("key.json did not exist")
    credentials = service_account.Credentials.from_service_account_file("key.json", scopes=SCOPES)
    cluster_manager_client = ClusterManagerClient(credentials=credentials)
    cluster = cluster_manager_client.get_cluster(project_id, zone, cluster_id)
    configuration = client.Configuration()
    configuration.host = "https://"+cluster.endpoint+":443"
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": "Bearer " + credentials.token}
    return configuration

def create_deployment_object(images, app_name, config_location, key):
    try:
        username = os.environ['DOCKERUSER']
    except:
        username = 'stolaunch'
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     logger.info("Loading k8s config from {}".format(config_location))
    #     config.load_kube_config(config_location)
    # else:
    #     logger.info("Loading k8s config from $HOME/.kube (or your default location)")
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)

    containers = []
    # Create a container for each image
    for image in images:
        logger.info("Adding container to deployment with image {}...".format(image[0]))
        containers.append(client.V1Container(
            name=image[0].replace(":latest", '').replace(username, '').replace('/', ''),
            image=image[0],
            ports=[client.V1ContainerPort(container_port=int(image[1]))]
        ))
    logger.info(containers)
    # Create metadata and spec
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={'app': app_name}),
        spec=client.V1PodSpec(containers=containers)
    )
    # Create the specification section
    spec = client.V1DeploymentSpec(
        replicas=1,
        selector={'matchLabels': {'app': app_name}},
        template=template
        
    )
    # Create and instantiate the deployment object
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=app_name),
        spec=spec
    )
    # Return our deployment object
    return deployment

def create_deployment(deployment, config_location, key):
    logger.debug("Creating deployment")
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     config.load_kube_config(config_location)
    # else:
    #     logger.info("Loading k8s config from default")
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)
    v1 = client.AppsV1Api()
    api_resp = v1.create_namespaced_deployment(
        body=deployment,
        namespace=namespace
    )
    logger.info("Created deployment. Status={}".format(str(api_resp.status)))
    return

def update_deployment(deployment, deployment_name, config_location, key):
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     logger.info("Loading k8s config from {}".format(config_location))
    #     config.load_kube_config(config_location)
    # else:
    #     logger.info("Loading k8s config from default")
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)
    v1 = client.AppsV1Api()
    api_resp = v1.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body=deployment
    )
    logger.info("Deployment updated. Status={}".format(api_resp.status))
    return

def delete_deployment(deployment_name, config_location, key, update=False): # deployment_name is just <repo>
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     logger.info("Loading k8s config from {}".format(config_location))
    #     config.load_kube_config(config_location)
    # else:
    #     logger.info("Loading k8s config from default")
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)

    v1 = client.AppsV1Api()
    corev1 = client.CoreV1Api()
    api_resp = v1.delete_namespaced_deployment(
        name=deployment_name,
        namespace=namespace
    )
    if not update:
        try:
            serv = corev1.delete_namespaced_service(
                name=deployment_name+"-exp",
                namespace=namespace
            )
            logger.info("Delete service status: {}".format(str(serv.status)))
        except:
            logger.error("Could not delete existing service tied to this deployment.")
    logger.info("Deployment deleted. Status={}".format(str(api_resp.status)))
    return

def create_service(deployment_name, port, config_location, key): # Returns the port to find this service at
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     logger.info("Loading k8s config from {}".format(config_location))
    #     config.load_kube_config(config_location)
    # else:
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api()
    try:
        v1.delete_namespaced_service(
            name=deployment_name+"-exp",
            namespace=namespace
        )
    except:
        logger.error("Could not delete existing service")
    body = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=deployment_name+"-exp"
        ),
        spec=client.V1ServiceSpec(
            selector={"app": deployment_name},
            ports=[client.V1ServicePort(
                port=port,
                target_port=port
            )],
            type="NodePort"
        )
    )
    return_value = str(v1.create_namespaced_service(namespace=namespace, body=body))
    node_port = re.search("'node_port': (\d+)", return_value)
    try:
        return node_port.group(1)
    except:
        return 1

# returns the port that you can access the deployment at, if the deployment has been created
def get_node_port_from_repo(repo, config_location, key):
    # if 'DEPLOYED' in os.environ:
    #     logger.info("Running in a k8s cluster")
    #     config.load_incluster_config()
    # elif config_location != None:
    #     logger.info("Loading k8s config from {}".format(config_location))
    #     config.load_kube_config(config_location)
    # else:
    #     config.load_kube_config()
    configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api()
    services = v1.list_namespaced_service(namespace=namespace)
    for service in services.items:
        logger.debug("service name: {}".format(service.metadata.name))
        logger.debug("repo+exp: {}".format(repo + '-exp'))
        if service.metadata.name == repo + '-exp':
            return str(service.spec.ports[0].node_port)
    return "None"

# def get_deployments_from_username(user, config_location, key):
#     # if 'DEPLOYED' in os.environ:
#     #     logger.info("Running in a k8s cluster")
#     #     config.load_incluster_config()
#     # elif config_location != None:
#     #     logger.info("Loading k8s config from {}".format(config_location))
#     #     config.load_kube_config(config_location)
#     # else:
#     #     config.load_kube_config()
#     configuration = google_authenticate('big-keyword-275020', 'us-central1-c', 'launch-cluster', key= key)
#     client.Configuration.set_default(configuration)

#     v1 = client.CoreV1Api()
#     deployments = v1.list_namespaced_deployment(namespace=namespace)
#     ret_val = []
#     for deployment in deployments.items:
#         ret_val.append(deployment.metadata.name)
#     return ret_val