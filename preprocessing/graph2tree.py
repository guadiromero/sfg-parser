from pathlib import Path
import typer
import json
from nltk.tree import Tree


def convert_treebank(input_dir, output_dir, left_label, right_label):
    """
    """

    for f in input_dir.iterdir():
        with open(f, "r") as json_file:
            docs = json.load(json_file)
            for doc in docs["docs"]:
                print(doc["doc"])
                for sent in doc["sents"]:
                    tree = convert_sent(sent["graph"])
#                    print(tree)
  


def traverse_graph(graph, root):  
    """
    """

    print(graph[root]["children"])
    children = [int(c) for c in graph[root]["children"]]
    unellipsed_children = []
    for child in children:
        ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
        if root not in ellipsed_parents:
            if graph[child]["terminal"] == "yes":
                unellipsed_children.append(Tree(graph[child]["tag"], [graph[child]["text"]]))
            else:
                unellipsed_children.append(traverse_graph(graph, child))
           
    return Tree(graph[root]["tag"], unellipsed_children)


def convert_sent(graph):
    """
    """

    tree = traverse_graph(graph, 0)
    tree_str = tree.pformat()
    tree_str_flat = ' '.join(tree_str.split())

    return tree_str_flat


def main(
    input_dir: Path, 
    output_dir: Path,
    left_label: bool = typer.Option(False, help="Use left label strategy to encode ellipsis"),  
    right_label: bool = typer.Option(False, help="Use right label strategy to encode ellipsis"),
    ):
    
    convert_treebank(input_dir, output_dir, left_label, right_label)


if __name__ == "__main__":
    typer.run(main)