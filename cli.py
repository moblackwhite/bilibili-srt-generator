import argparse
from database_manager import VideoDatabase

parser = argparse.ArgumentParser()

parser.add_argument('--add', type=str)

args = parser.parse_args()


vd = VideoDatabase()

vd.add_bv(args.add)