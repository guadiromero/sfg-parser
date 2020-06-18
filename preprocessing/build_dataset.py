# coding: utf8

import os
from argparse import ArgumentParser
import random


def split_data(args):
    """
    Split data into train/dev/test sets.
    """

    data_files = os.listdir(args.input_dir)

    # either sort the data files alphabetically or shuffle them (comment one of the lines)
#    data_files = sorted(data_files)
    random.shuffle(data_files)

    # get data file extension
    filename, file_extension = os.path.splitext(data_files[0])

    # number of files in the dev and test sets
    dev_n = int(args.dev_size * len(data_files) / 100)
    test_n = int(args.test_size * len(data_files) / 100)
    train_n = len(data_files) - dev_n - test_n

    # files in each set
    train_files = data_files[:(len(data_files) - dev_n - test_n)]
    dev_files = data_files[(len(data_files) - dev_n - test_n):(len(data_files) - test_n)]
    test_files = data_files[(len(data_files) - test_n):len(data_files)]

    # write the list of files in each set
    with open(os.path.join(args.output_dir, "README"), "w+") as f:
        f.write("### TRAIN SET ###\n\n")
        f.write("Percentage: " + str(100 - args.dev_size - args.test_size) + "%\n")
        f.write("Number of files: " + str(train_n) + "\n\n")
        for file_name in train_files:
            f.write(file_name + "\n")
        f.write("\n\n")
        f.write("### DEV SET ###\n\n")
        f.write("Percentage: " + str(args.dev_size) + "%\n")
        f.write("Number of files: " + str(dev_n) + "\n\n")
        for file_name in dev_files:
            f.write(file_name + "\n")
        f.write("\n\n")
        f.write("### TEST SET ###\n\n")
        f.write("Percentage: " + str(args.test_size) + "%\n")
        f.write("Number of files: " + str(test_n) + "\n\n")
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
    parser.add_argument(
        '--dev-size', default=10, type=int, help='Size of the development set as percentage')
    parser.add_argument(
        '--test-size', default=10, type=int, help='Size of the testing set as percentage')
    args = parser.parse_args()

    split_data(args)


if __name__ == "__main__":
    main()