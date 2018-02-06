import os
import sys

import mixmatch

if __name__ == '__main__':
    os.environ.setdefault('READER_SETTINGS', 'properties.ini')
    mixmatch.apply(sys.argv)
