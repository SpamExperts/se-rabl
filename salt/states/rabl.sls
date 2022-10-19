# Configure APT
basic-install:
  pkg:
    - latest
    - pkgs:
      - nano
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
      - wget
      - python3-dev
      - python3-pip
      - default-libmysqlclient-dev
      - libmariadb-dev-compat

# Salt 2018.3.4 (Oxygen) doesn't support a newer version
install_required_salt_packages:
  cmd.run:
    - name: pip3 install mysqlclient virtualenv==16.1.0

mariadb-server:
  pkg:
    - latest
    - pkgs:
      - mariadb-server
      - mariadb-client
      - libmariadbclient-dev
  service:
    - running
    - name: mysql
    - enable: True
    - reload: True
    - require:
      - pkg: mariadb-server

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
rabl-pre-install:
  virtualenv.managed:
    - name: /var/cache/se-rabl-env
    - system_site_packages: False
    - pip_upgrade: True
    - python: python2
  pip.installed:
    - name: setuptools
    - upgrade: True
    - bin_env: /var/cache/se-rabl-env/bin/pip

rabl-requirements:
  pip.installed:
    - requirements: /var/cache/se-rabl/requirements.txt
    - bin_env: /var/cache/se-rabl-env/bin/pip
    - upgrade: True


install-rabl:
  pip.installed:
    - name: /var/cache/se-rabl/
    - upgrade: True
    - bin_env: /var/cache/se-rabl-env/bin/pip
    - cwd: /var/cache/se-rabl/
    - watch_in:
      - service: rabl


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
