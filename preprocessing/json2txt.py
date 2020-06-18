# coding: utf8

from argparse import ArgumentParser
import json
import re


def convert(args):
    """
    Convert raw text in a JSON data file to str.
    """

    with open(args.input_file, "r") as f:
        input_file = json.load(f)

    with open(args.output_file, "w+") as output_file:    
        for doc in input_file:
            for par in doc["paragraphs"]:
                if args.delete_ellipsis:
                    sent = re.sub("<Ellipsis>", "", par["raw"])
                else:
                    sent = par["raw"]
                output_file.write(sent + "\n")


def main():

    parser = ArgumentParser(
        description="Convert raw text in a JSON data file to str")
    parser.add_argument(
        "-input-file", "--input-file", help="Path to the input file containing the data in JSON format")
    parser.add_argument(
        "-output-file", "--output-file", help="Path to the output file")
    parser.add_argument(
        '--delete-ellipsis', default=True, type=bool, help='Whether to delete ellipsis or not')
    args = parser.parse_args()

    convert(args)


if __name__ == "__main__":
    main()