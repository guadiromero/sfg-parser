from pathlib import Path
import typer
import json
from tag_ranks import TAG_RANKS


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


def extract_deps(graphs):
    """
    Extract dependencies from a graph.
    """

    deps = []

    for graph in graphs:
        # enrich graphs
        add_terminal_ids(graph)
        add_const_heads(graph)
        add_deps(graph)
        add_ellipsed_deps(graph)
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
                graph_label = node["tag"]
                dep.append({"token_id": token_id, "token": token, "dep_head": dep_head, "dep_label": dep_label, "ellipsed_dep_heads": ellipsed_dep_heads, "ellipsed_dep_labels": ellipsed_dep_labels, "graph_label": graph_label})
        deps.append(dep)

    return deps


def add_terminal_ids(graph):
    """
    Enumerate terminals in a graph.
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
    Add constituent heads to a graph.
    """

    for node in graph:
        const_head = find_const_head(graph, node)
        node["const_head"] = const_head


def find_const_head(graph, node):
    """
    Choose a terminal to be the head of a constituent.
    """

    if node["terminal"] == "yes":
        return node["terminal_id"]
    else:
        children = [graph[child] for child in node["children"] if node["id"] not in graph[child]["ellipsed_parents"]]
        const_head = const_head_rules(children)
        return find_const_head(graph, const_head)


def const_head_rules(children):
    """
    Rules for choosing the head of a constituent.
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
    Add dependencies for explicit edges in a graph.
    """

    for node in graph:
        if node["terminal"] == "no":
            dep_head = None
            dep_label = None
        elif node["terminal"] == "yes":
            dep_head, dep_label = find_dep_head(graph, graph[node["parent"]], node["terminal_id"])
        node["dep_head"] = dep_head
        node["dep_label"] = dep_label


def add_ellipsed_deps(graph):   
    """
    Add dependencies for ellipsed edges in a graph.
    """

    terminal_ids = {}
    for node in graph:
        node["ellipsed_dep_heads"] = []
        node["ellipsed_dep_labels"] = []
        if node["terminal"] == "yes":
            terminal_ids[node["terminal_id"]] = node["id"]

    for node in graph:
        ellipsed_dep_heads = []
        ellipsed_dep_labels = []
        for ellipsed_parent in node["ellipsed_parents"]:
            ellipsed_dep_head = graph[ellipsed_parent]["const_head"]
            ellipsed_dep_heads.append(ellipsed_dep_head)
            ellipsed_dep_label = graph[ellipsed_parent]["tag"]
            ellipsed_dep_labels.append(ellipsed_dep_label)
        const_head = node["const_head"]
        ellipsed_node = terminal_ids[const_head]
        graph[ellipsed_node]["ellipsed_dep_heads"].extend(ellipsed_dep_heads)
        graph[ellipsed_node]["ellipsed_dep_labels"].extend(ellipsed_dep_labels)      


def find_dep_head(graph, parent, terminal_id):
    """
    Find the dependency head for a terminal node.
    """

    if parent["const_head"] != terminal_id:
        return parent["const_head"], parent["tag"]
    else:
        # exception for the root
        if terminal_id == graph[0]["const_head"]:
            return parent["const_head"], "CLX"
        else:
            return find_dep_head(graph, graph[parent["parent"]], terminal_id)


def edge_is_correct(gold_node, predicted_node):
    """
    Check whether a node points to the correct head.
    """

    if gold_node["dep_head"] == predicted_node["dep_head"]:
        return True
    else:
        return False


def label_is_correct(gold_node, predicted_node):
    """
    Check whether a node points to the correct head with the correct label.
    """

    if gold_node["dep_label"] == predicted_node["dep_label"]:
        return True
    else:
        return False


def ellipsed_edges_are_correct(gold_node, predicted_node):
    """
    Check whether a node points to the correct ellipsed heads.
    """

    if set(gold_node["ellipsed_dep_heads"]) == set(predicted_node["ellipsed_dep_heads"]):
        return True
    else:
        return False


def ellipsed_labels_are_correct(gold_node, predicted_node):
    """
    Check whether a node points to the correct ellipsed heads with the correct labels.
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


def is_punct(node):
    """
    Check if a node is punctuation.
    """

    if node["graph_label"] in [",", ":", "``", '"', "-LRB-", "-RRB-"]:
        return True
    else:
        return False


def sdp2deps(sdp_file):
    """
    """

    with open(sdp_file, "r") as f:
        lines = f.readlines()

    deps = []
    preds = []

    dep_sent = []
    pred_sent = []
    for line in lines:
        if line.startswith("#"):
            continue
        if line == "\n":
            deps.append(dep_sent)
            dep_sent = []            
            pred_dict = {}
            for index, pred in enumerate(pred_sent):
                pred_dict[index] = pred
            preds.append(pred_dict)
            pred_sent = []
            break
        else:
            splitted_line = line.strip("\n").split("\t")
            token_id = int(splitted_line[0]) - 1
            token = splitted_line[1]
            graph_label = "_"
            args = splitted_line[7:]
            ellipsed_dep_heads = []
            ellipsed_dep_labels = []
            if splitted_line[5] == "+":
                pred_sent.append(token_id)
            for index, arg in enumerate(args):
                if arg == "_":
                    continue
                elif "ellipsis" in arg:
                    ellipsed_dep_heads.append(index)
                    ellipsed_dep_labels.append(arg.split("ellipsis")[0])
                else: 
                    dep_head = index
                    dep_label = arg.split("ellipsis")[0]                  
            dep = {"token_id": token_id, "token": token, "dep_head": dep_head, "dep_label": dep_label, "ellipsed_dep_heads": ellipsed_dep_heads, "ellipsed_dep_labels": ellipsed_dep_labels, "graph_label": graph_label}
            dep_sent.append(dep)

    # replace args with dependency heads
    for dep_sent, pred_dict in zip(deps, preds):
        for token in dep_sent:
            token["dep_head"] = pred_dict[token["dep_head"]]
            for index, ellipsed_dep_head in enumerate(token["ellipsed_dep_heads"]):
                token["ellipsed_dep_heads"][index] = pred_dict[ellipsed_dep_head]

    return deps


def score(gold_deps, predicted_deps, ellipsis_only=False, exclude_ellipsis=False):
    """
    Score graphs.
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
            # skip punctuation
            if is_punct(gold_node):
                continue
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
                    # inspect wrong nodes
#                    else:
#                        print("\n#############\n")
#                        print("Wrong node: " + str(gold_node["token_id"]) + "\n")
#                        for node in gold_dep:
#                            print(node)
#                        print("\n")
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

    gold_graphs = get_graphs(gold_file)
    gold_deps = extract_deps(gold_graphs)

    if predicted_file.suffix == ".json":
        predicted_graphs = get_graphs(predicted_file)
        predicted_deps = extract_deps(predicted_graphs)
    else:
        predicted_deps = sdp2deps(predicted_file)
        # DEBUG
#        for gold_dep, predicted_dep in zip(gold_deps, predicted_deps):
#            for index, token in enumerate(gold_dep):
#                print(token)
#                print(predicted_dep[index])
#                print("\n")
#            print("\n")

    score(gold_deps, predicted_deps)
    score(gold_deps, predicted_deps, ellipsis_only=True)
    score(gold_deps, predicted_deps, exclude_ellipsis=True)


if __name__ == "__main__":
    typer.run(main)