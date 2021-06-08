import yaml

API		= yaml.load(open("app/config/api.yml"),		Loader=yaml.SafeLoader)
SERVERS	= yaml.load(open("app/config/servers.yml"),	Loader=yaml.SafeLoader)
PRIVATE	= yaml.load(open("app/config/private.yml"),	Loader=yaml.SafeLoader)