FROM ubuntu:18.04
RUN apt-get update -y
RUN apt-get install -y python3 python3-pip redis-server

# copy directory to /agent
COPY . /agent
WORKDIR /agent

# install requirements according to requirements.txt
RUN pip3 install -r requirements.txt

# change name of resource controller or service: currently "dummy_controller"
ENTRYPOINT ["bash", "run.sh"]