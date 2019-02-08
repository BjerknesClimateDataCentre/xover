

Setup a test server (using UH-IAAS / Openstack)
-----------------------------------------------

This is a (possibly uncomplete) instruction for how to set up a server
using the UH-IAAS infrastructure provded by uib.

### Set up your server instance ###

Additional information for setting up a server instance is found at:
http://docs.uh-iaas.no/en/latest/

* Log in at https://dashboard.uh-iaas.no
* First set up a security group:
  * Click Network -> Security Groups
  * `+ Create Security group`
  * Write a name, eg "My security group", and  `Create Security Group`
  * Click `Manage rules` on the new group
    * Click `Add Rule` choose `All ICMP` and `Add`
    * Click `Add Rule` choose `SSH` and `Add`
    * Click `Add Rule` choose `HTTP` and `Add`
    * Click `Add Rule` choose `HTTPS` and `Add`
    * If you need other open ports, like 8000 for the django development server,
      open these by adding custom TCP ports.
  * Your security group is finished
* From "Images" click `Launch` on the GOLD Ubuntu 18.04 LTS
  * In "Details" write a name for the instance
  * In "Flavour" choose at least m1.small
  * In "Network" choose dualstack
  * In "Security Groups" add your new SSH - group as well as default
  * In Key Pair, import your public key from your computer
* When finnished, click `Lauch Instance`
* You can also add a disc volume. Click Volumes -> Volumes, `+Create Volume`
  * Write a volume name
  * Choose size eg 15GB
  * `Create Volume`
* Go to Compute -> Instances and on your instance, choose `Attach Volume`
* `Attach volume` to your instance

Click on "Instances" to see the IP-address of your new instance. You can ssh to
your instance by doing:

```
ssh ubuntu@XXX.XXX.XX.XX
```

### Preparing hard disk setup ###

After ssh-ing into the new machine you do the following:

*Partition and format your disk volume, possibly /dev/sdb*

This uses the fdisk programme to partition your disk volume. All commands are
single-letter commands.

* `sudo fdisk /dev/sdb`
* o      # Create partition table
* n      # Create new partition
  * p    # ... as a primary partition
  * 1    # ... with partition number 1
* w      # Write partition to disk

*Afterwards format volume*
* `sudo mkfs.ext4 /dev/sdb1`

### Install and setup server software ###

There are scripts to make this smoothly, so start by
cloning the git repository to your server:

* `sudo mkdir /vagrant`
* `sudo chown ubuntu:ubuntu /vagrant`
* `git clone https://github.com/jonasfh/xover.git /vagrant`
* `cd /vagrant`

Most of the sofware setup is defined in /scripts/setup. Vagrant scripts here are supposed to be run on a vagrant instance, but should work equally well here. Script 1 and 3 needs root access, while script 2 and the dev-script runs unprivileged.


* `sudo ./scripts/setup/vagrant_provisioning1.sh`
* `./scripts/setup/vagrant_provisioning2.sh`
* `sudo ./scripts/setup/vagrant_provisioning3.sh`
# Run this only on development servers #
* `./scripts/setup/vagrant_dev_provisioning.sh`

To be able to access the development server from the outside you need to update
the ALLOWED_HOSTS - variable in the django setup.
