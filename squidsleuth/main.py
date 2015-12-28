import logging
import os
import sys

from squidsleuth import Sleuth


def main():

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    sleuth = Sleuth(sys.argv[1], os.environ["SQUIDSLEUTH_CONNSTR"])
    sleuth.run()

if __name__ == "__main__":
    main()
