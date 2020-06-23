# coding: utf8

from argparse import ArgumentParser
import spacy
from spacy.gold import docs_to_json
from spacy.tokenizer import Tokenizer
import json


def main():

    parser = ArgumentParser(
        description='Parse data with a trained spaCy model')
    parser.add_argument(
        '-input-file', '--input-file', help='Path to the input file containing the raw text to parse')
    parser.add_argument(
        '-output-file', '--output-file', help='Path to the output file where to save the parsed data as JSON')
    parser.add_argument(
        '-model', '--model', help='Path to the trained model')
    args = parser.parse_args()

    with open(args.input_file, 'r') as f:
        input_file = f.readlines()

    nlp = spacy.load(args.model)
    nlp.tokenizer = Tokenizer(nlp.vocab) # tokenize by blank space

    docs = []

    for line in input_file:
        doc = nlp(line.strip('\n'))
        docs.append(doc)

    json_docs = docs_to_json(docs)  

    # reformat to one doc per sentence
    json_docs = [{'id':index, 'paragraphs':[par,]} for index, par in enumerate(json_docs['paragraphs'])]

    with open(args.output_file, 'w+') as f:
        json.dump(json_docs, f)  


if __name__ == "__main__":
    main()