# HueResource_Controller
For IoT service Testbed

# WebEng IoT Testbed: testbed-service-providers (in this case, Hue device)

Source codes of resource controllers and services in WebEng IoT testbed, written in Python  
Docker + Flask + Redis + Gunicorn

---
## How to run a provider

1. install [docker](https://www.docker.com/)
2. build docker image from Dockerfile:
```
docker build -t webeng_{provider name}:latest .
```
3. run the docker image to construct a container:
```
docker run -d -p 8000:8000 webeng_{provider name}:latest {provider name} {ID} {URL:PORT}
```
The format of `-p` port option is `{host's port}:{container's port}`.  
You can also set a name of the container by using `--name {name}` option.  
For instance, provider ```{provider name}``` is ```dummy_resource```, and it should be same with the file name.

---
## How to add a new service provider
You can copy `dummy_resource.py`, or `dummy_service.py` and following below instruction
1. add a new controller file, name as `{provider name}_{provider type}.py`
2. from `base.py`, import `ResourceAPI` or `ServiceAPI` and define new resource's or service's API by inherit it, name as `class {provider name}{provider type}API` with capitalization
3. implement all abstract methods
4. write execution code of flask app

---
### TODO
- [x] WSGI: Gunicorn integrated
- [ ] Visualization of the architecture

### Issue
- [x] Docker compose (divide Flask, Redis, NginX to different containers): maintain one container for each controller

---
### Frequently used commands of Docker
- `docker ps` shows every containers. `-a` option shows stopped containers. `-l` option shows latest containers.
- `docker logs {container ID}` shows execution logs of the container.
- `docker kill {container ID}` kills the container by sending a `SIGKILL` signal.
- `docker system prune` removes all stopped containers, dangling images, unused networks.
- `docker rm $(docker ps -a -q)` removes all docker containers

---
### To allow CORS
```
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```
---
### Notes
- Containers cannot communicate directly to each other. Be cautious
