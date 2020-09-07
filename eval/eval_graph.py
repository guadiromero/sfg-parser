from pathlib import Path
import typer
import json


def count_nodes(graphs):
    """
    Count number of nodes.
    """

    counter = 0
    for graph in graphs:
        counter += len(graph)

    return counter


def count_nodes_per_label(graphs):
    """
    Count number of nodes per label.
    """

    counter = {}
    for graph in graphs:
        for node in graph:
            label = node["tag"]
            if label not in counter:
                counter[label] = 1
            else:
                counter[label] += 1

    return counter


def get_parents(graph, node):
    """
    Get unellipsed and ellipsed parents for a node.
    """

    parent = graph[node]["parent"]
    ellipsed_parents = graph[node]["ellipsed_parents"]

    return parent, ellipsed_parents


def get_position(graph, parent, node):
    """
    Get position of a node among siblings.
    """

    for position, child in enumerate(graph[parent]["children"]):
        if child == node:
            return position


def edge_is_correct(gold_graph, predicted_graph, node):
    """
    Check that a node has the correct parents.
    When ellipsed, check that the node is inserted in the right position.
    """

    # check if any of the predicted unellipsed and ellipsed parents are incorrect
    predicted_parent, predicted_parents_ellipsed = get_parents(predicted_graph, node)
    gold_parent, gold_parents_ellipsed = get_parents(gold_graph, node)

    if set([predicted_parent,] + predicted_parents_ellipsed) != set([gold_parent,] + gold_parents_ellipsed):
        return False

    # when ellipsed, check if the node is inserted in a wrong position
    else:
        for parent in predicted_parents_ellipsed:
            predicted_position = get_position(predicted_graph, parent, node)
            gold_position = get_position(gold_graph, parent, node)     
            if predicted_position != gold_position:
                return False

    return True


def label_is_correct(gold_graph, predicted_graph, node):
    """
    Check that a node has the correct label.
    """

    predicted_label = predicted_graph[node]["tag"]
    gold_label = gold_graph[node]["tag"]

    if predicted_label == gold_label:
        return True
    else:
        return False


def get_graphs(json_file):
    """
    Extract graphs from a json file.
    """

    graphs = []

    with json_file.open(mode="r") as f:
        docs = json.load(f)

    for doc in docs["docs"]:
        for sent in doc["sents"]:
            graph = sent["graph"]
            graphs.append(graph)

    return graphs


def score(gold_graphs, predicted_graphs, exclude_ellipsis, ellipsis_only):
    """
    Evaluate graphs.
    """

    gold_nodes = count_nodes(gold_graphs)
    predicted_nodes = count_nodes(predicted_graphs)
    correct_unlabeled = 0
    correct_labeled = 0
    correct_per_label = {}
    gold_per_label = count_nodes_per_label(gold_graphs)
    predicted_per_label = count_nodes_per_label(predicted_graphs)

    for gold_graph, predicted_graph in zip(gold_graphs, predicted_graphs):
        # exclude graphs that contain/do not contain ellipsis if indicated as an argument
        if ellipsis_only:
            if all(len(node["ellipsis_tag"]) == 0 for node in gold_graph):
                break                          
        elif exclude_ellipsis:
            if any(len(node["ellipsis_tag"]) != 0 for node in gold_graph):
                break
        # count number of correct nodes
        for node in range(len(gold_graph)):
            label = gold_graph[node]["tag"]
            if label not in correct_per_label:
                correct_per_label[label] = {"correct_labeled": 0, "correct_unlabeled": 0}
            if edge_is_correct(gold_graph, predicted_graph, node):
                correct_unlabeled += 1
                correct_per_label[label]["correct_unlabeled"] += 1
                if label_is_correct(gold_graph, predicted_graph, node):
                    correct_labeled += 1
                    correct_per_label[label]["correct_labeled"] += 1

    # I WILL MAKE THIS PART MORE READABLE LATER :D
    scores = {}
    scores["unlabeled_p"] = correct_unlabeled / predicted_nodes
    scores["unlabeled_r"] = correct_unlabeled / gold_nodes
    if scores["unlabeled_p"] + scores["unlabeled_r"] != 0:
        scores["unlabeled_f"] = 2 * ((scores["unlabeled_p"] * scores["unlabeled_r"]) / (scores["unlabeled_p"] + scores["unlabeled_r"]))
    scores["labeled_p"] = correct_labeled / predicted_nodes
    scores["labeled_r"] = correct_labeled / gold_nodes
    if scores["labeled_p"] + scores["labeled_r"] != 0:
        scores["labeled_f"] = 2 * ((scores["labeled_p"] * scores["labeled_r"]) / (scores["labeled_p"] + scores["labeled_r"]))
    scores["per_label"] = {}
    for label in correct_per_label:
        scores["per_label"][label] = {}
        scores["per_label"][label]["unlabeled_p"] = correct_per_label[label]["correct_unlabeled"] / predicted_per_label[label]
        scores["per_label"][label]["unlabeled_r"] = correct_per_label[label]["correct_unlabeled"] / gold_per_label[label]
        if scores["per_label"][label]["unlabeled_p"] + scores["per_label"][label]["unlabeled_r"] != 0:
            scores["per_label"][label]["unlabeled_f"] = 2 * ((scores["per_label"][label]["unlabeled_p"] * scores["per_label"][label]["unlabeled_r"]) / (scores["per_label"][label]["unlabeled_p"] + scores["per_label"][label]["unlabeled_r"]))
        scores["per_label"][label]["labeled_p"] = correct_per_label[label]["correct_labeled"] / predicted_per_label[label]
        scores["per_label"][label]["labeled_r"] = correct_per_label[label]["correct_labeled"] / gold_per_label[label]
        if scores["per_label"][label]["labeled_p"] + scores["per_label"][label]["labeled_r"] != 0:
            scores["per_label"][label]["labeled_f"] = 2 * ((scores["per_label"][label]["labeled_p"] * scores["per_label"][label]["labeled_r"]) / (scores["per_label"][label]["labeled_p"] + scores["per_label"][label]["labeled_r"]))

    return scores


def main(
    gold_file: Path, 
    predicted_file: Path, 
    exclude_ellipsis: bool = typer.Option(False, help="Whether to exclude graphs with ellipsed nodes"),
    ellipsis_only: bool = typer.Option(False, help="Whether to only include graphs with ellipsed nodes"),
    ):

    gold_graphs = get_graphs(gold_file)
    predicted_graphs = get_graphs(predicted_file)

    scores = score(gold_graphs, predicted_graphs, exclude_ellipsis, ellipsis_only)
    print(scores)


if __name__ == "__main__":
    typer.run(main)