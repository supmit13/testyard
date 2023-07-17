# syntax=docker/dockerfile:1
FROM ubuntu:20.04

# install app dependencies
RUN apt-get update && apt-get install -y python2 python2-pip python2-dev
RUN apt-get install nginx
RUN apt-get install mysql
RUN pip install -r requirements.txt

# install app
COPY /home/supmit/ty_newiface /home/supmit/

# final configuration

EXPOSE 80 443 8888 3306
CMD /etc/init.d/nginx start
CMD /etc/init.d/mysql start

