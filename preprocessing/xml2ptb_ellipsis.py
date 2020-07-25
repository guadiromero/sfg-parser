# coding: utf8

import os
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import re
from collections import OrderedDict
from tag_maps import TAGS_SFG as tag_map


def traverse_tree(node, text, tag_map, ellipsis_method=None):
    """
    Traverse a tree with first-depth search and return it in PTB format.

    :param node: xml.etree.ElementTree.Element object, representing the syntactic tree of the sentence (where the root is a Clause Complex)
    :param text: str, text of the sentence
    :param tag_map: dict, tag map
    :return linearized_tree: str, linearized tree, following the PTB format
    """

    linearized_tree = ''
    node_metadata = {}
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
            # get node span
            span = [subnode.get("idref") for subnode in node.iter() if subnode.tag == "ConstituentRef"] # ERASE
            # check if the node is completely ellipsed
            ellipsed_node = True
            for subnode in node.iter():
                if subnode.get("type") in ["Word", "Punctuation"]:
                    ellipsed_node = False
            # keep a track of ellipsis in the metadata dictionary (left label strategy)
            if node.tag == "Constituent" and ellipsed_node == True:
                for previous_node in node_metadata:
                    # for ellipsed terminals
                    if node.get("type") == "Ellipsis":
                        if previous_node == node.find("ConstituentRef").get("idref"):
                            node_metadata[previous_node]["ellipsis"] += 1
                    # for ellipsed non-terminals
                    if node_metadata[previous_node]["terminal"] == "no" and node_metadata[previous_node]["span"] == span:
                        node_metadata[previous_node]["ellipsis"] += 1
            # otherwise, add node to the linearized tree
            if node.tag == 'Constituent' and ellipsed_node == False:
                if len(linearized_tree) > 0:
                    linearized_tree += ' '
                linearized_tree += '('
                linearized_tree += node.get('id')
                # create a metadata dict for the current node
                node_id = node.get('id')
                node_type = node.get('type')
                node_metadata[node_id] = {}
                node_metadata[node_id]["tag"] = node_type
                node_metadata[node_id]["ellipsis"] = 0
                if node_type in ["Word", "Punctuation"]:
                    node_metadata[node_id]["terminal"] = "yes"
                    node_metadata[node_id]["text"] = text[int(node[0].get('start')):int(node[0].get('end'))]
                    node_metadata[node_id]["pos"] = node[1][0].get('value')[6:]
                else:
                    node_metadata[node_id]["terminal"] = "no"
                    node_metadata[node_id]["span"] = [subnode.get("id") for subnode in node.iter() if subnode.get("type") in ["Word", "Punctuation"]]
            # push the direct children of the current node to the stack, from right to left
            if ellipsed_node == False:
                for child in reversed(list(node)):
                    # skip child if it only contains ellipsis
                    ellipsed_child = True 
                    for subnode in child.iter():
                        if subnode.get("type") in ["Word", "Punctuation"]:
                            ellipsed_child = False    
                    if child.tag == 'Constituent' and ellipsed_child == False:
                        stack.append(')')           
                    stack.append(child)
    linearized_tree += ')'

    # create new labels for the phrase-structure representation
    for node in node_metadata:
        # for non-terminals
        if node_metadata[node]["terminal"] == "no":
            if node_metadata[node]["ellipsis"] > 0:
                new_label = tag_map[node_metadata[node]["tag"]] + "_ellipsis" + str(node_metadata[node]["ellipsis"])
            else:
                new_label = tag_map[node_metadata[node]["tag"]]
        # for terminals
        else:
            if node_metadata[node]["ellipsis"] > 0:
                new_label = node_metadata[node]["pos"] + "_ellipsis" + str(node_metadata[node]["ellipsis"]) + " " + node_metadata[node]["text"]
            else:
                new_label = node_metadata[node]["pos"] + " " + node_metadata[node]["text"]
        node_metadata[node]["new_label"] = new_label

    # replace node ids with the new labels in the linearized tree
    for node in node_metadata:
        linearized_tree = re.sub(node, node_metadata[node]["new_label"], linearized_tree, count=1)

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

    print('Conversion from XML to PTB format ready!')
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

    # convert the data format from XML to PTB format
    convert_treebank(args, tag_map)


if __name__ == "__main__":
    main()