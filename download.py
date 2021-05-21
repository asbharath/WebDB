import argparse
import os
import sys
import time

from Download.image_scraper import BingImageScraper, GoogleImageScraper, YahooImageScraper

parser = argparse.ArgumentParser()
parser.add_argument("--queries", type=str, help='path to queries text file')
parser.add_argument("--directories", type=str, help='path to directories text file')
parser.add_argument("--run_headless", action="store_true", help='run the script without launching the chromium browser')
args = parser.parse_args()


def main(args):
    # Read the text files
    with open(os.path.join(args.queries)) as f:
        queries = f.readlines()
    with open(os.path.join(args.directories)) as f:
        dirnames = f.readlines()

    # start crawling the search engines
    for line, dirs in zip(queries, dirnames):
        queries = (line.rstrip()).split(',')  # get list of queries
        for i, query in enumerate(queries):
            dirs = dirs.rstrip()
            query = query.lstrip(' ')
            print(f"Downloading {query}: ")
            BingImageScraper(query=query, save_img_dir=dirs, index=i, run_headless=args.run_headless).scrape()
            GoogleImageScraper(query=query, save_img_dir=dirs, index=i, run_headless=args.run_headless).scrape()
            YahooImageScraper(query=query, save_img_dir=dirs, index=i, run_headless=args.run_headless).scrape()


if __name__ == "__main__":
    main(args)
