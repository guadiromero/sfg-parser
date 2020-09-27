from pathlib import Path
import typer
from nltk import ParentedTree
import re
import json


def split_tag(tag):
    """
    Split tag to get the constituent tag and the ellipsis tags separately.
    """

    splits = re.split("(start|end)", tag)

    const_tag = splits[0]
    end_tags = []
    start_tags = []
    for index, tag in enumerate(splits):
        if splits[index-1] == "start":
            start_tags.append(tag)
        elif splits[index-1] == "end":
            end_tags.append(tag)

    return const_tag, start_tags, end_tags


def get_basic_graph(tree):
    """
    Convert a phrase-structure tree to a basic graph, without the ellipsis edges.
    """

    t = ParentedTree.fromstring(tree)

    graph = []
    tree_positions = {}
    parent_clauses = {}

    for index, st in enumerate(t.subtrees()):
        tree_positions[st.treeposition()] = index # keep track of indexes & tree positions
        node = {}
        node["id"] = index
        node["children"] = []
        node["parent"] = tree_positions[st.parent().treeposition()] if st.parent() != None else 0
        node["ellipsed_parents"] = []
        const_tag, start_tags, end_tags = split_tag(st.label())
        node["tag"] = const_tag
        node["start_tags"] = start_tags
        node["end_tags"] = end_tags
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

    # keep track of the parent clause for each node
    parent_clauses = {tree_positions[pos]:parent_clauses[pos] for pos in parent_clauses}

    return graph, parent_clauses


def add_ellipsis_starting_node(graph, parent_clauses):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the starting_node tags.
    """

    for node in graph:
        parent = node["parent"]
        start_tags = node["start_tags"]
        end_tags = node["end_tags"]
        ellipsed_nodes = []
        if len(start_tags) > 0:
            for ellipsed_node in start_tags:
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
            next_non_terminal_i = node["id"] + 1 
            if node["tag"] == "VG" and graph[ellipsed_node]["tag"] in ["VG", "VB", "VBD", "VBG", "VBN", "VBP", "VBZ", "TO", "MD", "RB"]:
                vg_exception = True
            else:
                vg_exception = False
            if vg_exception == False:
                while next_non_terminal_i < len(graph) and graph[next_non_terminal_i]["terminal"] == "yes":
                    next_non_terminal_i += 1
            if next_non_terminal_i < len(graph):
                if parent_clauses[next_non_terminal_i] == parent_clauses[node["id"]]:
                    ellipsed_parent = graph[next_non_terminal_i]["parent"]
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

    return graph


def add_ellipsis_ending_node(graph, parent_clauses):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the ending_node tags.
    """

    for node in graph:
        parent = node["parent"]
        start_tags = node["start_tags"]
        end_tags = node["end_tags"]
        ellipsed_nodes = []
        if len(start_tags) > 0:
            for ellipsed_node in start_tags:
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

    return graph


def convert(input_file, strategy):
    """
    Convert phrase-structure trees to graphs.
    """

    with open(input_file, "r", encoding="utf-8") as f:
        trees = f.readlines()

    sents = {"sents": []}

    for tree in trees:
        # get basic tree
        graph, parent_clauses = get_basic_graph(tree)
        # add secondary edges with a specific strategy for decoding ellipsis
        if strategy == "starting-node":
            graph = add_ellipsis_starting_node(graph, parent_clauses)

        sents["sents"].append({"graph": graph})  
       
    return {"docs": [sents]}


def main(
    input_dir: Path, 
    output_dir: Path, 
    strategy: str = typer.Option("", help="Strategy for encoding ellipsis, can be starting_node, ending_node or both_nodes."),
    ):

    for input_file in input_dir.iterdir():
        doc = convert(input_file, strategy)
        output_path = Path.joinpath(output_dir, input_file.name).with_suffix(".json")
        with output_path.open(mode="w+") as f:
            json.dump(doc, f) 


if __name__ == "__main__":
    typer.run(main)