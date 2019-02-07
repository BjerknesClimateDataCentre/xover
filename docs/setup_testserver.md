

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
  * Write a name, eg SSH and outside access
  * Click `Create Security Group`
  * Click `Manage rules` on the new group
    * Click `Add Rule` choose `All ICMP` and `Add`
    * Click `Add Rule` choose `SSH` and `Add`
  * Your security group is finnished
* From "Images" click `Launch` on the GOLD Ubuntu 18.04 LTS
  * In "Details" write a name for the instance
  * In "Flavour" choose at least m1.small
  * In "Network" choose dualstack
  * In "Security Groups" add your new SSH - group as well as default
  * In Key Pair, import your public key from your computer
* When finnished, click `Lauch Instance`

Click on "Instances" to see the IP-address of your new instance


