# Configure APT
basic-install:
  pkg:
    - latest
    - pkgs:
      - git
      - bsdmainutils
      - libssl-dev
      - libxml2-dev
      - libxslt-dev
      - logrotate
      - nano
      - libffi-dev
      - openssl
      - binutils
      - libc6
      - gcc

broken_python_modules:
  pkg.purged:
    - pkgs:
      - python-pip
      - python-pip-whl

download get-pip:
  cmd.run:
    - name: wget -nv -N https://bootstrap.pypa.io/get-pip.py
    - cwd: /var/cache/
    - creates: /var/cache/get-pip.py

install pip:
  cmd.run:
    - name: /usr/bin/python /var/cache/get-pip.py
    - unless: 'test -f /usr/bin/pip && fgrep -q /usr/bin/python /usr/bin/pip && /usr/bin/python -m pip'
    - require:
      - cmd: download get-pip
  pip.installed:
    - name: setuptools
    - upgrade: True

mariadb-server:
  pkg:
    - latest
    - pkgs:
      - mariadb-server
      - mariadb-client
      - libmariadb-client-lgpl-dev
  file.symlink:
    - name: /usr/bin/mysql_config
    - target: /usr/bin/mariadb_config
  file.symlink:
    - name: /var/run/mysqld/mysqld.sock
    - target: /tmp/mysql.sock
  service:
    - running
    - name: mysql
    - enable: True
    - reload: True
    - require:
      - pkg: mariadb-server

install-mysqlclient:
  pkg:
    - latest
    - pkgs:
        - python-dev
  pip.installed:
    - name: mysqlclient
    - upgrade: True

{%- if not pillar.get('just_update') %}
configure-root-user:
  file.managed:
    - name: /root/.my.cnf
    - source: salt://my.cnf
    - template: jinja
  mysql_user.present:
    - name: root
    - host: localhost
    - password: {{ pillar['mysql']['password'] }}
    - connection_pass: ""

# Set-up SQL configuration/user/database
rabl-conf:
  mysql_user.present:
    - name: rabl
    - host: localhost
    - password: {{ pillar['mysql']['rabl_password'] }}
    - connection_pass: {{ pillar['mysql']['password'] }}
  mysql_database.present:
    - name: dnsbl
    - connection_pass: {{ pillar['mysql']['password'] }}
  mysql_grants.present:
    - grant: ALL PRIVILEGES
    - database: dnsbl.*
    - user: rabl
    - connection_pass: {{ pillar['mysql']['password'] }}
  file.managed:
    - name: /etc/rabl.conf
    - source: salt://rabl.conf
    - template: jinja
{%- endif %}

add-tables:
  cmd.run:
    - name: mysql dnsbl < /var/cache/se-rabl/sql/dnsbl.sql

# Configure pip and virtualenv
pip-conf:
  pip.installed:
    - name: virtualenv

rabl-pre-install:
  git.latest:
    - name: git@github.com:SpamExperts/se-rabl.git
    - target: /var/cache/se-rabl/
    - force_reset: True
    - identity: /root/.ssh/id_rsa
  virtualenv.managed:
    - name: /var/cache/se-rabl-env
    - system_site_packages: False
    - pip_upgrade: True
  pip.installed:
    - name: setuptools
    - upgrade: True
    - bin_env: /var/cache/se-rabl-env/bin/pip

rabl-requirements:
  pip.installed:
    - requirements: /var/cache/se-rabl/requirements.txt
    - bin_env: /var/cache/se-rabl-env/bin/pip
    - upgrade: True

# Configure PDNS-recursor
pdns-recursor:
  pkg:
    - latest
    - pkgs:
      - pdns-recursor
  service.running:
    - name: pdns-recursor
    - enable: True

rabl-service:
  file.managed:
    - name: /etc/systemd/system/rabl.service
    - source: salt://rabl.service
  service.running:
    - name: rabl
    - enable: True


# Do a final upgrade of various packages
uptodate:
  pkg.uptodate: []
