# EIDA Server

> Ansible configuration for an EIDA node server


## Running the playbook

### Setup

This playbook depends on the BGS Ansible Collection.
These include Sophos, Prometheus and DevOps related collections. 

```bash
ansible-galaxy install -r requirements.yml
```

The seisan folder is mounted onto the VM. 

### Server configuration

To configure the server, it is necessary to run the playbook as the DevOps admin user, with your SSH public key already installed.
Run the playbook as:

```bash
ansible-playbook -i hosts.yml -u admin main.yml
```

### Initialisation
Run the following commands when setting up EIDA for the first time: (When setting up mysql_secure_installation, make sure you create a new root password. Use mysql_root_password in vars.yml. This root password is used during seiscomp setup)
```
sudo mysql_secure_installation

sudo systemctl enable mariadb

sudo systemctl enable seiscomp

sudo systemctl restart mariadb

seiscomp setup

# Might have to wait for the cronJob to run the python script that fills the inventory folder with XML files from SDS archive
seiscomp update-config inventory

seiscomp enable fdsnws

seiscomp start
```

When setting up WS-Availability for the first time, uncomment the tasks "Initial build command for materialised view" and "Print initial materialised build stdout" in the file tasks/wsavailability_setup.yml. It can be commented out after setup. 

### Things to delete in EIDA server to start fresh
```
sudo systemctl stop seiscomp

sudo systemctl stop mariadb

docker rm -f wfcatalog-collector-1 wfcatalog-service-1 nginx-nginx-1 mongo-mongodb-1 fdsnws-availability-api fdsnws-availability-cacher fdsnws-availability-cache && docker rmi -f wfcatalog-collector wfcatalog-service nginx-nginx mongo:7.0 redis:7.0-alpine wsavailability-cacher wsavailability-api

sudo dnf remove -y mariadb-server mariadb

sudo rm -rf databases/ nginx/ seiscomp6/ wfcatalog/ wsavailability/ .seiscomp/ /var/lib/mysql/ /etc/my.cnf.d/ && sudo rm -f create_station_xml.py /etc/my.cnf

crontab -r

# Find the PID for ports 8080 and 18180 (seiscomp ports)
# Find PIDs
sudo ss -tulpn

# Kill PIDs
sudo kill -9 <pid_1> <pid_2>
```
