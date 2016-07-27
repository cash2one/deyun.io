base:
  'T':
    - match: nodegroup
    - roles.test
    - roles.ss-node
  'SS':
    - match: nodegroup
    - roles.ss-node
  'DB':
    - match: nodegroup
    - roles.common
    - roles.db-node
  'Spider':
    - match: nodegroup
    - roles.common
  'DO':
    - match: compound
    - roles.common
