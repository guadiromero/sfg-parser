# coding: utf8

from argparse import ArgumentParser
import json


def get_dep_spans(args):
    """
    Get dependency spans from a dependency parse in JSON spaCy training format.

    :return dep_spans: dict, where each key is a token index and each value is a dictionary
    containing annotations and the dependency span that this token is head of
    :return root: int, index of the token that is the root of the dependency tree
    """

    with open(args.input_file, "r") as f:
        input_file = json.load(f)

    for doc in input_file:
        for par in doc["paragraphs"]:
            for sent in par["sentences"]:
                # get dependency spans
                dep_spans = {tok["id"]:{"orth":tok["orth"], "tag":tok["tag"], "head":tok["head"], "dep":tok["dep"], "span":[tok["id"],]} for tok in sent["tokens"]}
                for tok in sent["tokens"]:
                    if tok["head"] == 0:
                        root = tok["id"]
                    else:
                        abs_head = tok["head"] + tok["id"]
                        dep_spans[abs_head]["span"].append(tok["id"])
                # sort indexes in the span
                for head in dep_spans:
                    dep_spans[head]["span"] = sorted(dep_spans[head]["span"])

    return dep_spans, root


def build_ctree(dep_spans, root):
    """
    Build a constituency tree from the dependency spans, using an iterative Breadth-First Search algorithm.

    :param dep_spans: dict, where each key is a token index and each value is a dictionary
    containing annotations and the dependency span that this token is head of
    :param root: int, index of the token that is the root of the dependency tree
    :return ctree: dict, representation of the constituency tree, where each key is the index of a node
    and each value is a dictionary with annotations and the indexes of its direct children
    """

    UD_DEPS = [
        "acl", 
        "advcl", 
        "advmod",
        "amod",
        "appos",
        "aux",
        "case",
        "cc",
        "ccomp",
        "clf",
        "compound",
        "conj",
        "cop",
        "csubj"
        "dep",
        "det",
        "discourse",
        "dislocated",
        "expl",
        "fixed",
        "flat",
        "goeswith",
        "iobj",
        "list",
        "mark",
        "nmod",
        "nsubj",
        "nummod",
        "obj",
        "obl",
        "orphan",
        "parataxis",
        "pobj", # english tag
        "prep", # english tag
        "punct",
        "reparandum",
        "root",
        "vocative",
        "xcomp",
        ]

    TAG_MAP = {
        "C": {"head_tag": ["VERB",], "head_dep": ["root", "parataxis"]},
        "VP": {"head_tag": ["VERB",], "head_dep": UD_DEPS},
        "NP": {"head_tag": ["NOUN",], "head_dep": UD_DEPS},
        "PP": {"head_tag": ["ADP",], "head_dep": UD_DEPS},
    }

    queue = [0,]
    ctree = {}
    node_heads = {0:root,}
    visited_heads = []

    # build the tree iteratively    
    while len(queue) > 0:
       # pop the first element in the queue
        node = queue.pop(0)
        ctree[node] = {}
        # get children heads of the node
        children_heads = dep_spans[node_heads[node]]["span"]
        # add the current node to the ctree
        if len(children_heads) == 1 or node_heads[node] in visited_heads:
        # if it is a terminal or if this head has already been visited
            ctree[node] = dep_spans[node_heads[node]]
            ctree[node]["is_terminal"] = "yes"
        else:
        # if it is a non-terminal and the head has not been visited yet
            ctree[node]["is_terminal"] = "no"
            ctree[node]["tag"] = "TAG"
            for tag in TAG_MAP:
                if dep_spans[node_heads[node]]["tag"] in TAG_MAP[tag]["head_tag"] and dep_spans[node_heads[node]]["dep"] in TAG_MAP[tag]["head_dep"]:                
                    ctree[node]["tag"] = tag
                    break
            children = [child for child in range(len(node_heads), len(node_heads)+len(children_heads))]
            ctree[node]["children"] = children
            # keep track of children heads
            for child, child_head in zip(children, children_heads):
                node_heads[child] = child_head
            # push the direct children of the current node to the queue, from left to right
            for child in children:         
                queue.append(child)
            visited_heads.append(node_heads[node])

    return ctree


def main():

    parser = ArgumentParser(
        description="Convert raw text in a JSON data file to str")
    parser.add_argument(
        "-input-file", "--input-file", help="Path to the input file containing the data in JSON format")
    parser.add_argument(
        "-output-file", "--output-file", help="Path to the output file")
    args = parser.parse_args()

    dep_spans, root = get_dep_spans(args)
    ctree = build_ctree(dep_spans, root)
    for node in ctree:
        print(node, ctree[node])
        print('\n')


if __name__ == "__main__":
    main()