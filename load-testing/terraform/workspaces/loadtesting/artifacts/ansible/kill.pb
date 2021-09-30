--- 
- hosts: all 
  gather_facts: false
  become: true
 
  tasks: 
  - name: kill
    shell: "killall locust"