#!/bin/bash

sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo DEBIAN_FRONTEND=noninteractive apt install -y python3.8
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2
sudo apt install -y python3-pip
sudo apt install -y libpython3.8-dev
sudo pip3 install --upgrade pip
sudo pip3 install --upgrade locust


# cd /etc/nginx/sites-available
# sudo vi default
# -- change port to 7777
# sudo vi /var/www/html/index.nginx-dbian.html
# sudo service nginx restart
