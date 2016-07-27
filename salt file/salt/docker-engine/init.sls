{% if grains['os'] == 'Kali' or grains['os'] == 'Debian'  %}
pkginstall:
  pkg.installed:
    - pkgs:
       - apt-transport-https
       - ca-certificates
  cmd.run:
    - name: apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

docker-aptfile:
  file.managed:
    - name: /etc/apt/sources.list.d/docker.list
    - source: salt://docker-engine/docker.list

backport-aptfile:
  file.managed:
    - name: /etc/apt/sources.list.d/backport.list
    - source: salt://docker-engine/backport.list

aptupdate:
  cmd.wait:
    - name: /usr/bin/apt-get update
    - watch:
       - file: docker-aptfile
       - file: backport-aptfile
       - pkginstall

docker-engine:
  pkg.installed:
    - require:
       - aptupdate
  cmd.run:
    - name: /usr/sbin/service docker status
{% endif %}
