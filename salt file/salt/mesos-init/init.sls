# vi: set ft=yaml.jinja :

{% if salt['config.get']('os_family') == 'Debian' or salt['config.get']('os_family') == 'Ubuntu' %}

openjdf-7-jdk:
  pkg.installed:   []

build-essential:
  pkg.installed:   []

python-dev:
  pkg.installed:   []

libcurl4-nss-dev:
  pkg.installed:   []

libsasl2-dev:
  pkg.installed:   []

libsasl2-modules:
  pkg.installed:   []

maven:
  pkg.installed:   []

libapr1-dev:
  pkg.installed:   []

livsvn-dev:
  pkg.installed:   []
{% endif %}
