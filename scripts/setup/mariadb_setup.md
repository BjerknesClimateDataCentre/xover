
SETUP MARIA-DB
==============

For installation of MariaDB, consult references for your preferred system.

To set up mariadb with a user with all privileges, use the following sql:

    CREATE USER 'd2qc'@'localhost'; -- Replace localhost for external host name
    GRANT ALL PRIVILEGES ON d2qc.* To 'd2qc'@'localhost' IDENTIFIED BY 'd2qc';

    -- Database with utf8 collation support
    CREATE DATABASE d2qc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
