import yaml

API = yaml.load(open("bapi/config/api.yml"), Loader=yaml.SafeLoader)
SERVERS = yaml.load(open("bapi/config/servers.yml"), Loader=yaml.SafeLoader)
PRIVATE = yaml.load(open("bapi/config/private.yml"), Loader=yaml.SafeLoader)

VERSION = "2.2.0"
