import argparse
import os
import sys
import time

from Download.image_scraper import BingImageScraper, GoogleImageScraper, YahooImageScraper, open_file

parser = argparse.ArgumentParser()
parser.add_argument("--queries", type=str, help='path to queries text file')
parser.add_argument("--directories", type=str, help='path to directories text file')
parser.add_argument("--run_headless", action="store_true", help='run the script without launching the chromium browser')
args = parser.parse_args()


def main(args):
    # Read the text files
    queries = open_file(args.queries)
    dirnames = open_file(args.directories)

    # start crawling the search engines
    for q_line, d_line in zip(queries, dirnames):
        queries = q_line.strip().split(',')
        dirs = d_line.strip().split(',')
        for i, (query, directory) in enumerate(zip(queries, dirs)):
            directory = directory.strip()
            query = query.strip()
            print(f"Downloading {query}: ")
            # BingImageScraper(query=query, save_img_dir=directory, index=i, run_headless=args.run_headless).scrape()
            GoogleImageScraper(query=query, save_img_dir=directory, index=i, run_headless=args.run_headless).scrape()
            # YahooImageScraper(query=query, save_img_dir=directory, index=i, run_headless=args.run_headless).scrape()


if __name__ == "__main__":
    main(args)
