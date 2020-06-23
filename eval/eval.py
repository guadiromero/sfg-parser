# coding: utf8

from argparse import ArgumentParser
import spacy
from spacy.gold import Example, TokenAnnotation
from spacy.tests.util import get_doc
from spacy.scorer import Scorer
from spacy.vocab import Vocab
import json


def main():

    parser = ArgumentParser(
        description='Evaluate parser')
    parser.add_argument(
        '-predicted', '--predicted', help='Path to the json file with the predicted dependencies')
    parser.add_argument(
        '-gold', '--gold', help='Path to json file with the gold dependencies')
    args = parser.parse_args()

    with open(args.predicted, 'r') as f:
        predicted = json.load(f)

    with open(args.gold, 'r') as f:
        gold = json.load(f) 

    sents = []
    vocab_list = []

    heads_pred = []
    deps_pred = []

    for p in predicted:
        words = []
        heads = []
        deps = []
        for par in p['paragraphs']:
            for sent in par['sentences']:
                for token in sent['tokens']:
                    words.append(token['orth'])
                    vocab_list.append(token['orth'])
                    heads.append(token['head'])
                    deps.append(token['dep'])   
        sents.append(words)
        heads_pred.append(heads)
        deps_pred.append(deps)    

    heads_gold = []
    deps_gold = []

    for g in gold:
        heads = []
        deps = []
        for par in g['paragraphs']:
            for sent in par['sentences']:
                for token in sent['tokens']:
                    heads.append(int(token['head']) + int(token['id'])) # convert relative head to absolute head
                    deps.append(token['dep'])
        heads_gold.append(heads)
        deps_gold.append(deps)

    vocab = Vocab(strings=vocab_list)
    scorer = Scorer()

    for sent, head_pred, dep_pred, head_gold, dep_gold in zip(sents, heads_pred, deps_pred, heads_gold, deps_gold):
        doc = get_doc(vocab=vocab, words=sent, heads=head_pred, deps=dep_pred)
        annotations = TokenAnnotation(words=sent, heads=head_gold, deps=dep_gold)
        example = Example(doc=doc, token_annotation=annotations)
        scorer.score(example)

    print('Scores:')
    print('UAS: ' + str(round(scorer.uas, 2)))
    print('LAS: ' + str(round(scorer.las, 2)))


if __name__ == "__main__":
    main()