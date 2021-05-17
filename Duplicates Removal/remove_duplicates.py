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
    parser.add_argument('--duplicates_dir', type=str, default=None,
        help='Directory for the duplicate images to be moved to, defaults to subdirectory "duplicates" within the tested directory')
    parser.add_argument('--display_removed', action='store_true', help='Show images that will be removed, requires tkinter')
    parser.add_argument('--dry_run', action='store_true', help='Does not remove images in dry run')
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
        print('Displaying duplicate images')
        duplicates_map = []
        if args.encoder == 'CNN':
            duplicates_map = encoder.find_duplicates(encoding_map=encodings, min_similarity_threshold=args.threshold)
        elif args.encoder == 'DHash':
            duplicates_map = encoder.find_duplicates(encoding_map=encodings, max_distance_threshold=args.threshold)

        from imagededup.utils import plot_duplicates
        for dup in duplicates:
            plot_duplicates(args.dir, duplicates_map, dup)

    if not args.dry_run:
        duplicates_dir = args.duplicates_dir if args.duplicates_dir else f'{args.dir}/duplicates'
        print(f'Moving duplicate images to {duplicates_dir}')

        os.makedirs(duplicates_dir, exist_ok=True)

        for dup in duplicates:
            os.rename(f'{args.dir}/{dup}', f'{duplicates_dir}/{dup}')


args = get_args()
print(args)
remove_duplicates(args)