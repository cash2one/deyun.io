# vi: set ft=yaml.jinja :

{% from 'postgresql/map.jinja' import map with context %}

postgresql:
  pkg.installed:
    - name:     {{ map.get('pkg', {}).get('name') }}
  service.running:
    - enable:      True
    - reload:      True
    - watch:
      - pkg:       postgresql

postgresql-conf:
  file.managed:
    - name:        /etc/postgresql/{{ pillar['postgresql']['version']  }}/main/postgresql.conf
    - source:      salt://{{ sls }}/etc/postgresql/postgresql.conf
    - template:    jinja
    - user:        root
    - group:       root
    - mode:        644
    - require:
      - service:   postgresql
  cmd.run:
    - name:       /usr/sbin/service postgresql restart
    - require:
      - pkg:      postgresql  

postgresql-pghba:
  file.managed:
    - source:     salt://{{ sls }}/etc/postgresql/pg_hba.conf
    - name:       /etc/postgresql/{{ pillar['postgresql']['version']  }}/main/pg_hba.conf
    - template:   jinja
    - user:       root
    - group:      root
  cmd.run:
    - name:       /usr/sbin/service postgresql restart
    - require:
      - pkg:      postgresql

service postgresql initdb:
  cmd.run:
    {% if grains.os_family == 'Kali' %}
    - name: pg_createcluster {{ pillar['postgresql']['version']  }} -d {{ pillar['postgresql']['data_dir'] }} --start main 
    {% else  %}
    - name: {{ postgresql.commands.initdb }}
    {% endif %}
    - unless:      test -f /var/lib/pgsql/data/postgresql.conf
    - require:
      - pkg:       postgresql
    - require_in:
      - service:   postgresql



  
