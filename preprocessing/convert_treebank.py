# coding: utf8

import os
from argparse import ArgumentParser
import json
import xml.etree.ElementTree as ET


def split_data(input_dir, train_size=80):
    """
    Split data into training and testing sets.
    
    :param data_dir: str, path to the directory containing the data
    :param train_size: int, size of the training set as percentage
    :return train_files: list, containing the names of the training XML files
    :return test_files: list, containing the names of the testing XML files
    """

    data_files = sorted(os.listdir(input_dir))
    split_index = int(len(data_files) * train_size / 100)
    train_files = data_files[:split_index]
    test_files = data_files[split_index:]

    return train_files, test_files


def parse_data(data_dir, data_files):
    """
    Parse the data files into lists of examples with the following format:
    [text as str, {'entities': [[start index as int, end index as int, entity tag as str, ]]}] 

    For example,
    ['The campus is spacious and beautiful', {'entities': [[0, 10, 'Nominal_Group'], [11, 13, 'Verbal_Group'], [14, 36, 'Nominal_Group']]}]

    :param data_dir: str, path to the directory containing the data
    :param data_files: list, containing the names of the dataset XML files
    """

    data = []

    base_group_types = [
        'Adverbial_Group', 
        'Conjunction_Group', 
        'Nominal_Group', 
        'Verbal_Group',
        ]

    for data_file in data_files:

        full_path = os.path.join(data_dir, data_file)  

        tree = ET.parse(full_path)
        root = tree.getroot()

        # get the example text as str
        text = root[0].text[9:-5]

        # get the example grammar as an Element object
        grammar = root[1]

        annotations = []

        for node in grammar:
            if node.get('type') == 'Clause_Complex':                
                for sub_node in node.iter():
                    if sub_node.get('type') in base_group_types:
                        # skip base group if it contains embedded base groups
                        embed_base_groups = False
                        subsub_nodes = sub_node.iter()
                        next(subsub_nodes) # skip root
                        for subsub_node in subsub_nodes:
                            if subsub_node.get('type') in base_group_types:
                                embed_base_groups = True
                                break
                        if embed_base_groups == False:
                            word_spans = []
                            for subsub_node in sub_node.iter():
                                if subsub_node.get('type') == 'Word':
                                    start = subsub_node.find('StringRef').get('start')
                                    end = subsub_node.find('StringRef').get('end')
                                    word_spans.append((int(start), int(end)))
        #                        elif subsub_node.get('type') == 'Ellipsis':
        #                            word_spans.append(('unknown', 'unknown'))
                            if len(word_spans) > 0: # skip if there is no word_span info (problem with the data whenever there is ellipsis)
                                node_annot = [word_spans[0][0], word_spans[-1][1], sub_node.get('type')]
                                annotations.append(node_annot)

        data.append([text, {'entities': annotations}]) # named entities instead of base_groups to be used by spaCy's NER model
#        break # parse only one tree

    return data


def traverse_tree(node):

    if node.tag == 'Constituent':
        print(node.tag, node.attrib)
    for child in list(node):
        traverse_tree(child)


def xml_to_berkeley(input_dir):

    data_files = sorted(os.listdir(input_dir))   

    for data_file in data_files:

        full_path = os.path.join(input_dir, data_file)  

        tree = ET.parse(full_path)
        root = tree.getroot()

        # get the example text as str
        text = root[0].text[9:-5]

        # get the example grammar as an Element object
        grammar = root[1]

        for node in grammar:
            if node.get('type') == 'Clause_Complex':  
                traverse_tree(node) 

                break
        break 


def main():

    parser = ArgumentParser(
        description='Create training and testing datasets')
    parser.add_argument(
        '-input_dir', '--input_dir', help='Path to the directory containing the input XML data files')
    parser.add_argument(
        '-output_dir', '--output_dir', help='Path to the output directory to save the converted data')
    args = parser.parse_args()

    # split the files into training and testing
#    train_files, test_files = split_data(args.input_dir)

    # parse the training and testing files
#    train_data = parse_data(args.input_dir, train_files)
#    test_data = parse_data(args.input_dir, test_files)

    # save the converted training and testing


    # convert the data format from xml to berkeley
    xml_to_berkeley(args.input_dir)


if __name__ == "__main__":
    main()