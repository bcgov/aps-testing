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
  - name: start locust
    shell: "nohup locust -f locustfile.py --worker --master-host={{MASTER_HOST}} &"
