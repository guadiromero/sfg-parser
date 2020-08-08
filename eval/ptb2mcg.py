import os
from argparse import ArgumentParser
from nltk import Tree
import spacy
from seg.newline.segmenter import NewLineSegmenter
from spacy.pipeline import Sentencizer
import xml.etree.ElementTree as ET
from xml.dom import minidom


def extract_segments(file_text, file_parse, corpus):
    """
    :param doc_text: absolute path to the text file, where each line is a sentence
    :param doc_parse: absolute path to the parse file, where each line is a parsed sentence as a phrase-structure three
    :return segments_dict: dict, where each key is a segment id, and each value is a dictionary with the text, start index and end index of the segment
    """

    with open(file_text, "r", encoding="utf-8") as f:
        doc_text = f.read()

    if corpus == "OCD":
        nlp = spacy.load("en_core_web_sm", disable=["tagger", "ner", "parser"])
        nlseg = NewLineSegmenter()
        nlp.add_pipe(nlseg.set_sent_starts, name='sentence_segmenter')
    elif corpus == "OE":
        nlp = spacy.load("en_core_web_sm", disable=["tagger", "ner", "parser"]) 
        sentencizer = Sentencizer(punct_chars=["."])  
        nlp.add_pipe(sentencizer) 
    doc = nlp(doc_text)

    with open(file_parse, "r") as f:
        sent_parses = f.readlines()

    segments_list = []

    sent_index = 0
    for sent, parse in zip(doc.sents, sent_parses):
        tokens = {}
        for index, token in enumerate(sent):
            tokens[index] = {}
            start = token.idx
            end = token.idx + len(token.text)
            tokens[index]["start"] = start
            tokens[index]["end"] = end    
            tokens[index]["text"] = doc_text[start:end]

        # get segments from the parse tree
        t = Tree.fromstring(parse)

        for index, treepos in enumerate(t.treepositions("leaves")):
            t[treepos] = index

        segments_ids = []
        for st in t.subtrees():
            # save segment if it is not already saved and if it does not contain only terminals (height=2)
            if corpus == "OCD":
                # exclude punctuation leaves
                st_leaves = [leaf[0] for leaf in st.pos() if leaf[1] not in ["#", "$", '"', "``", "(", ")", "-LRB-", "-RRB-", ",", ":", "."]]
            elif corpus == "OE":
                st_leaves = st.leaves()
            if st_leaves not in segments_ids and st.height() > 2 and len(st_leaves) > 0: 
                segments_ids.append(st_leaves)    
        for index, segment in enumerate(segments_ids):
            segment_start = tokens[segment[0]]["start"] + sent_index # shift the index to fit the bug in the eval script
            segment_end = tokens[segment[-1]]["end"] + sent_index # shift the index to fit the bug in the eval script
            segment_text = doc_text[segment_start:segment_end]
            segments_list.append({"start": segment_start, "end": segment_end, "text": segment_text})
        sent_index += 1

    segments_dict = {}
    for index, data in enumerate(segments_list):
        segments_dict[index] = data

    return segments_dict


def main():

    parser = ArgumentParser(
        description="Split data into train/dev/test sets")
    parser.add_argument(
        "-input-text-dir", "--input-text-dir", help="Path to the directory containing the input texts")
    parser.add_argument(
        "-input-parse-dir", "--input-parse-dir", help="Path to the directory containing the input parses")
    parser.add_argument(
        "-output-dir", "--output-dir", help="Path to the directory where to save the output mcg files")
    parser.add_argument(
        "-corpus", "--corpus", help="Str indicating the corpus to process, can be either OCD or OE")
    args = parser.parse_args()

    doc_texts = sorted(os.listdir(args.input_text_dir))
    doc_parses = sorted(os.listdir(args.input_parse_dir))

    for doc_text, doc_parse in zip(doc_texts, doc_parses):
        filename, file_extension = os.path.splitext(doc_text)
        doc_segments = extract_segments(os.path.join(args.input_text_dir, doc_text), os.path.join(args.input_parse_dir, doc_parse), args.corpus)
        # build xml tree
        document = ET.Element("document")
        header = ET.SubElement(document,"header")
        segments = ET.SubElement(document, "segments")
        textfile = ET.SubElement(header, "textfile")
        lang = ET.SubElement(header, "lang")
        complete = ET.SubElement(header, "complete")
        visited = []
        for segment_id in doc_segments:
            start = doc_segments[segment_id]["start"]
            end = doc_segments[segment_id]["end"]   
            if ((start, end)) not in visited: # do not include duplicates   
                segment = ET.SubElement(segments, "segment")
                segment.set("id", str(start))
                segment.set("start", str(start))
                segment.set("end", str(end))
#                segment.set("text", str(doc_segments[segment_id]["text"]))
                segment.set("state", "active")
                segment.set("features", "constituent")
                visited.append((start, end))
        # write in xml file
        with open(os.path.join(args.output_dir, filename + ".txt.mcg_berkeley.xml"), "w+") as f:
            rough_string = ET.tostring(document, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            f.write(reparsed.toprettyxml(indent=" "))


if __name__ == "__main__":
    main()