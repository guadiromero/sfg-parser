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


def convert(deps):
    """
    """

    sdp_deps = []

    for sent_i, sent in enumerate(deps):
        sdp_sent = ["#" + str(sent_i), ]
        # get predicates (tokens with outgoing edges) and enumerate them
        preds = []
        for token in sent:
            if token["dep_head"] not in preds:
                preds.append(token["dep_head"])
        args = {index+1:token_id for index, token_id in enumerate(preds)}
        # get sdp columns
        for token in sent:            
            id_ = str(int(token["token_id"]) + 1)
            form = token["token"]
            lemma = "_"
            pos = "_"
            top = "+" if token["dep_head"] == token["token_id"] else "-"
            pred = "+" if token["token_id"] in preds else "-"
            frame = "_"
            sdp_token = [id_, form, lemma, pos, top, pred, frame]
            for arg in args:
                if args[arg] == token["dep_head"]:
                    sdp_token.append(token["dep_label"])
                elif args[arg] in token["ellipsed_dep_heads"]:
                    for index, head in enumerate(token["ellipsed_dep_heads"]):
                        if args[arg] == head:
                            sdp_token.append(token["ellipsed_dep_labels"][index] + "ellipsis")
                else:
                    sdp_token.append("_")
            sdp_sent.append("\t".join(sdp_token))
        sdp_sent.append("\n")
        sdp_deps.append(sdp_sent)

    return sdp_deps


def main(
    input_dir: Path, 
    output_dir: Path,
    ):

    for f in input_dir.iterdir():
        basic_graphs = get_graphs(f)
        deps = extract_deps(basic_graphs)
        sdp_deps = convert(deps)
        with open(output_dir.joinpath(f.name).with_suffix(".txt"), "w+") as sdp_file:
            for sent in sdp_deps:
                for line in sent:
                    sdp_file.write(line)
                    sdp_file.write("\n")


if __name__ == "__main__":
    typer.run(main)