# coding: utf8

import os
from argparse import ArgumentParser
import random


def split_data(args):
    """
    Split data into train/dev/test sets.
    """

    data_files = os.listdir(args.input_dir)

    # sort the data files alphabetically
    data_files = sorted(data_files)

    # get data file extension
    filename, file_extension = os.path.splitext(data_files[0])

    # files in each set
    train_files = [f for f in data_files if f.startswith(("wsj_02","wsj_03", "wsj_04", "wsj_05", "wsj_06", "wsj_07", "wsj_08", "wsj_09", "wsj_10", "wsj_11", "wsj_12", "wsj_13", "wsj_14", "wsj_15", "wsj_16", "wsj_17", "wsj_18", "wsj_19", "wsj_20", "wsj_21"))]
    dev_files = [f for f in data_files if f.startswith("wsj_22")]
    test_files = [f for f in data_files if f.startswith("wsj_23")]

    # write the list of files in each set
    with open(os.path.join(args.output_dir, "README"), "w+") as f:
        f.write("### TRAIN SET ###\n\n")
        for file_name in train_files:
            f.write(file_name + "\n")
        f.write("\n\n")
        f.write("### DEV SET ###\n\n")
        for file_name in dev_files:
            f.write(file_name + "\n")
        f.write("\n\n")
        f.write("### TEST SET ###\n\n")
        for file_name in test_files:
            f.write(file_name + "\n")

    with open(os.path.join(args.output_dir, args.data_name + '-train' + file_extension), 'w+') as train:
        for f in train_files:
            train.write(open(os.path.join(args.input_dir, f), 'r').read())
    with open(os.path.join(args.output_dir, args.data_name + '-dev' + file_extension), 'w+') as dev:
        for f in dev_files:
            dev.write(open(os.path.join(args.input_dir, f), 'r').read())
    with open(os.path.join(args.output_dir, args.data_name + '-test' + file_extension), 'w+') as test:
        for f in test_files:            
            test.write(open(os.path.join(args.input_dir, f), 'r').read())


def main():

    parser = ArgumentParser(
        description='Split data into train/dev/test sets')
    parser.add_argument(
        '-input-dir', '--input-dir', help='Path to the directory containing the data files')
    parser.add_argument(
        '-output-dir', '--output-dir', help='Path to the output directory to save the datasets')
    parser.add_argument(
        '-data-name', '--data-name', help='Name of the data to save')
    args = parser.parse_args()

    split_data(args)


if __name__ == "__main__":
    main()