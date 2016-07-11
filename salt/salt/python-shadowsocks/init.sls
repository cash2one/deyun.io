# vi: set ft=yaml.jinja :

include:
  -  python-pip
  -  supervisor

python-shadowsocks:
  pip.installed:
    - name:        shadowsocks
    
/etc/shadowsocks.json:
  file.managed:
    - template:    jinja
    - source:      salt://{{ sls }}/etc/shadowsocks.json
    - user:        root
    - group:       root
    - replace:     True
    - mode:       '0644'
    - watch:
       - pkg:       python-pip


/etc/supervisor/conf.d/shadowsocks.conf:    
  file.managed:
    - template:     jinja
    - name:         /etc/supervisor/conf.d/shadowsocks.conf
    - source:       salt://{{ sls }}/etc/supervisor/conf.d/shadowsocks.conf
    - user:         root
    - group:        root
    - mode:        '0644'
  cmd.run:
    - name: /usr/sbin/service supervisor  restart
