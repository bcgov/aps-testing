#!/bin/bash

sudo apt update
sudo apt install -y python3-pip ansible nginx
sudo pip3 install locust

# cd /etc/nginx/sites-available
# sudo vi default
# -- change port to 7777
# sudo vi /var/www/html/index.nginx-dbian.html
# sudo service nginx restart
