# Deduplication

## Description

To clean image directories from duplicates, near-duplicates (same images, but transformed, e.g. color-adjusted, cropped, rotated) and close-to duplicates (e.g. images taken in the same place at different moments) you can use the deduplication script `remove_duplicates.py`. How close resemblance is required for images to be considered duplicates can be set using argument `--threshold`.

The script encodes the images found in the directory, compares the encodings for similarity, and moves the duplicates to the target directory. There are two available ways to encode the images, either using method `DHash` or `CNN`, both from package `imagededup`. Note: `threshold` meaning is different for these two, for hashing it is bit distance of 64-bit encodings, and for CNN it is based on `cosine_similarity` from `sklearn`. From experience, `CNN` thresholds 0.82-0.9 are generally fine, and for hashing ~10. Encodings can be also saved to a JSON file and a list of encodings for different datasets can be loaded from their corresponding JSON files.

The duplicates can be visualized using the script.

A docker installing `imagededup` from a repository is prepared in `duplicates_removal.dockerfile`.

## Examples

Example argument sets for `python remove_duplicates.py`:

- `-d ~/dataset` - will find duplicates in `~/dataset` and move them to the directory `duplicates` rooted in current directory
- `--dirs ~/dataset --duplicates_dir ~/duplicates --encoder CNN --threshold 0.85` - will move the duplicates to the directory `~/duplicates`, encoding will happen using the `CNN` method (default)
- `-d ~/dataset_1 ~/dataset_2 --display_duplicates` - find duplicates and cross_duplicates in the listed datasets and display them
- `--encodings_in ~/enc_1.json ~/enc_2 --encodings out ~/enc_merged --encodings_only` - load encodings (no `.json` needed in encodings filenames) and save merged ones to a file, and finish on that (`--encodings_only`)
- `-r ~/dataset -d dir_1 dir_2` - process duplicates in directories `~/dataset/dir_1` and `~/dataset/dir_2`
- `-d ~/dataset --dry_run` - do not actually move files
- `-d ~/images_dir --no_data_dir --no_annot` - process regular images directory