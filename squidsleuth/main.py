from __future__ import print_function

import fileinput
import logging
import os
import sys

from squidsleuth import Sleuth


LOG = logging.getLogger(__name__)


def main():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    sleuth = Sleuth(sys.argv[1], os.environ["SQUIDSLEUTH_CONNSTR"])
    sleuth.run()


def main_detectvuln():
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    for line in fileinput.input():
        line = line.rstrip()
        sleuth = Sleuth(line, os.environ["SQUIDSLEUTH_CONNSTR"])
        try:
            sleuth.guess_base_uri()
            print(line)
        except Exception as e:
            print("Exception: ", e, file=sys.stderr)

if __name__ == "__main__":
    main()
