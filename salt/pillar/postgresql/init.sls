lxc:
  conf:
    arch: amd64
  create:
    source:
      - centos:latest
      - debian:latest
      - ubuntu:latest
  ns:
    net:
      -
        port:     5432
        protocol: tcp

postgresql:
  service: postgresql
  version: 9.4
  commands:
    initdb: service postgresql initdb
  data_dir: /data/postgresql 
  initdb_args: --data-checksum
  
