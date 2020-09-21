from pathlib import Path
import typer
import json
from eval_graph import get_graphs
from tag_ranks import TAG_RANKS


def extract_deps(graphs):
    """
    """

    deps = []

    for graph in graphs:
        # enrich graphs
        add_terminal_ids(graph)
        add_const_heads(graph)
        add_deps(graph)
        # extract dependencies
        dep = []
        for node in graph:
            if node["terminal"] == "yes":
                token_id = node["terminal_id"]
                token = node["text"]
                dep_head = node["dep_head"]
                dep_label = node["dep_label"]
                ellipsed_dep_heads = node["ellipsed_dep_heads"]
                ellipsed_dep_labels = node["ellipsed_dep_labels"]
                dep.append({"token_id": token_id, "token": token, "dep_head": dep_head, "dep_label": dep_label, "ellipsed_dep_heads": ellipsed_dep_heads, "ellipsed_dep_labels": ellipsed_dep_labels})
        deps.append(dep)

    return deps


def add_terminal_ids(graph):
    """
    """

    terminal_counter = 0
    for node in graph:
        if node["terminal"] == "yes":
            node["terminal_id"] = terminal_counter
            terminal_counter += 1
        else:
            node["terminal_id"] = None


def add_const_heads(graph):
    """
    """

    for node in graph:
        const_head = find_const_head(graph, node)
        node["const_head"] = const_head


def find_const_head(graph, node):
    """
    """

    if node["terminal"] == "yes":
        return node["terminal_id"]
    else:
        children = [graph[child] for child in node["children"]]
        const_head = const_head_rules(children)
        return find_const_head(graph, const_head)


def const_head_rules(children):
    """
    """

    ranks = []

    for index, child in enumerate(children):
        if child["tag"] in TAG_RANKS:
            rank = TAG_RANKS[child["tag"]]
        else:
            rank = 10 # assign a random low rank
        ranks.append(rank)

    # return the first child with the highest rank    
    highest_rank = min(ranks)
    for rank, child in zip(ranks, children):
        if rank == highest_rank:
            return child     


def add_deps(graph):   
    """
    """

    for node in graph:
        if node["terminal"] == "no":
            dep_head = None
            dep_label = None
            ellipsed_dep_heads = []
            ellipsed_dep_labels = []
        elif node["terminal"] == "yes":
            dep_head, dep_label = find_dep_head(graph, node)
            ellipsed_dep_heads, ellipsed_dep_labels = find_ellipsed_dep_heads(graph, node)
        node["dep_head"] = dep_head
        node["dep_label"] = dep_label
        node["ellipsed_dep_heads"] = ellipsed_dep_heads
        node["ellipsed_dep_labels"] = ellipsed_dep_labels


def find_dep_head(graph, node):
    """
    """

    parent = graph[node["parent"]]
    if parent["const_head"] != node["terminal_id"]:
        return parent["const_head"], parent["tag"]
    else:
        # exception for the root
        if node["terminal_id"] == graph[0]["const_head"]:
            return parent["const_head"], "CLX"
        else:
            return find_dep_head(graph, parent)


def find_ellipsed_dep_heads(graph, node):
    """
    """

    ellipsed_parents = [graph[ellipsed_parent] for ellipsed_parent in node["ellipsed_parents"]]
    ellipsed_dep_heads = []
    ellipsed_dep_labels = []

    for ellipsed_parent in ellipsed_parents:
        ellipsed_dep_head, ellipsed_dep_label = find_dep_head(graph, ellipsed_parent)
        ellipsed_dep_heads.append(ellipsed_dep_head)
        ellipsed_dep_labels.append(ellipsed_dep_label)

    return ellipsed_dep_heads, ellipsed_dep_labels


def edge_is_correct(gold_node, predicted_node):
    """
    """

    if gold_node["dep_head"] == predicted_node["dep_head"]:
        return True
    else:
        return False


def label_is_correct(gold_node, predicted_node):
    """
    """

    if gold_node["dep_label"] == predicted_node["dep_label"]:
        return True
    else:
        return False


def ellipsed_edges_are_correct(gold_node, predicted_node):
    """
    """

    if set(gold_node["ellipsed_dep_heads"]) == set(predicted_node["ellipsed_dep_heads"]):
        return True
    else:
        return False


def ellipsed_labels_are_correct(gold_node, predicted_node):
    """
    """

    gold_tuples = set()
    for gold_head, gold_label in zip(gold_node["ellipsed_dep_heads"], gold_node["ellipsed_dep_labels"]):
        gold_tuples.add((gold_head, gold_label))

    predicted_tuples = set()
    for predicted_head, predicted_label in zip(predicted_node["ellipsed_dep_heads"], predicted_node["ellipsed_dep_labels"]):
        predicted_tuples.add((predicted_head, predicted_label))

    if gold_tuples == predicted_tuples:
        return True
    else:
        return False


def score(gold_deps, predicted_deps, ellipsis_only=False, exclude_ellipsis=False):
    """
    """

    if ellipsis_only:
        print("Results for ellipsed nodes only")
    elif exclude_ellipsis:
        print("Results for non-ellipsed nodes only")
    else:
        print("Results for all nodes")

    correct_unlabeled = 0
    correct_labeled = 0
    total_gold_nodes = 0
    total_predicted_nodes = 0

    for gold_dep, predicted_dep in zip(gold_deps, predicted_deps):
        for gold_node, predicted_node in zip(gold_dep, predicted_dep):
            # count total of nodes
            if ellipsis_only:
                if len(gold_node["ellipsed_dep_heads"]) > 0:
                    total_gold_nodes += 1
                if len(predicted_node["ellipsed_dep_heads"]) > 0:
                    total_predicted_nodes += 1
            else:
                total_gold_nodes += 1
                total_predicted_nodes += 1
            # count total of correct nodes
            if ellipsis_only:
                if len(gold_node["ellipsed_dep_heads"]) > 0:
                    if ellipsed_edges_are_correct(gold_node, predicted_node):
                        correct_unlabeled += 1
                    if ellipsed_labels_are_correct(gold_node, predicted_node):
                        correct_labeled += 1
#                    else:
#                        print("\n#############\n")
#                        print("Wrong node: " + str(gold_node["token_id"]) + "\n")
#                        for node in gold_dep:
#                            print(node)
#                       print("\n")
#                        for node in predicted_dep:
#                            print(node)
            elif exclude_ellipsis:
                if edge_is_correct(gold_node, predicted_node):
                    correct_unlabeled += 1
                    if label_is_correct(gold_node, predicted_node):
                        correct_labeled += 1
            else:
                if edge_is_correct(gold_node, predicted_node) and ellipsed_edges_are_correct(gold_node, predicted_node):
                    correct_unlabeled += 1
                    if label_is_correct(gold_node, predicted_node) and ellipsed_labels_are_correct(gold_node, predicted_node):
                        correct_labeled += 1 

#    print(total_gold_nodes)
#    print(total_predicted_nodes) 
#    print(correct_unlabeled)
#    print(correct_labeled)              

    unlabeled_p = correct_unlabeled / total_predicted_nodes
    unlabeled_r = correct_unlabeled / total_gold_nodes
    unlabeled_f = 2 * ((unlabeled_p * unlabeled_r) / (unlabeled_p + unlabeled_r))
    labeled_p = correct_labeled / total_predicted_nodes
    labeled_r = correct_labeled / total_gold_nodes
    labeled_f = 2 * ((labeled_p * labeled_r) / (labeled_p + labeled_r))

    print("Unlabeled Precision: " + str(round(unlabeled_p * 100, 2)))
    print("Unlabeled Recall: " + str(round(unlabeled_r * 100, 2)))
    print("Unlabeled F1: " + str(round(unlabeled_f * 100, 2)))
    print("Labeled Precision: " + str(round(labeled_p * 100, 2)))
    print("Labeled Recall: " + str(round(labeled_r * 100, 2)))
    print("Labeled F1: " + str(round(labeled_f * 100, 2)))
    print("\n")


def main(
    gold_file: Path, 
    predicted_file: Path, 
    ):

    # TEST
    gold_graph = [
        {"id": 0, "children": [1, 9], "parent": None, "ellipsed_parents": [], "terminal": "no", "tag": "CLX", "text": ""},
        {"id": 1, "children": [2, 3, 4], "parent": 0, "ellipsed_parents": [], "terminal": "no", "tag": "CL", "text": ""},
        {"id": 2, "children": [], "parent": 1, "ellipsed_parents": [9], "terminal": "yes", "tag": "NG", "text": "he"},
        {"id": 3, "children": [], "parent": 1, "ellipsed_parents": [], "terminal": "yes", "tag": "VG", "text": "ate"},
        {"id": 4, "children": [5, 6], "parent": 1, "ellipsed_parents": [], "terminal": "no", "tag": "NG", "text": ""},
        {"id": 5, "children": [], "parent": 4, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "pizza"},
        {"id": 6, "children": [7, 8], "parent": 4, "ellipsed_parents": [], "terminal": "no", "tag": "PP", "text": ""},
        {"id": 7, "children": [], "parent": 6, "ellipsed_parents": [], "terminal": "yes", "tag": "PREP", "text": "with"},
        {"id": 8, "children": [], "parent": 6, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "anchovies"},
        {"id": 9, "children": [10, 2, 11, 12], "parent": 0, "ellipsed_parents": [], "terminal": "no", "tag": "CL", "text": ""},
        {"id": 10, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "CC", "text": "and"},
        {"id": 11, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "VG", "text": "drank"},
        {"id": 12, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "beer"},
    ]

    predicted_graph = [
        {"id": 0, "children": [1, 9], "parent": None, "ellipsed_parents": [], "terminal": "no", "tag": "CLX", "text": ""},
        {"id": 1, "children": [2, 3, 4], "parent": 0, "ellipsed_parents": [], "terminal": "no", "tag": "CL", "text": ""},
        {"id": 2, "children": [], "parent": 1, "ellipsed_parents": [9], "terminal": "yes", "tag": "NG", "text": "he"},
        {"id": 3, "children": [], "parent": 1, "ellipsed_parents": [], "terminal": "yes", "tag": "VG", "text": "ate"},
        {"id": 4, "children": [5, 6], "parent": 1, "ellipsed_parents": [], "terminal": "no", "tag": "NG", "text": ""},
        {"id": 5, "children": [], "parent": 4, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "pizza"},
        {"id": 6, "children": [7, 8], "parent": 4, "ellipsed_parents": [], "terminal": "no", "tag": "PP", "text": ""},
        {"id": 7, "children": [], "parent": 6, "ellipsed_parents": [], "terminal": "yes", "tag": "PREP", "text": "with"},
        {"id": 8, "children": [], "parent": 6, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "anchovies"},
        {"id": 9, "children": [10, 2, 11, 12], "parent": 0, "ellipsed_parents": [], "terminal": "no", "tag": "CL", "text": ""},
        {"id": 10, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "CC", "text": "and"},
        {"id": 11, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "VG", "text": "drank"},
        {"id": 12, "children": [], "parent": 9, "ellipsed_parents": [], "terminal": "yes", "tag": "NG", "text": "beer"},
    ]

#    gold_graphs = [gold_graph,] # TEST
#    predicted_graphs = [predicted_graph,] # TEST

    gold_graphs = get_graphs(gold_file)
    gold_deps = extract_deps(gold_graphs)

    predicted_graphs = get_graphs(predicted_file)
    predicted_deps = extract_deps(predicted_graphs)

    score(gold_deps, predicted_deps)
    score(gold_deps, predicted_deps, ellipsis_only=True)
    score(gold_deps, predicted_deps, exclude_ellipsis=True)


if __name__ == "__main__":
    typer.run(main)