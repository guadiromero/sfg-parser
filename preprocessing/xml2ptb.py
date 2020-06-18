# coding: utf8

import os
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
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

def traverse_tree(node, text, tag_map):
    """
    Traverse a tree with first-depth search and return it in Penn Treebank format.

    :param node: xml.etree.ElementTree.Element object, representing the syntactic tree of the sentence (Clause Complex)
    :param text: str, text of the sentence
    :param tag_map: dict, map of SFG to Penn Treebank tags
    :return linearized_tree: str, linearized tree, following the Penn Treebank format
    """

    linearized_tree = ''
    stack = []

    # push the root of the tree to the stack
    stack.append(node)
    
    while len(stack) > 0:
       # pop the last element in the stack
        node = stack.pop()
        # add the current node to the linearized tree
        if node == ')':
            linearized_tree += ')'
        else:
            # skip node if it only contains ellipsis
            ellipsis = True
            for subnode in node.iter():
                if subnode.get("type") in ["Word", "Punctuation"]:
                    ellipsis = False
            if node.tag == 'Constituent' and ellipsis == False:
                if len(linearized_tree) > 0:
                    linearized_tree += ' '
                linearized_tree += '('
                if node.get('type') in ['Word', 'Punctuation']:
                    pos = node[1][0].get('value')[6:]
                    word_text = text[int(node[0].get('start')):int(node[0].get('end'))]
                    linearized_tree += pos + ' ' + word_text
                # keep ellipsis
#                elif node.get('type') in ['Ellipsis']:
#                    linearized_tree += 'Ellipsis <Ellipsis>'
                else:
                    linearized_tree += node.get('type')
            # push the direct children of the current node to the stack, from right to left
            for child in reversed(list(node)):
                # skip if it only contains ellipsis
                ellipsis = True 
                for subnode in child.iter():
                    if subnode.get("type") in ["Word", "Punctuation"]:
                        ellipsis = False    
                if child.tag == 'Constituent' and ellipsis == False:
                    stack.append(')')           
                stack.append(child)
    linearized_tree += ')'

    # map SFG to Penn Treebank tags
    for tag in TAG_MAP:
        linearized_tree = re.sub(tag, TAG_MAP[tag], linearized_tree)

    return linearized_tree


def convert_treebank(args, tag_map):
    """
    Convert treebank from XML to the PTB format.

    :param tag_map: ordered dict, map of SFG to PTB tags
    """

    data_files = sorted(os.listdir(args.input_dir))  
    total = 0
    deleted = 0 

    for data_file in data_files:

        # read the file
        full_path = os.path.join(args.input_dir, data_file)  
        tree = ET.parse(full_path)
        root = tree.getroot()

        # get the example text as str
        text = root[0].text[9:-5]

        # get the example grammar as an Element object
        grammar = root[1]

        # traverse all the trees in the file and write them in
        # new files following the Penn Treebank format
        output_file = open(os.path.join(args.output_dir, data_file[:-3] + 'ptb'), 'w+')
        for node in grammar:
            if node.get('type') == 'Clause_Complex':
                total += 1
                linearized_tree = traverse_tree(node, text, tag_map)
                tokens = linearized_tree.replace("(", " ( ").replace(")", " ) ").split() 
                if len(tokens) < args.max_len:
                    output_file.write(linearized_tree + '\n')
                else:
                    deleted += 1

    print('Conversion from XML to Penn Treebank format ready!')
    print(str(deleted) + ' sentences out of ' + str(total) + ' were deleted because they excedeed the maximum sequence length of ' + str(args.max_len) + '. This gives a total of ' + str(total-deleted) + ' sentences.')


def main():

    parser = ArgumentParser(
        description='Convert treebank from XML to Penn Treebank format')
    parser.add_argument(
        '-input-dir', '--input-dir', help='Path to the directory containing the input XML data files')
    parser.add_argument(
        '-output-dir', '--output-dir', help='Path to the output directory to save the converted data files')
    parser.add_argument(
        '--max-len', default=512, type=int, help='Maximum length allowed by the BERT model')
    args = parser.parse_args()

    # convert the data format from XML to Penn Treebank format
    convert_treebank(args, TAG_MAP)


if __name__ == "__main__":
    main()