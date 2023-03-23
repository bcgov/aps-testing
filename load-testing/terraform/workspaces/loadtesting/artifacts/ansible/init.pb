---
- hosts: all
  gather_facts: false
  become: true
  strategy: free

  # docker run -ti --rm --user root ubuntu:18.04
  tasks:
  - name: package update
    shell: |
      apt update
      apt install -y software-properties-common
      add-apt-repository -y ppa:deadsnakes/ppa
      DEBIAN_FRONTEND=noninteractive apt install -y python3.8
      update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
      update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 2
      apt install -y python3-pip
      apt install -y libpython3.8-dev
      pip3 install --upgrade pip
      pip3 install --upgrade locust
      echo "\n* hard nofile 200000\n* soft nofile 200000\n" >> /etc/security/limits.conf
