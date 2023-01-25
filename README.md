# African Genome Archive

A Data storage solution to make genomic data and metadata both findable and accessible.


### Requirements

Ubuntu 20.04.05
iRODS 4.2

### Prerequisites


iRODS 4.2 can be deployed using the ansible code found here:

https://github.com/jamietyger/irods_ansible

```
ansible-playbook -i inv site.yml
```

[Beginner Training with iRODS 4.2](irods_beginner_training_2018.pdf) will get you started on the basics of installing iRODS on your local machine and demonstrates the iRods commands. 


## Installing / Getting started

A quick introduction of the minimal setup

```
sudo apt-get update
```

Install git
```
sudo apt install git
git --version
```

Configure git
```
git config --global user.name “Firstname Lastname”
git config --global user.email “example@email.com”
```

Python3 pip installation
```
sudo apt install python3-pip
pip list
```

Clone repo
```
mkdir genome-project
cd genome-project
git clone <african genome archive git repo url>
```

Setup virtual environment
```
sudo apt install python3.8-venv
python3 -m venv venv
source venv/bin/activate
```

Install requirements
```
cd AfricanGenomeArchive
pip install -r requirements.txt
```

Upgrade werkzeug & markupsafe

```
pip install -- upgrade werkzeug
pip install markupsafe==2.0.1
```

Run program

```
python -m flask run
```

## Developing

### Built With
Python3, flask, iRODS, bulma-css


