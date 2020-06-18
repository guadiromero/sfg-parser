# coding: utf8

from argparse import ArgumentParser
import re
from collections import OrderedDict

# map of SFG to PTB tags,
# source: http://www.sfs.uni-tuebingen.de/~dm/07/autumn/795.10/ptb-annotation-guide/root.html
TAG_MAP = OrderedDict([
    # clause level
    ("Clause_Complex", "S"),
    ("Clause", "S"),
    # phrase level
    ("Adverbial_Group_Complex", "ADVP"),
    ("Adverbial_Group", "ADVP"),
    ("Conjunction_Group", "CONJP"),
    ("Interjection_Complex", "INTJ"),
    ("Interjection", "INTJ"),
    ("Nominal_Group_Complex", "NP"),
    ("Nominal_Group", "NP"),
    ("Verbal_Group_Complex", "VP"),    
    ("Verbal_Group", "VP"),
    ("Particle", "PRT"),
    ("Prepositional_Phrase_Complex", "PP"),
    ("Prepositional_Phrase", "PP"),
    ])


def map_pos(args, tag_map):
    """
    Map tags from SFG to PTB.

    :param tag_map: ordered dict, map of SFG to PTB tags
    """

    with open(args.input_file, "r") as f:
        input_file = f.readlines()

    with open(args.output_file, "w+") as output_file:
        for line in input_file:
            for tag in tag_map:
                line = re.sub(tag, tag_map[tag], line)
            output_file.write(line)


def main():

    parser = ArgumentParser(
        description="Map tags from SFG to PTB")
    parser.add_argument(
        '-input-file', '--input-file', help='Path to the input file')
    parser.add_argument(
        '-output-file', '--output-file', help='Path to the output file')
    args = parser.parse_args()

    # convert the data format from XML to PTB
    map_pos(args, TAG_MAP)


if __name__ == "__main__":
    main()