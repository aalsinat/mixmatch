from os import environ
from sys import argv

import mixmatch

if __name__ == '__main__':
    environ.setdefault('READER_SETTINGS', 'properties.ini')
    mixmatch.apply(argv)
