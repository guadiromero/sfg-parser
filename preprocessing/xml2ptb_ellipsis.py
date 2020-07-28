# coding: utf8

import os
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import re
from collections import OrderedDict
from tag_maps import TAGS_SFG as tag_map


def traverse_tree(node, text, tag_map, ellipsis_method=None):
    """
    Traverse a tree with first-depth search and return it in PTB-style phrase-structure format.

    :param node: xml.etree.ElementTree.Element object, representing the syntactic tree of the sentence (where the root is a Clause Complex)
    :param text: str, text of the sentence
    :param tag_map: dict, tag map
    :return linearized_tree: str, linearized tree, following the PTB format
    """

    linearized_tree = ""
    tokens = []
    node_metadata = {}
    constituent_counter = {}
    right_label = ""
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
            # enumerate the constituent and get some basic information about it
            node_id = node.get('id')
            node_type = node.get('type')
            if node.tag == "Constituent":
                # terminals
                if node_type in ["Word", "Punctuation"]:
                    terminal = "yes"
                    pos = node[1][0].get('value')[6:]
                    if pos in constituent_counter:
                        constituent_counter[pos] += 1
                    else:
                        constituent_counter[pos] = 0
                    constituent_id = pos + str(constituent_counter[pos])
                # non-terminals
                if node_type not in ["Word", "Punctuation", "Ellipsis"]:
                    terminal = "no"
                    tag = tag_map[node_type]
                    if tag in constituent_counter:
                        constituent_counter[tag] += 1
                    else:
                        constituent_counter[tag] = 0
                    constituent_id = tag + str(constituent_counter[tag])
            # get node span
            span = [subnode.get("idref") for subnode in node.iter() if subnode.tag == "ConstituentRef"]
            # check if the node is completely ellipsed
            ellipsed_node = True
            for subnode in node.iter():
                if subnode.get("type") in ["Word", "Punctuation"]:
                    ellipsed_node = False
            # save ellipsis information from the current node
            if node.tag == "Constituent" and ellipsed_node == True:
                # for the left strategy, add this information to the previous node it refers to
                # for the right strategy, keep this information to add it to the next non-ellipsed node
                for previous_node in node_metadata:
                    # for ellipsed terminals
                    if node_type == "Ellipsis":
                        if previous_node == node.find("ConstituentRef").get("idref"):
                            node_metadata[previous_node]["left_label"] += 1
                            right_label += "ellipsis" + node_metadata[previous_node]["constituent_id"]
                    # for ellipsed non-terminals
                    if node_metadata[previous_node]["terminal"] == "no" and node_metadata[previous_node]["span"] == span:
                        node_metadata[previous_node]["left_label"] += 1
                        right_label += "ellipsis" + node_metadata[previous_node]["constituent_id"]
            # otherwise, add node to the linearized tree
            if node.tag == 'Constituent' and ellipsed_node == False:
                if len(linearized_tree) > 0:
                    linearized_tree += ' '
                linearized_tree += '('
                linearized_tree += node.get('id')
                # create a metadata dictionary for the current node
                node_metadata[node_id] = {}
                node_metadata[node_id]["tag"] = tag
                node_metadata[node_id]["left_label"] = 0
                node_metadata[node_id]["constituent_id"] = constituent_id
                if terminal == "yes":
                    node_metadata[node_id]["terminal"] = "yes"
                    node_metadata[node_id]["pos"] = node[1][0].get('value')[6:]
                    token_text = text[int(node[0].get('start')):int(node[0].get('end'))]
                    node_metadata[node_id]["text"] = token_text
                    tokens.append(token_text)
                else:
                    node_metadata[node_id]["terminal"] = "no"
                    node_metadata[node_id]["span"] = [subnode.get("id") for subnode in node.iter() if subnode.get("type") in ["Word", "Punctuation"]]
                # add right label from the previous node to the current node metadata and restore it to an empty string
                node_metadata[node_id]["right_label"] = right_label       
                right_label = ""             
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
            if ellipsis_method == "left_label" and node_metadata[node]["left_label"] > 0:
                    new_label = node_metadata[node]["tag"] + "ellipsis" + str(node_metadata[node]["left_label"])
            elif ellipsis_method == "right_label" and len(node_metadata[node]["right_label"]) > 0:
                    new_label = node_metadata[node]["tag"] + str(node_metadata[node]["right_label"])
            else:
                new_label = node_metadata[node]["tag"]          
        # for terminals
        else:
            if ellipsis_method == "left_label" and node_metadata[node]["left_label"] > 0:
                    new_label = node_metadata[node]["pos"] + "ellipsis" + str(node_metadata[node]["left_label"]) + " " + node_metadata[node]["text"]
            elif ellipsis_method == "right_label" and len(node_metadata[node]["right_label"]) > 0:
                    new_label = node_metadata[node]["pos"] + str(node_metadata[node]["right_label"]) + " " + node_metadata[node]["text"]
            else:
                new_label = node_metadata[node]["pos"] + " " + node_metadata[node]["text"]
        node_metadata[node]["new_label"] = new_label

    # replace node ids with the new labels in the linearized tree
    for node in node_metadata:
        linearized_tree = re.sub(node, node_metadata[node]["new_label"], linearized_tree, count=1)

    # create sentence string (without duplication of ellipsis as in the SFG corpus)
    string = " ".join(tokens)

    return linearized_tree, string


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
        # new files following the PTB format
        output_ptb_file = open(os.path.join(args.output_ptb_dir, data_file[:-3] + 'ptb'), 'w+')
        if args.output_str_dir:
            output_str_file = open(os.path.join(args.output_str_dir, data_file[:-3] + 'txt'), 'w+')
        for node in grammar:
            if node.get('type') == 'Clause_Complex':
                total += 1
                linearized_tree, string = traverse_tree(node, text, tag_map, args.ellipsis_method)
                tokens = linearized_tree.replace("(", " ( ").replace(")", " ) ").split() 
                if len(tokens) < args.max_len:
                    output_ptb_file.write(linearized_tree + '\n')
                    if args.output_str_dir:
                        output_str_file.write(string + '\n')
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
        '-output-ptb-dir', '--output-ptb-dir', help='Path to the output directory to save the data files in PTB format')
    parser.add_argument(
        '--output-str-dir', default=None, type=str, help='Path to the output directory to save the data files as strings')
    parser.add_argument(
        '--ellipsis-method', default=None, type=str, help='Method for ellipsis recovery')
    parser.add_argument(
        '--max-len', default=512, type=int, help='Maximum length allowed by the BERT model')
    args = parser.parse_args()

    # convert the data format from XML to PTB format
    convert_treebank(args, tag_map)


if __name__ == "__main__":
    main()