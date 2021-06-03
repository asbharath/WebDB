import argparse
import os
import json
import tensorflow as tf
from path import Path
from imagededup.methods import CNN, DHash


encoder_methods = {
    'CNN' : CNN,
    'DHash' : DHash,
}


def get_args():
    parser = argparse.ArgumentParser('Duplicates removal tool',
        description='Encode images, find duplicates based on the encodings, and move the duplicates to a different location')
    parser.add_argument('-r', '--dirs_root', type=Path, default='/', help='Root path for --dirs')
    parser.add_argument('-d', '--dirs', nargs='+', default=[],
        help='Input image directories, located in --dirs_root, to be checked for duplicates')
    parser.add_argument('--duplicates_dir', type=Path, default='duplicates',
        help='Directory for the duplicate images to be moved to')
    parser.add_argument('--encoder', type=str, choices=['CNN', 'DHash'], default='CNN', help='Type of encoding for features comparison')
    parser.add_argument('--threshold', type=float, default=0.9,
        help='For hashing: max_distance_threshold, for CNN: min_similarity_threshold (note: the logic of these differs, refer to documentation of imagededup)')
    parser.add_argument('--display_duplicates', action='store_true', help='Show duplicate images that will be moved, requires tkinter')
    parser.add_argument('--dry_run', action='store_true', help='Does not remove images in dry run')
    parser.add_argument('--encodings_in', nargs='+', default=[], help='Input encodings path')
    parser.add_argument('--encodings_out', type=Path, default=None, help='Output encodings path')
    parser.add_argument('--encodings_only', action='store_true', help='Only compute encodings and finish')
    args = parser.parse_args()
    return args


def tf_startup():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)


def encode_dataset(encoder, dataset_dir):
    encodings = encoder.encode_images(dataset_dir)
    encodings = {f'{dataset_dir}/{k}' : v for k, v in encodings.items()}
    return encodings


def encode_datasets(encoder, dataset_root, dataset_dirs):
    all_encodings = {}
    for dataset in dataset_dirs:
        print(f'Encoding dataset {dataset}')
        encodings = encode_dataset(encoder, dataset_root / dataset)
        all_encodings.update(encodings)
    return all_encodings


def load_encodings(encodings_in):
    print('Loading encodings:')
    encodings = {}
    for enc in encodings_in:
        enc_file = Path(enc).with_suffix('.json')
        print(f'Loading {enc_file}')
        with open(enc_file, 'r') as fp:
            data = json.load(fp)
            encodings = {**encodings, **data}
    return encodings


def get_encodings(args, encoder):
    encodings = None
    if args.encodings_in != []:
        encodings = load_encodings(args.encodings_in)
    else:
        encodings = encode_datasets(encoder, args.dataset_root, args.dataset_dirs)
    return encodings


def save_encodings(encodings, encodings_out, encoder_type):
    if encoder_type == 'CNN':
        encodings = {k : v.tolist() for k, v in encodings.items()}

    out_file = encodings_out.with_suffix('.json')
    print(f'Saving encodings as {out_file}')
    with open(out_file, 'w') as fp:
        json.dump(encodings, fp)


def get_duplicates(encoder, encodings, encoder_type, threshold):
    duplicates = None
    if encoder_type == 'CNN':
        duplicates = encoder.find_duplicates_to_remove(encoding_map=encodings, min_similarity_threshold=threshold)
    elif encoder_type == 'DHash':
        duplicates = encoder.find_duplicates_to_remove(encoding_map=encodings, max_distance_threshold=int(threshold))
    return duplicates


def display_duplicates(encoder, encodings, encoder_type, threshold, duplicates):
    duplicates_map = None
    if encoder_type == 'CNN':
        duplicates_map = encoder.find_duplicates(encoding_map=encodings, min_similarity_threshold=threshold)
    elif encoder_type == 'DHash':
        duplicates_map = encoder.find_duplicates(encoding_map=encodings, max_distance_threshold=int(threshold))

    print('Displaying duplicate images')
    from imagededup.utils import plot_duplicates
    for dup in duplicates:
        plot_duplicates('/', duplicates_map, dup)


def move_duplicates(duplicates, duplicates_dir):
    print(f'Moving duplicate images to {duplicates_dir}')
    os.makedirs(duplicates_dir, exist_ok=True)
    for dup in duplicates:
        dup_name = Path(dup).name
        os.rename(dup, duplicates_dir / dup_name)


def process_duplicates(args):
    encoder = encoder_methods[args.encoder]()
    encodings = get_encodings(args, encoder)

    if args.encodings_out:
        save_encodings(encodings, args.encodings_out, args.encoder)

    if args.encodings_only:
        return

    duplicates = get_duplicates(encoder, encodings, args.encoder, args.threshold)
    print(f'Number of duplicates to remove: {len(duplicates)}')

    if args.display_duplicates:
        display_duplicates(encoder, encodings, args.encoder_type, args.threshold, duplicates)

    if not args.dry_run:
        move_duplicates(duplicates, args.duplicates_dir)


def main():
    args = get_args()
    print(args)
    if args.encoder == 'CNN':
        tf_startup()
    process_duplicates(args)


if __name__ == "__main__":
    main()
