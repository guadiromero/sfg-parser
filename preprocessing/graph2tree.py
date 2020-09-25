from pathlib import Path
import typer
import json
from nltk import ParentedTree as Tree
import re


def get_ellipsis_tag_from_graph(graph, target_node):
    """
    Given a graph and a node, get the starting_node ellipsis tag for it.
    """

    counter = 0
    for node in graph:
        if node["tag"] == graph[target_node]["tag"]:
            if node["id"] != graph[target_node]["id"]:
                counter += 1
            else:
                ellipsis_tag = "start" + node["tag"] + str(counter)
                return ellipsis_tag


def get_ellipsis_tag_from_tree(tree, target_position):
    """
    Given a tree and a tree position, get the ending_node ellipsis tag for it.
    """

    counter = 0
    target_tag = tree[target_position].label()
    for node in tree.subtrees():
        if node.label() == target_tag:
            if node.treeposition() != target_position:
                counter += 1
            else:
                ellipsis_tag = "end" + target_tag + str(counter)
                return ellipsis_tag


def get_ellipsis_location(tree, target_tag):
    """
    Given a tree and an ending_node ellipsis tag, get the tree position for it.
    """

    index = "".join(re.findall(r"\d+", target_tag))
    tag = re.sub(index, "", target_tag)
    counter = 0
    for node in tree.subtrees():
        if node.label().split("end")[0] == tag:
            if counter == int(index):
                return node.treeposition()
            else:
                counter += 1  


def traverse_graph_no_strategy(graph, node):  
    """
    Convert a single graph to a phrase-structure tree, without encoding ellipsis.
    """

    children = [int(c) for c in graph[node]["children"]]
    tagged_children = []
    for child in children:
        ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
        # if the child is explicit
        if node not in ellipsed_parents:
            if graph[child]["terminal"] == "yes":
                tagged_children.append(Tree(graph[child]["tag"], [graph[child]["text"]]))
            else:
                tagged_children.append(traverse_graph_no_strategy(graph, child))
           
    tree = Tree(graph[node]["tag"], tagged_children)

    return tree
  

def traverse_graph_starting_node(graph, node):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appendig a tag to the starting node of the ellipsis edge.
    """

    children = [int(c) for c in graph[node]["children"]]
    tagged_children = []
    for child in children:
        ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
        # if the child is explicit
        if node not in ellipsed_parents:
            if graph[child]["terminal"] == "yes":
                tagged_children.append(Tree(graph[child]["tag"], [graph[child]["text"]]))
            else:
                tagged_children.append(traverse_graph_starting_node(graph, child))
        # if the child is ellipsed
        else:
            ellipsis_tag = get_ellipsis_tag_from_graph(graph, child)
            tagged_children.append(Tree(ellipsis_tag, []))
           
    tree = Tree(graph[node]["tag"], tagged_children)

    return tree


def traverse_graph_ending_node(graph, node):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appending a tag to the ending node of the ellipsis edge.
    """

    # get tree with starting_node tags
    tree = traverse_graph_starting_node(graph, node)

    # get ending_node tags
    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    end_tags = []
    for pos_i, pos in enumerate(positions):
        if tree[pos].label().startswith("start"):
            ellipsis_tag = tree[pos].label().split("start")[-1]
            end_location = get_ellipsis_location(tree, ellipsis_tag)
            start_location = pos_i
            while tree[positions[start_location]].label().startswith("start"):
                start_location -= 1
            end_tag = get_ellipsis_tag_from_tree(tree, positions[start_location])
            end_tags.append((end_location, end_tag))

    # insert ending_node tags
    for index, st in enumerate(tree.subtrees()):
        for end_location, end_tag in end_tags:
            if st.treeposition() == end_location:
                st.insert(index, Tree(end_tag, []))

    # delete starting_node tags
    subtrees = [st for st in tree.subtrees()]
    reversed_subtrees = [st for st in reversed(subtrees)]
    for st in reversed_subtrees:
        if st.label().startswith("start"):
            del tree[st.treeposition()]

    return tree


def traverse_graph_both_nodes(graph, node):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appending a tag to both the starting and ending nodes of the ellipsis edge.
    """

    # get the with starting_node tags
    tree = traverse_graph_starting_node(graph, node)

    # get ending_node tags and modify starting_node tags to fit the both_nodes strategy scheme
    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    end_tags = []
    ellipsis_counter = 0
    for pos in positions:
        if tree[pos].label().startswith("start"):
            ellipsis_tag = tree[pos].label().split("start")[-1]
            end_location = get_ellipsis_location(tree, ellipsis_tag)
            tree[pos].set_label("start" + str(ellipsis_counter))
            end_tag = "end" + str(ellipsis_counter)
            end_tags.append((end_location, end_tag))
            ellipsis_counter += 1

    # insert ending_node tags
    for index, st in enumerate(tree.subtrees()):
        for end_location, end_tag in end_tags:
            if st.treeposition() == end_location:
                st.insert(index, Tree(end_tag, []))

    return tree


def get_string(graph, strategy):
    """
    Get string representation from a tree.
    """

    if strategy == "starting_node":
        tree = traverse_graph_starting_node(graph, 0)
    elif strategy == "ending_node":
        tree = traverse_graph_ending_node(graph, 0)
    elif strategy == "both_nodes":
        tree = traverse_graph_both_nodes(graph, 0)
    else:
        tree = traverse_graph_no_strategy(graph, 0)

    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        # append starting_node tag to the parent of the next node
        if tree[pos].label().startswith("start"):
            prev_pos = rev_positions[pos_i+1]
            tree[prev_pos].set_label(tree[prev_pos].label() + tree[pos].label())
            del tree[pos]
        # append ending_node tag to the parent of the current node
        elif tree[pos].label().startswith("end"):
            parent_pos = tree[pos].parent().treeposition()
            tree[parent_pos].set_label(tree[parent_pos].label() + tree[pos].label())
            del tree[pos]

    tree_str = tree.pformat()
    tree_str_flat = ' '.join(tree_str.split())

    return tree_str_flat


def convert_treebank(input_dir, output_dir, strategy):
    """
    Convert a treebank of graphs to phrase-structure trees.
    """

    for f in input_dir.iterdir():
        with open(f, "r") as json_file:
            docs = json.load(json_file)
            trees = ""
            for doc in docs["docs"]:
                for sent in doc["sents"]:
                    tree = get_string(sent["graph"], strategy)
                    trees += tree + "\n"
        with open(output_dir.joinpath(f.name).with_suffix(".txt"), "w+") as tree_files:
            tree_files.write(trees)


def main(
    input_dir: Path, 
    output_dir: Path, 
    strategy: str = typer.Option("", help="Strategy for encoding ellipsis, can be starting_node, ending_node or both_nodes."),
    ):
    
    convert_treebank(input_dir, output_dir, strategy)


if __name__ == "__main__":
    typer.run(main)