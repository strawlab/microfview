import os.path
import logging
import collections

import json
import yaml


def get_logger():
    """returns the global microfview logging.Logger instance"""
    # setup logging
    logger = logging.getLogger('microfview')
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler()
    f = logging.Formatter("%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
    return logger


def parse_config_file(filename):
    config = collections.defaultdict(dict)

    if filename and os.path.isfile(filename):
        with open(filename,'r') as f:
            if filename.endswith('.json'):
                config.update( json.load(f) )
            elif filename.endswith('.yaml'):
                config.update( yaml.load(f) )

    return config

