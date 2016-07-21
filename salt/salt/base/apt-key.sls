debian-archive-keyring:
  pkg.installed

apt-get-update:
  cmd.run:
    - name: apt-get update
    - require:
      - debian-archive-keyring
