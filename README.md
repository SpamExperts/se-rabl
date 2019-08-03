[![Code Climate](https://codeclimate.com/github/SpamExperts/se-rabl/badges/gpa.svg)](https://codeclimate.com/github/SpamExperts/se-rabl)

[![Issue Count](https://codeclimate.com/github/SpamExperts/se-rabl/badges/issue_count.svg)](https://codeclimate.com/github/SpamExperts/se-rabl)

# se-rabl

SpamExperts implementation of the RABL system

## Installing

To install the server, follow these steps.

 * Install git: `apt-get update && apt-get install git`
 * Install salt-minion using [bootstrap](https://docs.saltstack.com/en/latest/topics/tutorials/salt_bootstrap.html)
 * Generate a ssh key with `ssh-keygen`
 * Authorise the key to access the repository on github.
 * Clone the repository: `git clone git@github.com:SpamExperts/se-rabl.git /var/cache/se-rabl/`
 * Copy the minion configuration: `cp /var/cache/se-rabl/salt/minion /etc/salt/minion`
 * Run salt: `salt-call --local state.highstate pillar='{"mysql":{"password":"rootpassword", "rabl_password":"serverpassword"}}'`

If you want to update the server after the first install add the just_update
flag:

```
    git -C /var/cache/se-rabl pull
    salt-call --local state.highstate pillar='{"just_update":true}'
```

Features
========

TODO
