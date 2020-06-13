# coding: utf8

import os
from argparse import ArgumentParser
import random


def reduce_corpus(args):
    """
    Reduce the number of sentences in the corpus.
    """

    split_index = int(args.sent_num * 80 / 100)

    with open(args.input_file, "r") as f:
        input_file = f.readlines()

    output_full = open(args.output_dir + 'sfgbank-sample-full.conll', "w+")
    output_train = open(args.output_dir + 'sfgbank-sample-train.conll', "w+")
    output_dev = open(args.output_dir + 'sfgbank-sample-dev.conll', "w+")

    sent_counter = 0

    for line in input_file:
        if sent_counter < split_index:
            output_train.write(line)
        else:
            output_dev.write(line)
        output_full.write(line)
        if line == "\n":
            sent_counter += 1
        if sent_counter == args.sent_num:
            break


def main():

    parser = ArgumentParser(
        description='Split data into train/dev/test sets')
    parser.add_argument(
        '-input-file', '--input-file', help='Path to the input file in CoNLL format')
    parser.add_argument(
        '-output-dir', '--output-dir', help='Path to the output dir')
    parser.add_argument(
        '--sent-num', default=200, type=int, help='Number of sentences in the corpus to build')
    args = parser.parse_args()

    reduce_corpus(args)


if __name__ == "__main__":
    main()