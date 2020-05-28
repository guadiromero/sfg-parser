# coding: utf8

import os
from argparse import ArgumentParser
import xml.etree.ElementTree as ET


def traverse_tree(node, text):
    """
    Traverse a tree with first-depth search and return it in the linearized Berkeley format.

    :param node: xml.etree.ElementTree.Element object, representing the syntactic tree of the sentence (Clause Complex)
    :param text: str, text of the sentence
    :return linearized_tree: str, linearized tree, following the Berkeley format
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
            if node.tag == 'Constituent':
                if len(linearized_tree) > 0:
                    linearized_tree += ' '
                linearized_tree += '('
                if node.get('type') in ['Word', 'Punctuation']:
                    pos = node[1][0].get('value')[6:]
                    word_text = text[int(node[0].get('start')):int(node[0].get('end'))]
                    linearized_tree += pos + ' ' + word_text
                elif node.get('type') in ['Ellipsis']:
                    linearized_tree += 'Ellipsis <Ellipsis>'
                else:
                    linearized_tree += node.get('type')
            # push the children of the current node to the stack, from right to left
            for child in reversed(list(node)): 
                if child.tag == 'Constituent':
                    stack.append(')')           
                stack.append(child)
    linearized_tree += ')'

    return linearized_tree


def convert_treebank(input_dir, output_dir, max_len):
    """
    Convert treebank from XML to the Berkeley Parser format.

    :param input_dir: str, path to the directory containing the input XML data files
    :param output_dir: str, path to the output directory to save the converted data files
    """

    data_files = sorted(os.listdir(input_dir))  
    total = 0
    deleted = 0 

    for data_file in data_files:

        # read the file
        full_path = os.path.join(input_dir, data_file)  
        tree = ET.parse(full_path)
        root = tree.getroot()

        # get the example text as str
        text = root[0].text[9:-5]

        # get the example grammar as an Element object
        grammar = root[1]

        # traverse all the trees in the file and write them in
        # new files following the linearized Berkeley format
        output_file = open(os.path.join(output_dir, data_file[:-3] + 'bkl'), 'w+')
        for node in grammar:
            if node.get('type') == 'Clause_Complex':
                total += 1
                linearized_tree = traverse_tree(node, text)
                tokens = linearized_tree.replace("(", " ( ").replace(")", " ) ").split() 
                if len(tokens) < max_len:
                    output_file.write(linearized_tree + '\n')
                else:
                    deleted += 1

    print('Conversion from XML to Berkeley Parser format ready!')
    print(str(deleted) + ' sentences out of ' + str(total) + ' were deleted because they excedeed the maximum sequence length of ' + str(max_len))


def main():

    parser = ArgumentParser(
        description='Convert treebank from XML to the Berkeley Parser format')
    parser.add_argument(
        '-input_dir', '--input_dir', help='Path to the directory containing the input XML data files')
    parser.add_argument(
        '-output_dir', '--output_dir', help='Path to the output directory to save the converted data files')
    parser.add_argument(
        '--max_len', default=512, type=int, help='Maximum length allowed by the BERT model')
    args = parser.parse_args()

    # convert the data format from xml to berkeley
    convert_treebank(args.input_dir, args.output_dir, args.max_len)


if __name__ == "__main__":
    main()