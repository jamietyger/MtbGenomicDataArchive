# iRODS Demo Setup Guide

```
sudo apt-get update

sudo apt-get -y install postgresql

sudo su - postgres

psql

```

Now we are in PostgreSQL, so we will switch to database query language.

Let’s create the database to be used by iRODS:

```
CREATE DATABASE "ICAT";

CREATE USER irods WITH PASSWORD 'testpassword';

GRANT ALL PRIVILEGES ON DATABASE "ICAT" to irods;

\q

exit

wget -qO - https://packages.irods.org/irods-signing-key.asc | sudo
apt-key add -

echo "deb [arch=amd64] https://packages.irods.org/apt/ $(lsb_release
-sc) main" | sudo tee /etc/apt/sources.list.d/renci-irods.list

sudo apt-get update

sudo apt-get -y install irods-server irods-database-plugin-postgres

sudo python /var/lib/irods/scripts/setup_irods.py

```

The setup irods.py script will ask for information in five sections.

The details used here are found in pages 15, 16 and 17 of the [Beginner Training with iRODS 4.2](irods_beginner_training_2018.pdf).

```
iinit

Enter hostname: localhost

Enter port number: 1247

Enter irods user name: rods

Enter irods zone: tempZone

Enter irods password: rods

iadmin mkuser alice rodsuser

iadmin moduser alice password alicepass

iadmin mkresc newResc unixfilesystem
`hostname`:/var/lib/irods/new_vault

iexit full

rm ~/.irods/irods_environment.json

iinit

Enter hostname: localhost

Enter port number: 1247

Enter irods user name: alice

Enter irods zone: tempZone

Enter your current iRODS password: alicepass

```

