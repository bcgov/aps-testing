--- 
- hosts: all 
  gather_facts: false
  become: true
  strategy: free
 
  tasks: 
  - name: copy locustfile 
    copy:
      src: locustfile.py
      dest: locustfile.py
  - name: run.sh
    copy:
      src: run.sh
      dest: run.sh
      mode: preserve
  - name: start locust
    shell:
      cmd: nohup ./run.sh {{MASTER_HOST}} &
