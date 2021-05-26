import argparse
import os
import sys
import time
from itertools import zip_longest

from Download.image_scraper import BingImageScraper, GoogleImageScraper, YahooImageScraper, open_file

parser = argparse.ArgumentParser()
parser.add_argument("--search_engine", type=str, required=True, choices=["all", "bing", "google", "yahoo"], help='path to queries text file')
parser.add_argument("--queries", type=str, required=True, help='path to queries text file')
parser.add_argument("--directories", type=str, required=True, help='path to directories text file')
parser.add_argument("--num_of_images", type=int, default=100, help='number of images to be scraped')
parser.add_argument("--run_headless", action="store_true", help='run the script without launching the firefox browser')
args = parser.parse_args()

MAP_SCRAPER = {
    "bing": BingImageScraper,
    "google": GoogleImageScraper,
    "yahoo": YahooImageScraper,
}


def main(args):
    # Read the text files
    queries = open_file(args.queries)
    dirnames = open_file(args.directories)

    # start crawling the search engines
    for q_line, d_line in zip(queries, dirnames):
        queries_list = q_line.strip().split(',')
        dirs_list = d_line.strip().split(',')
        # if dirs_list contains only one directory, zip longers will replicate to match queries_list
        for i, (query, directory) in enumerate(zip_longest(queries_list, dirs_list, fillvalue=dirs_list[0])):
            directory = directory.strip()
            query = query.strip()
            print(f"Downloading {query}: ")
            if args.search_engine == "all":
                for engine in MAP_SCRAPER.keys():
                    MAP_SCRAPER[engine](query=query, save_img_dir=directory, index=i, num_of_images=args.num_of_images, run_headless=args.run_headless).scrape()
            else:
                MAP_SCRAPER[args.search_engine](query=query, save_img_dir=directory, index=i, num_of_images=args.num_of_images, run_headless=args.run_headless).scrape()


if __name__ == "__main__":
    main(args)
