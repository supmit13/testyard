#!/bin/bash

# Targets:
# --------
# Install docker on AWS EC2 Ubuntu 22.04 host. 
# Import docker image from Images repository.
# Create a container from that image by running it.
# -------------------------------------------------

# Credits: https://linux.how2shout.com/how-to-install-docker-on-aws-ec2-ubuntu-22-04-or-20-04-linux/

# Install required packages and tools
apt install ca-certificates curl gnupg lsb-release

# Add docker's GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add the official repo
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update

# Install Docker CE
apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Find out version and service status and write it on console. 
# May be it would be nice to put it in a log file, but we will do that later.
docker_version_details="$(docker -v)"
docker_service_status="$(systemctl status docker --no-pager -l)"

echo $docker_version_details
echo $docker_service_status

# Add the user ('ubuntu') to the 'docker' group
usermod -aG docker $USER

# Reload shell session
newgrp docker

# Copy docker image from Images repo


# Run the image to create a container. Note/Print the container Id.


# Done!
