# coding: utf8

import os
from argparse import ArgumentParser
import random


def split_data(input_dir, output_dir, dev_size, test_size):
    """
    Split data into train/dev/test sets.
    
    :param input_dir: str, path to the directory containing the data files
    :param output_dir: str, path to the output directory to save the data sets
    :param dev_size: int, size of the developing set as percentage
    :param test_size: int, size of the testing set as percentage
    """

    data_files = os.listdir(input_dir)
    random.shuffle(data_files)

    split_index_dev = int(len(data_files) * dev_size / 100)
    split_index_test = split_index_dev + int(len(data_files) * dev_size / 100)

    with open(os.path.join(output_dir, 'sfgbank-bkl.dev'), 'w+') as dev:
        for input_file in data_files[:split_index_dev]:
            dev.write(open(os.path.join(input_dir, input_file), 'r').read())
    with open(os.path.join(output_dir, 'sfgbank-bkl.test'), 'w+') as test:
        for input_file in data_files[split_index_dev:split_index_test]:            
            test.write(open(os.path.join(input_dir, input_file), 'r').read())
    with open(os.path.join(output_dir, 'sfgbank-bkl.train'), 'w+') as train:
        for input_file in data_files[split_index_test:]:
            train.write(open(os.path.join(input_dir, input_file), 'r').read())


def main():

    parser = ArgumentParser(
        description='Split data into train/dev/test sets')
    parser.add_argument(
        '-input_dir', '--input_dir', help='Path to the directory containing the data files')
    parser.add_argument(
        '-output_dir', '--output_dir', help='Path to the output directory to save the datasets')
    parser.add_argument(
        '--dev_size', default=10, type=int, help='Size of the development set as percentage')
    parser.add_argument(
        '--test_size', default=10, type=int, help='Size of the testing set as percentage')
    args = parser.parse_args()

    split_data(args.input_dir, args.output_dir, args.dev_size, args.test_size)


if __name__ == "__main__":
    main()