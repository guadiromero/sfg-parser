from pathlib import Path
import typer
import json
from nltk.tree import Tree


def get_ellipsis_tag(graph, target_node):
    """
    """

    counter = 0
    for node in graph:
        if node["tag"] == graph[target_node]["tag"]:
            if node["id"] != graph[target_node]["id"]:
                counter += 1
            else:
                ellipsis_tag = "-ellipsis" + node["tag"] + str(counter)
                return ellipsis_tag
  

def traverse_graph(graph, node, right_label):  
    """
    Convert a single graph to a phrase-structure tree.
    """

    children = [int(c) for c in graph[node]["children"]]
    unellipsed_children = []
    for child in children:
        ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
        # if the child is explicit
        if node not in ellipsed_parents:
            if graph[child]["terminal"] == "yes":
                unellipsed_children.append(Tree(graph[child]["tag"], [graph[child]["text"]]))
            else:
                unellipsed_children.append(traverse_graph(graph, child, right_label))
        # if the child is ellipsed
        else:
            if right_label:
#                unellipsed_children.append("ellipsis" + str(graph[child]["id"]) + graph[child]["tag"])
                ellipsis_tag = get_ellipsis_tag(graph, child)
                unellipsed_children.append(Tree(ellipsis_tag, [])) # CHECK
           
    tree = Tree(graph[node]["tag"], unellipsed_children)

    return tree


def get_string(graph, right_label):
    """
    Get string representation from a tree.
    """

    tree = traverse_graph(graph, 0, right_label)

    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        label = tree[pos] if type(tree[pos]) == str else tree[pos].label()
        if tree[pos].label().startswith("-ellipsis"):
            prev_pos = rev_positions[pos_i+1]
            tree[prev_pos].set_label(tree[prev_pos].label() + tree[pos].label())
            del tree[pos]

    tree_str = tree.pformat()
    tree_str_flat = ' '.join(tree_str.split())

    return tree_str_flat


def convert_treebank(input_dir, output_dir, right_label):
    """
    Convert a treebank of graphs to phrase-structure trees.
    """

    for f in input_dir.iterdir():
        with open(f, "r") as json_file:
            docs = json.load(json_file)
            trees = ""
            for doc in docs["docs"]:
                for sent in doc["sents"]:
                    tree = get_string(sent["graph"], right_label)
                    trees += tree + "\n"
        with open(output_dir.joinpath(f.name).with_suffix(".txt"), "w+") as tree_files:
            tree_files.write(trees)


def main(
    input_dir: Path, 
    output_dir: Path, 
    right_label: bool = typer.Option(False, help="Use right label strategy to encode ellipsis"),
    ):
    
    convert_treebank(input_dir, output_dir, right_label)


if __name__ == "__main__":
    typer.run(main)