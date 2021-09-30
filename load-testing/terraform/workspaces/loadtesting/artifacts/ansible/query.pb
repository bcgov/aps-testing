--- 
- hosts: all 
  gather_facts: false
  become: true
 
  tasks:
  - name: query 
    shell: "curl https://ip.api.gov.bc.ca"
    register: ip
  - debug: msg="{{ ip.stdout }}"