import os
from argparse import ArgumentParser
import spacy
from spacy.pipeline import Sentencizer
from seg.newline.segmenter import NewLineSegmenter
import re


def tokenize(full_input_path, corpus):

    with open(full_input_path, "r") as f:
        text = f.read()
        text = re.sub("\n", "", text)
        text = re.sub("\ufeff", "", text)

    if corpus == "OCD":
        nlp = spacy.load("en_core_web_sm", disable=["tagger", "ner", "parser"])
        nlseg = NewLineSegmenter()
        nlp.add_pipe(nlseg.set_sent_starts, name='sentence_segmenter')
    elif corpus == "OE":
        nlp = spacy.load("en_core_web_sm", disable=["tagger", "ner", "parser"]) 
        sentencizer = Sentencizer(punct_chars=[".", "\n"])  
        nlp.add_pipe(sentencizer) 
    doc = nlp(text)

    tokenized_sents = []
    for sent in doc.sents:
        tokens = []
        for token in sent:
            if token.text == "(":
                token_text = "-LRB-"
            elif token.text == ")":
                token_text = "-RRB-"
            elif token.text in [":)", ":-)", ":(", ":-("]:
                token_text = "-EMOJI-"
            else:
                token_text = token.text
            tokens.append(token_text)
        tokenized_sent = " ".join(tokens)
        tokenized_sents.append(tokenized_sent)

    if corpus == "OCD":    
        tokenized_text = "".join(tokenized_sents)
    elif corpus == "OE":
        non_empty_sents = []
        for sent in tokenized_sents:
            non_empty_sents.append(sent.lstrip())
        tokenized_text = "\n".join(non_empty_sents)
    return tokenized_text
        

def main():

    parser = ArgumentParser(
        description="Separate all tokens in a text by blankspace")
    parser.add_argument(
        "-input-dir", "--input-dir", help="Path to the directory containing the input texts")
    parser.add_argument(
        "-output-dir", "--output-dir", help="Path to the directory where to save the output texts")
    parser.add_argument(
        "-corpus", "--corpus", help="Str indicating the corpus to process, can be either OCD or OE")
    args = parser.parse_args()

    input_files = os.listdir(args.input_dir)

    for file_ in input_files:
        full_input_path = os.path.join(args.input_dir, file_)
        full_output_path = os.path.join(args.output_dir, file_)
        tokenized_text = tokenize(full_input_path, args.corpus)
        with open(full_output_path, "w+") as f:
            f.write(tokenized_text)


if __name__ == "__main__":
    main()