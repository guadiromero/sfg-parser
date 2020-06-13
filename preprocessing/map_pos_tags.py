from argparse import ArgumentParser
import spacy
from spacy.lang.en.tag_map import TAG_MAP, POS
import re

def convert_pos(args):
    """
    Converts the CoNLL fine-grained tags to spaCy coarse-grained tags.

    :param input_file: str, path to the input file
    :param output_file: str, path to the output file
    """

    nlp = spacy.blank("en")

    with open(args.input_file, "r") as f:
        input_lines = f.readlines()

    with open(args.output_file, "w+") as f:
        for line in input_lines[:-1]:
            if line == "\n":
                f.write(line)
            else:
                id, word, lemma, fine_pos, fine_tag, morph, head, dep, _, space_after = line.split("\t")
                if fine_pos == "Ellipsis":
                    coarse_pos = "X" # check if there is a more appropriate tag
                else:
                    coarse_id = TAG_MAP[fine_pos][POS]
                    coarse_pos = nlp.vocab.strings[coarse_id]
                f.write(id + "\t" + word + "\t" + lemma + "\t" + coarse_pos + "\t" + coarse_pos + "\t" + morph + "\t" + head + "\t" + dep + "\t" + _ + "\t" + space_after)

def main():

    parser = ArgumentParser(
        description="Convert CoNLL fine-grained tags to spaCy coarse-grained tags")
    parser.add_argument(
        "-input-file", "--input-file", help="Path to the input file")
    parser.add_argument(
        "-output-file", "--output-file", help="Path to the output file")
    args = parser.parse_args()

    convert_pos(args)

if __name__ == "__main__":
    main()