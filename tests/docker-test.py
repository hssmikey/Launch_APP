import docker
import os
def main():
    client = docker.from_env()
    tag = "gcr.io/conductive-fold-275020/hello_from_python:latest"
    client.images.build(path="../frontend/", rm=True, tag=tag, platform='amd64')
    # filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    f = open("/Users/dylanblake/key.json", "r")
    key = f.read()
    key = "$(" + key + ")"
    client.login(username="_json_key", password = key, email= "1011931254470-compute@developer.gserviceaccount.com", registry= "https://gcr.io", reauth= False, dockercfg_path=None)
    client.images.push(tag)

if __name__ == '__main__':
    main()