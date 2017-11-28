import os
import sys

from mixmatch.promotion import apply

if __name__ == '__main__':
    os.environ.setdefault('READER_SETTINGS', 'properties.ini')

    apply(sys.argv)
