from pathlib import Path
import typer
from nltk import ParentedTree
import re
import json


def convert(input_file, right_label):
    """
    :param input_file: file containing the phrase-structure trees 
    :param right_label: bool, whether the ellipsis has been encoded with the right label strategy or not
    :return graph: embedded dict, containing the parsed data as a graph
    """

    with open(input_file, "r", encoding="utf-8") as f:
        trees = f.readlines()

    sents = {"sents": []}

    for tree in trees:

        graph = []
        tree_positions = {}

        # build graph
        t = ParentedTree.fromstring(tree)
#        parent_clause = 0
        parent_clauses = {}
        for index, st in enumerate(t.subtrees()):
            tree_positions[st.treeposition()] = index # keep track of indexes & tree positions
            node = {}
            node["id"] = index
            node["children"] = []
            node["parent"] = tree_positions[st.parent().treeposition()] if st.parent() != None else 0
            node["ellipsed_parents"] = []
            node["tag"] = st.label().split("ellipsis")[0] # -ellipsis
            ellipsis_tags = st.label().split("ellipsis")[1:] # -ellipsis
            node["ellipsis_tags"] = ellipsis_tags
            if st.height() == 2:
                node["terminal"] = "yes"
                node["text"] = st.leaves()[0]
            else:
                node["terminal"] = "no"
                node["text"] = ""
            if node["tag"] == "CL":
                for child in st.subtrees():
                    parent_clauses[child.treeposition()] = index
            graph.append(node)  

        parent_clauses = {tree_positions[pos]:parent_clauses[pos] for pos in parent_clauses}

        # recover ellipsed nodes
        for node in graph:
            parent = node["parent"]
            ellipsis_tags = node["ellipsis_tags"]
            ellipsed_nodes = []
            if right_label and len(ellipsis_tags) > 0:
                for ellipsed_node in ellipsis_tags:
                    ellipsed_node_i = "".join(re.findall(r"\d+", ellipsed_node))
                    ellipsed_node_tag = re.sub(ellipsed_node_i, "", ellipsed_node)
                    # find the ellipsed node
                    tag_i = 0
                    for node2 in graph:
                        if node2["tag"] == ellipsed_node_tag:
                            if tag_i == int(ellipsed_node_i):
                                ellipsed_nodes.append(node2["id"])
                                break
                            else:
                                tag_i += 1       
            for ellipsed_node in ellipsed_nodes:
                # add ellipsed parent information            
#                if node["id"]+1 < len(graph) and graph[node["id"]+1]["tag"] not in [",", ":", "``", '"', "-LRB-", "-RRB-"]:
#                    if parent_clauses[node["id"]+1] == parent_clauses[node["id"]]:
#                        ellipsed_parent = graph[node["id"]+1]["parent"]
#                    else: 
#                        ellipsed_parent = parent_clauses[node["id"]]
#                else:
#                    ellipsed_parent = graph[node["id"]]["parent"]   
                if node["id"]+1 < len(graph):
                    if parent_clauses[node["id"]+1] == parent_clauses[node["id"]]:
                        ellipsed_parent = graph[node["id"]+1]["parent"]
                    else: 
                        ellipsed_parent = parent_clauses[node["id"]]
                else:
                    ellipsed_parent = parent_clauses[node["id"]]         
                graph[ellipsed_node]["ellipsed_parents"].append(graph[ellipsed_parent]["id"])
                # add ellipsed children information
                graph[ellipsed_parent]["children"].append(ellipsed_node)
            # add non-ellipsed children information
            if node["id"] != 0:
                graph[parent]["children"].append(node["id"])

        sents["sents"].append({"graph": graph})  
       
    return {"docs": [sents]}


def main(
    input_dir: Path, 
    output_dir: Path, 
    right_label: bool = typer.Option(False, help="Use right label strategy to decode ellipsis"),
    ):

    for input_file in input_dir.iterdir():
        doc = convert(input_file, right_label)
        output_path = Path.joinpath(output_dir, input_file.name).with_suffix(".json")
        with output_path.open(mode="w+") as f:
            json.dump(doc, f) 


if __name__ == "__main__":
    typer.run(main)