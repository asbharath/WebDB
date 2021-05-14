import argparse
import os
from imagededup.methods import CNN, DHash


encoder_methods = {
    'CNN' : CNN,
    'DHash' : DHash,
}


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', type=str, default='.', help='Directory with downloaded images')
    parser.add_argument('--encoder', type=str, choices=['CNN, DHash'], default='CNN', help='Type of encoding for features comparison')
    parser.add_argument('--threshold', type=float, default=0.9,
        help='For hashing: max_distance_threshold, for CNN: min_similarity_threshold (note: the logic of these differs, refer to documentation)')
    parser.add_argument('--display_removed', type=bool, default='False', help='Show images that will be removed, requires tkinter')
    parser.add_argument('--dry_run', type=bool, default=False, help='Does not remove images in dry run')
    args = parser.parse_args()
    return args


def remove_duplicates(args):
    encoder = encoder_methods[args.encoder]()
    encodings = encoder.encode_images(args.dir)

    duplicates = []
    if args.encoder == 'CNN':
        duplicates = encoder.find_duplicates_to_remove(encoding_map=encodings, min_similarity_threshold=args.threshold)
    elif args.encoder == 'DHash':
        duplicates = encoder.find_duplicates_to_remove(encoding_map=encodings, max_distance_threshold=args.threshold)

    print(f'Number of duplicates to remove: {len(duplicates)}')

    if args.display_removed:
        duplicates_map = []
        if args.encoder == 'CNN':
            duplicates_map = encoder.find_duplicates(encoding_map=encodings, min_similarity_threshold=args.threshold)
        elif args.encoder == 'DHash':
            duplicates_map = encoder.find_duplicates(encoding_map=encodings, max_distance_threshold=args.threshold)

        from imagededup.utils import plot_duplicates
        for dup in duplicates:
            plot_duplicates(args.dir, duplicates_map, dup)

    os.makedirs(f'{args.dir}/duplicates', exist_ok=True)

    for dup in duplicates:
        os.rename(f'{args.dir}/{dup}', f'{args.dir}/duplicates/{dup}')


args = get_args()
remove_duplicates(args)