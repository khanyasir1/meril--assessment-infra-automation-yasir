def validate_config_schema(config: dict) -> bool:
    """
    Basic validation: check required keys
    """
    try:
        service = config['service']
        required_keys = ['name','version','env','port','max_memory','healthcheck']
        return all(k in service for k in required_keys)
    except KeyError:
        return False
