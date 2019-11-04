Importing Glodap reference data
-------------------------------

Some scripts are provided for importing glodap reference data, and a brief
recipe is provided here. Issues with the Glodap data set does however
cause the import to produce a few errors.

To use the import functionality, you need access to a server running the xover
system. This can be the production or development server, og it can be your
local development server. See [README.md](README.md) for more info on where to
find the current production or development servers.

1.  The function can accept either:
    - a direct link to the file online
    - a file path to the downloaded file
    - file type must be .csv or .csv.zip
2.  The actual reference data is found on https://www.glodap.info. Go to
    "Data Access -> Merged and adjusted data products" to find files to import.
    The import needs both a reference to the actual data as csv or .zip-file,
    and a reference to the list of expocodes. You can choose to import the full,
    merged data set, or some of the regional data sets.
3.  Navigate to /vagrant/d2qc on your server
4.  Activate the python environment:
    `$ source .env_vagrant/bin/activate`
5.  Youll probably need to clean the database in some way. To simply remove the
    reference data before import, use: `$ ./manage.py clear_refdata`. This removes
    all data sets marked as is_reference.
    To remove ALL DATA, you can use `$  ./manage.py clear_db -m`. This clears all
    data in the database, and initializes the tables.
6.  Now to import the reference data. This might take some hours. Eg:
    ```
    $ m import_refdata \
    https://www.glodap.info/glodap_files/v2.2019/GLODAPv2.2019_Merged_Master_File.csv.zip \
    https://www.glodap.info/glodap_files/v2.2019/EXPOCODES.txt
    ```
