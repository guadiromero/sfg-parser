# coding: utf8

import os
from argparse import ArgumentParser
import random


def split_data(args):
    """
    Split data into train/dev/test sets.
    """

    # randomize data
    data_files = os.listdir(args.input_dir)
    random.shuffle(data_files)

    # get data file extension
    filename, file_extension = os.path.splitext(data_files[0])

    # get split indexes
    split_index_dev = int(len(data_files) * args.dev_size / 100)
    split_index_test = split_index_dev + int(len(data_files) * args.dev_size / 100)

    with open(os.path.join(args.output_dir, args.data_name + '-dev' + file_extension), 'w+') as dev:
        for input_file in data_files[:split_index_dev]:
            dev.write(open(os.path.join(args.input_dir, input_file), 'r').read())
    with open(os.path.join(args.output_dir, args.data_name + '-test' + file_extension), 'w+') as test:
        for input_file in data_files[split_index_dev:split_index_test]:            
            test.write(open(os.path.join(args.input_dir, input_file), 'r').read())
    with open(os.path.join(args.output_dir, args.data_name + '-train' + file_extension), 'w+') as train:
        for input_file in data_files[split_index_test:]:
            train.write(open(os.path.join(args.input_dir, input_file), 'r').read())


def main():

    parser = ArgumentParser(
        description='Split data into train/dev/test sets')
    parser.add_argument(
        '-input-dir', '--input-dir', help='Path to the directory containing the data files')
    parser.add_argument(
        '-output-dir', '--output-dir', help='Path to the output directory to save the datasets')
    parser.add_argument(
        '-data-name', '--data-name', help='Name of the data to save')
    parser.add_argument(
        '--dev-size', default=10, type=int, help='Size of the development set as percentage')
    parser.add_argument(
        '--test-size', default=10, type=int, help='Size of the testing set as percentage')
    args = parser.parse_args()

    split_data(args)


if __name__ == "__main__":
    main()