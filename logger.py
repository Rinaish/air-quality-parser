import logging.config

def setup_logger(level: str = 'INFO'):
    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': f'%(asctime)s - %(levelname)s - %(name)s:%(lineno)s - %(message)s'
                }
            },
            'handlers': {
                'console': {'class': 'logging.StreamHandler', 'formatter': 'default'}
            },
            'root': {'handlers': ['console'], 'level': level}
        }
    )