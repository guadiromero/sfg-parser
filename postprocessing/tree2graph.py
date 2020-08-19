from pathlib import Path
import typer
from nltk import ParentedTree
import re
import json


def convert(input_file, ellipsis_method):
    """
    :param input_file: file containing the phrase-structure trees 
    :param ellipsis_method: str, indicating the method for encoding ellipsis, can either be right_label or left_label
    :return graph: embedded dict, containing the parsed data as a graph
    """

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
            token["parent"] = 0
            token["parent_ellipsed"] = []
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
                token["parent"] = parent_index                          # non-ellipsed children
                for ellipsed_node in ellipsed_nodes:                    # ellipsed children                    
                    tokens[ellipsed_node]["parent_ellipsed"].append(parent_index)
                # add children information
                tokens[parent_index]["children"].extend(ellipsed_nodes) # ellipsed children
                tokens[parent_index]["children"].append(index)          # non-ellipsed children

        graph["sentences"].append({"tokens": [tokens[token] for token in tokens]})
    
    return graph


def main(input_dir: Path, output_dir: Path, ellipsis_method: str=""):
    for input_file in input_dir.iterdir():
        graph = convert(input_file, ellipsis_method)
        output_path = Path.joinpath(output_dir, input_file.name).with_suffix(".json")
        with output_path.open(mode="w+") as f:
            json.dump(graph, f) 


if __name__ == "__main__":
    typer.run(main)