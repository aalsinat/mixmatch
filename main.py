import sys

import os

from mixmatch import promotion

if __name__ == '__main__':
    os.environ.setdefault('READER_SETTINGS', 'properties.ini')
    promotion.apply(sys.argv)
