---
- hosts: all
  gather_facts: false
  become: true
  strategy: free

  tasks:
  - name: package update
    shell: |
      apt update
      apt install -y python3-pip
      pip3 install locust
      echo "\n* hard nofile 200000\n* soft nofile 200000\n" >> /etc/security/limits.conf
