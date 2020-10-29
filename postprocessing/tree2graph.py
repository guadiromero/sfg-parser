from pathlib import Path
import typer
from nltk import Tree, ParentedTree
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


def remove_extra_nodes(tree):
    """
    Remove any extra nodes encoding ellipsis.
    """

    def traverse(tree):
        children = []
        for subtree in tree:
            if type(subtree) == str:
                children.append(subtree)
            else:
                if "end" in subtree.label() or "start" in subtree.label():
                    child = [sst for sst in subtree][0]
                    children.append(Tree(subtree.label(), [sst for sst in child]))
                else:
                    children.append(traverse(subtree))

        return Tree(tree.label(), children)

    new_tree = traverse(tree)

    return new_tree


def get_basic_graph(tree, strategy):
    """
    Convert a phrase-structure tree to a basic graph, without the ellipsis edges.
    """

    t = ParentedTree.fromstring(tree)

    if strategy in ["end-extra-node", "start-end-extra-node", "start-end-extra-node-heuristic"]:
        t = remove_extra_nodes(t)
        t = ParentedTree.convert(t)

    graph = []
    tree_positions = {}
    parent_clauses = {}

    start_index = 0
    end_index = 0

    for index, st in enumerate(t.subtrees()):
        tree_positions[st.treeposition()] = index # keep track of indexes & tree positions
        node = {}
        node["id"] = index
        node["children"] = []
        node["parent"] = tree_positions[st.parent().treeposition()] if st.parent() != None else 0
        node["ellipsed_parents"] = []
        const_tag, start_tags, end_tags = split_tag(st.label())
        # assign indexes for start and end tags if they don't have any (heuristic)
        if const_tag == "CL":
            start_index = 0
        if strategy == "start-end-extra-node-heuristic":
#        for tag_i, tag in enumerate(start_tags):
#            if tag == "":
#                start_tags[tag_i] = start_index
#                start_index += 1
#        for tag_i, tag in enumerate(end_tags):
#            if tag == "":
#                end_tags[tag_i] = end_index
#                end_index += 1
            for tag_i, tag in enumerate(start_tags):
                start_tags[tag_i] = start_index
                start_index += 1
            for tag_i, tag in enumerate(end_tags):
                end_tags[tag_i] = end_index
            if len(end_tags) > 0:
                end_index += 1
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

    # assign CLX as the parent clause for nodes which don't have a CL parent
    for node in graph:
        if node["id"] in parent_clauses:
            node["parent_clause"] = parent_clauses[node["id"]]
        else:
            node["parent_clause"] = 0

    return graph


def add_ellipsis_start(graph):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the starting node strategy.
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
            if next_non_terminal_i < len(graph):
                if graph[next_non_terminal_i]["parent_clause"] == graph[node["id"]]["parent_clause"]:
                    ellipsed_parent = graph[next_non_terminal_i]["parent"]
                else: 
                    ellipsed_parent = graph[node["id"]]["parent_clause"]
            else:
                ellipsed_parent = graph[node["id"]]["parent_clause"]         
            graph[ellipsed_node]["ellipsed_parents"].append(graph[ellipsed_parent]["id"])
            # add ellipsed children information
            graph[ellipsed_parent]["children"].append(ellipsed_node)
        # add non-ellipsed children information
        if node["id"] != 0:
            graph[parent]["children"].append(node["id"])

    return graph


def add_ellipsis_start_without_pos(graph):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the starting node (without pos) strategy.
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
                if graph[next_non_terminal_i]["parent_clause"] == graph[node["id"]]["parent_clause"]:
                    ellipsed_parent = graph[next_non_terminal_i]["parent"]
                else: 
                    ellipsed_parent = graph[node["id"]]["parent_clause"]
            else:
                ellipsed_parent = graph[node["id"]]["parent_clause"]         
            graph[ellipsed_node]["ellipsed_parents"].append(graph[ellipsed_parent]["id"])
            # add ellipsed children information
            graph[ellipsed_parent]["children"].append(ellipsed_node)
        # add non-ellipsed children information
        if node["id"] != 0:
            graph[parent]["children"].append(node["id"])

    return graph


def add_ellipsis_end(graph):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the ending node strategy.
    """

    # add start ellipsis tags
    for node in graph:
        end_tags = node["end_tags"]
        ellipsed_locations = []
        if len(end_tags) > 0:
            for ellipsed_location in end_tags:
                ellipsed_location_i = "".join(re.findall(r"\d+", ellipsed_location))
                ellipsed_location_tag = re.sub(ellipsed_location_i, "", ellipsed_location)
                # find the ellipsed node
                tag_i = 0
                for node2 in graph:
                    if node2["tag"] == ellipsed_location_tag:
                        if tag_i == int(ellipsed_location_i):
                            ellipsed_locations.append(node2["id"])
                            break
                        else:
                            tag_i += 1       
        for ellipsed_location in ellipsed_locations:
            graph[ellipsed_location]["start_tags"].append(node["id"])

    # now decode ellipsis using the start tags
    for node in graph:
        parent = node["parent"]
        ellipsed_nodes = node["start_tags"]      
        for ellipsed_node in ellipsed_nodes:
            next_non_terminal_i = node["id"] + 1 
            if next_non_terminal_i < len(graph):
                if graph[next_non_terminal_i]["parent_clause"] == graph[node["id"]]["parent_clause"]:
                    ellipsed_parent = graph[next_non_terminal_i]["parent"]
                else: 
                    ellipsed_parent = graph[node["id"]]["parent_clause"]
            else:
                ellipsed_parent = graph[node["id"]]["parent_clause"]         
            graph[ellipsed_node]["ellipsed_parents"].append(graph[ellipsed_parent]["id"])
            # add ellipsed children information
            graph[ellipsed_parent]["children"].append(ellipsed_node)
        # add non-ellipsed children information
        if node["id"] != 0:
            graph[parent]["children"].append(node["id"])

    return graph


def add_ellipsis_start_end_extra_node(graph):
    """
    Add ellipsed edges to a basic graph, decoding ellipsis with the start-end-extra-node strategy.
    """

    for node in graph:
        parent = node["parent"]
        start_tags = node["start_tags"]
        ellipsed_nodes = []
        if len(start_tags) > 0:
            for start_id in start_tags:
                # find the ellipsed node
                for node2 in graph:
                    if start_id in node2["end_tags"]:
                        ellipsed_nodes.append(node2["id"])
                        break      
        for ellipsed_node in ellipsed_nodes:
            next_non_terminal_i = node["id"] + 1 
            if next_non_terminal_i < len(graph):
                if graph[next_non_terminal_i]["parent_clause"] == graph[node["id"]]["parent_clause"]:
                    ellipsed_parent = graph[next_non_terminal_i]["parent"]
                else: 
                    ellipsed_parent = graph[node["id"]]["parent_clause"]
            else:
                ellipsed_parent = graph[node["id"]]["parent_clause"]         
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
        graph = get_basic_graph(tree, strategy)
        # add secondary edges with a specific strategy for decoding ellipsis
        if strategy == "start":
            graph = add_ellipsis_start(graph)
        elif strategy == "start-without-pos":
            graph = add_ellipsis_start_without_pos(graph)
        elif strategy == "end":
            graph = add_ellipsis_end(graph)
        elif strategy == "end-extra-node":
            graph = add_ellipsis_end(graph)
        elif strategy == "start-end-extra-node":
            graph = add_ellipsis_start_end_extra_node(graph)
        elif strategy == "start-end-extra-node-heuristic":
            graph = add_ellipsis_start_end_extra_node(graph)

        sents["sents"].append({"graph": graph})  
       
    return {"docs": [sents]}


def main(
    input_dir: Path, 
    output_dir: Path, 
    strategy: str = typer.Option("start-end-extra-node-heuristic", help="Strategy for encoding ellipsis: start, start-without-pos, end, end-extra-node, start-end-extra-node"),
    ):

    for input_file in input_dir.iterdir():
        doc = convert(input_file, strategy)
        output_path = Path.joinpath(output_dir, input_file.name).with_suffix(".json")
        with output_path.open(mode="w+") as f:
            json.dump(doc, f) 


if __name__ == "__main__":
    typer.run(main)