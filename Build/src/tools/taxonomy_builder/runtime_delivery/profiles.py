profiles_config = {
    "dev": {
        "respect_robots": False,
        "rate_limit_rps": 5,
        "backoff_max": 10,
        "use_cache": False,
    },
    "ci": {
        "respect_robots": True,
        "rate_limit_rps": 2,
        "backoff_max": 20,
        "use_cache": True,
    },
    "prod": {
        "respect_robots": True,
        "rate_limit_rps": 1,
        "backoff_max": 60,
        "use_cache": True,
    },
}

def get_profile_settings(name: str):
    return profiles_config.get(name, profiles_config["dev"])
