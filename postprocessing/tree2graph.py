import os
from argparse import ArgumentParser
from nltk import ParentedTree
import re
import json


def convert(input_file, ellipsis_method=None):
    """
    :param input_file: file containing the phrase-structure trees 
    :param ellipsis_method: str, indicating the method for encoding ellipsis, can either be right_label or left_label, default to None
    :return graph: embedded dict, containing the parsed data as a graph
    """

    filename, file_extension = os.path.splitext(input_file)

    with open(input_file, "r", encoding="utf-8") as f:
        trees = f.readlines()

    graph = {"sentences": []}

    for tree in trees:

        tokens = {}
        tree_positions = {}

        t = ParentedTree.fromstring(tree)
        for index, st in enumerate(t.subtrees()):
            tree_positions[st.treeposition()] = index # keep track of indexes & tree positions
            token = {}
            token["id"] = index
            token["children"] = []
#            token["parents"] = []
            token["tag"] = st.label().split("ellipsis")[0]
            ellipsis_tags = st.label().split("ellipsis")[1:]
            token["ellipsis_tag"] = ellipsis_tags
            ellipsed_nodes = []
            # recover the ellipsed nodes
            if ellipsis_method == "right_label" and len(ellipsis_tags) > 0:
                for ellipsed_node in ellipsis_tags:
                    ellipsed_node_i = "".join(re.findall(r"\d+", ellipsed_node))
                    ellipsed_node_tag = re.sub(ellipsed_node_i, "", ellipsed_node)
                    # search the ellipsed node
                    tag_i = 0
                    for node in tokens:
                        if tokens[node]["tag"] == ellipsed_node_tag:
                            if tag_i == int(ellipsed_node_i):
                                ellipsed_nodes.append(node)
                            else:
                                tag_i += 1
            if st.height() == 2:
                token["terminal"] = "yes"
                token["text"] = st.leaves()[0]
            else:
                token["terminal"] = "no"
                token["text"] = ""
            tokens[index] = token
            
            if st.parent() != None:
                parent_index = tree_positions[st.parent().treeposition()]
                # add parent information
#                token["parents"].append(parent_index)
                # add children information
                tokens[parent_index]["children"].extend(ellipsed_nodes) # ellipsed children
                tokens[parent_index]["children"].append(index)          # non-ellipsed children

        graph["sentences"].append({"tokens": [tokens[token] for token in tokens]})
    
    return graph


def main():

    parser = ArgumentParser(
        description="Tree to graph conversion")
    parser.add_argument(
        "-input-dir", "--input-dir", help="Path to the directory containing the input PCFG trees")
    parser.add_argument(
        "-output-dir", "--output-dir", help="Path to the directory where to save the output graphs")
    parser.add_argument(
        "--ellipsis-method", default=None, type=str, help="Ellipsis method (right_label, left_label or None)")
    args = parser.parse_args()

    input_files = os.listdir(args.input_dir)
    for input_file in input_files:
        filename, file_extension = os.path.splitext(input_file)
        full_path = os.path.join(args.input_dir, input_file)
        graph = convert(full_path, args.ellipsis_method)
        with open(os.path.join(args.output_dir, filename + ".json"), "w+") as f:
            json.dump([graph], f)    


if __name__ == "__main__":
    main()