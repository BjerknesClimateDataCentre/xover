Importing Glodap reference data
-------------------------------

Some scripts are provided for importing glodap reference data, and a brief
recipe is provided here. The poor quality of the Glodap data set does however
cause the import to produce a few errors.

To use the import functionality, you need access to a server running the xover
system. This can be the production or development server, og it can be your
local development server. See [README.md](README.md) for more info on where to
find the current production or development servers.

1.  Locate the data on https://glodap.info
    Choose to import the full, merged data set, or some of the regional data
    sets
2.  Navigate to /vagrant/d2qc on your server
3.  Activate the python environment:
    `$ source .env_vagrant/bin/activate`
4.  Youll probably need to clean the database in some way. To remove ALL DATA,
    you can use `$  manage.py clear_db -m`. This clears all data and
    initializes the tables
5.  Now to import the reference data. This will take some hours. Eg:
    ```
    $ m import_refdata \
    https://www.glodap.info/glodap_files/v2.2019/GLODAPv2.2019_Merged_Master_File.csv.zip \
    https://www.glodap.info/glodap_files/v2.2019/EXPOCODES.txt
    ```
