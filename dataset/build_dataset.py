from pathlib import Path
import typer
import xml.etree.ElementTree as ET
import json
from tag_maps import TAGS_SFG as tag_map
from collections import defaultdict
from itertools import chain, combinations


def get_function_label(node):
    """
    Get function label of a node.
    """

    features = [feat.get("value") for feat in node[1]]

    if "functionLabels.SBJ" in features:
        function_label = "subject"
    elif not set(["label.VB", "label.VBD", "label.VBG", "label.VBN", "label.VBP", "label.VBZ", "label.MD", "label.TO"]).isdisjoint(set(features)):
        function_label = "auxiliary"
    elif not set(["label.ADVP", "label.RB"]).isdisjoint(set(features)):
        function_label = "adjunct"
    elif "label.VP" in features:
        function_label = "process"
    elif not set(["label.PP", "label.IN"]).isdisjoint(set(features)):
        function_label = "preposition"
    elif not set(["label.WHADVP", "label.WHNP", "label.WHPP", "label.WRB", "label.WDT", "label.WP"]).isdisjoint(set(features)):
        function_label = "relative_pronoun"
    elif not set(["label.NP", "label.PRP", "label.NN", "label.NNS", "label.NNP", "label.NNPS", "label.NX", "label.JJ"]).isdisjoint(set(features)) and "functionLabels.SBJ" not in features:
        function_label = "object"
    else:
        function_label = "other"
#        function_label = node[1][0].get("value") # inspect labels of ellipsis in the "other" category

    return function_label


def count_ellipsis_types(graph):
    """
    Count how many ellipsis of each type occur in a graph.
    """

    ellipsis_types = defaultdict(int)

    for node in graph:
        if node["tag"] == "CL":
            auxiliary = node["ellipsis_types"]["auxiliary"] if node["ellipsis_types"]["auxiliary"] else 0
            adjunct = node["ellipsis_types"]["adjunct"] if node["ellipsis_types"]["adjunct"] else 0
            # count adjunct + (auxiliary) + (subject) as 1 ellipsis
            while adjunct > 0:
                adjunct -= 1
                if node["ellipsis_types"]["subject"]:
                    node["ellipsis_types"]["subject"] -= 1
                if node["ellipsis_types"]["auxiliary"]:
                    node["ellipsis_types"]["auxiliary"] -= 1
            # count auxiliary + (subject) as 1 ellipsis
            while auxiliary > 0:
                auxiliary -= 1
                if node["ellipsis_types"]["subject"]:
                    node["ellipsis_types"]["subject"] -= 1
            for type_ in node["ellipsis_types"]:
                ellipsis_types[type_] += node["ellipsis_types"][type_]

    return ellipsis_types


def select_spans(spans, target_terminals):
    """
    Select the shortest combination of spans for the target terminals.
    """

    def sliceable(xs):
        """
        Return a sliceable version of the iterable xs.
        """
        try:
            xs[:0]
            return xs
        except TypeError:
            return tuple(xs)

    def partition(iterable):
        s = sliceable(iterable)
        n = len(s)
        b, mid, e = [0], list(range(1, n)), [n]
        getslice = s.__getitem__
        splits = (d for i in range(n) for d in combinations(mid, i))
        return [[s[sl] for sl in map(slice, chain(b, d), chain(d, e))]
                for d in splits]

    def filter(splits, spans):
        """
        Select the splits that are possible.
        """
        possible_splits = []
        for split in splits:
            if all([span in spans for span in split]):
                possible_splits.append(split)   
        return possible_splits     

    if len(target_terminals) < 10: # if the target is too long, just skip the sentence as it will take too long to compute
        splits = partition(target_terminals)
        possible_splits = filter(splits, spans)
        # choose shortest split
        shortest_len = min([len(split) for split in possible_splits])
        for split in possible_splits:
            if len(split) == shortest_len:
                shortest_split = split
        if shortest_len < 3: # also introduce a limit of ellipsed nodes, as the berkeley parser is not able to handle such long tags
            return shortest_split

    return None


def xml2graph(root, text, tag_map):
    """
    Traverse a xml tree with first-depth search and convert it to a directed acyclic graph.
    :param node: xml.etree.ElementTree.Element object, representing the syntactic tree of the sentence (where the root is a Clause Complex)
    :param text: str, text for the whole document
    :param tag_map: dict, tag map
    :return graph: str, linearized tree, following the PTB format
    :return string: str, text for the sentence
    :return ellipsis: bool, whether there is ellipsis in the sentence or not
    """

    stack = [] # list of (node, parent) tuples
    graph = [] # list of dictionaries representing nodes
    tracking_list = [] # list of terminal spans
    terminals = [] # list of the sentence tokens
    parent_clause = None # keep track of the parent clause
    ellipsed_punct = [] # ellipsed punctuation that constitutes a node of its own

    # push the root of the tree to the stack
    stack.append((root, 0))
    
    while len(stack) > 0:
       # pop the last element in the stack
        last = stack.pop()
        node = last[0]
        parent = last[1]
        if node.tag == "Constituent":
            # get basic information from the node
            node_type = node.get("type")     
            function_label = get_function_label(node)      
            if node_type in ["Word", "Punctuation"]:
                terminal = "yes"
                tag = node[1][0].get('value')[6:] # pos
                node_text = text[int(node[0].get('start')):int(node[0].get('end'))]
            if node_type not in ["Word", "Punctuation", "Ellipsis"]:
                terminal = "no"
                tag = tag_map[node_type]
                node_text = ""
            # check if the node is ellipsed, i.e., all its terminals are ellipsed
            ellipsed_node = True
            for subnode in node.iter():
                if subnode.get("type") in ["Word", "Punctuation"]:
                    ellipsed_node = False                     
            if ellipsed_node == True:
                # add node span to its parent's children list
                span = [subnode[0].get("idref") for subnode in node.iter() if subnode.get("type") == "Ellipsis"]
                # search for original node if there is ellipsis of ellipsis
                for i, s in enumerate(span):
                    attempts = 0
                    while "." in s and attempts < 10:
                        for subnode in root.iter():
                            if subnode.get("id") == s:
                                if subnode.get("type") in ["Word", "Punctuation"]:
                                    s = subnode.get("id")
                                elif subnode.get("type") == "Ellipsis":
                                    s = subnode[0].get("idref") # if subnode.get("idref") != None else s
                                break
                        span[i] = s  
                        attempts += 1                
                graph[parent]["children"].append(span)
            if ellipsed_node == False:
                # create a graph node
                graph_id = len(tracking_list)
                # keep track of the parent clause
                if node.get("type") == "Clause":
                    parent_clause = graph_id
                    ellipsis_types = defaultdict(int)
                else: 
                    ellipsis_types = None
                graph_node = {"id": graph_id, "children": [], "parent": parent, "ellipsed_parents": [], "terminal": terminal, "tag": tag, "text": node_text, "function_label": function_label, "parent_clause": parent_clause, "ellipsis_types": ellipsis_types}
                # add node span to the tracking list
                span = [subnode.get("id") for subnode in node.iter() if subnode.get("type") in ["Word", "Punctuation"]]
                tracking_list.append(span)
                # add node to the graph
                graph.append(graph_node)
                # add node to its parent's children list
                if graph_id != 0:
                    graph[parent]["children"].append(graph_id)
        if ellipsed_node == False:
            # push the direct children of the current node to the stack, from right to left (even if it's not a constituent)
            for child in reversed(list(node)):       
                stack.append((child, graph_id))

    ellipsis = "no"
    bert_len = 0
    for node in graph:
        # finish constructing the graph
        for child_id, child in enumerate(node["children"]):
            if type(child) == list:
                ellipsis = "yes" # record that there is at least one ellipsed node in the graph
                no_match = True
                for span_id, span in enumerate(tracking_list):
                    if set(child) == set(span):
                        # replace ellipsed node span for node id
                        node["children"][child_id] = span_id  
                        # add parent to the node's ellipsed parents list
                        graph[span_id]["ellipsed_parents"].append(node["id"]) 
                        no_match = False
                        break
                if no_match == True:
                    # if no nodes coincide with the ellipsed span, get the shortest combination of spans
                    selected_spans = select_spans(tracking_list, child) 
                    if selected_spans == None:
                        return None, None, None, None
                    selected_spans_ids = []  
                    for selected_span in selected_spans:
                        found = "no"
                        for span_id, span in enumerate(tracking_list):
                            if set(span) == set(selected_span):
                                selected_spans_ids.append(span_id)
                                found = "yes"
                                break
                    node["children"][child_id] = selected_spans_ids
                    for span_id in selected_spans_ids:
                        graph[span_id]["ellipsed_parents"].append(node["id"])
        # flatten list of children
        flatten_children = []
        for child in graph[node["id"]]["children"]:
            if type(child) == list:
                for subchild in child:
                    flatten_children.append(subchild)
            else:
                flatten_children.append(child)
        graph[node["id"]]["children"] = flatten_children
        # if terminal, add node's text to the list of terminals
        if node["terminal"] == "yes":
            terminals.append(node["text"])
        # count tokens for a BERT-based system
            bert_len += 4 # left bracket + right bracket + pos + text
        elif node["terminal"] == "no":
            bert_len += 3 # left bracket + right bracket + tag

    # count ellipsis types per clause
    for node in graph:
        if len(node["ellipsed_parents"]) > 0:
            ellipsis_type = node["function_label"]
            for parent in node["ellipsed_parents"]:
                parent_clause = graph[parent]["parent_clause"]
                graph[parent_clause]["ellipsis_types"][ellipsis_type] += 1

    # build sentence string (without duplication of ellipsis as in the original SFGbank)
    string = " ".join(terminals)

    return string, graph, ellipsis, bert_len


def gen_graphs(files, ellipsis_only, max_len):
    """
    Generate a dictionary containing sentence strings, graphs, and whether they contain ellipsis or not.
    """

    data = {"docs": [], "total_sents": 0, "ellipsis_types": defaultdict(int)}

    for f in files:
        doc = {"doc": f.name, "sents": []}

        doc_tree = ET.parse(f).getroot()
        doc_text = doc_tree[0].text[9:-5]
        doc_parses = doc_tree[1]

        sents = [parse for parse in doc_parses if parse.get("type") == "Clause_Complex"]
        for sent in sents:
            string, graph, ellipsis, bert_len = xml2graph(sent, doc_text, tag_map)
            if string == None:
                continue
            # exclude sentences without ellipsis
            if ellipsis_only == True and ellipsis == "no":
                continue
            # exclude sentences that exceed the maximum length allowed by BERT
            if max_len == True and bert_len > 512: # maximum length = 512
                continue
            doc["sents"].append({"string": string, "graph": graph, "ellipsis": ellipsis, "bert_len": bert_len})
            data["total_sents"] += 1
            ellipsis_types = count_ellipsis_types(graph)
            for type_ in ellipsis_types:
                data["ellipsis_types"][type_] += ellipsis_types[type_]
        data["docs"].append(doc)

    return data


def gen_str(graphs):
    """
    Generate file containing sentences as strings
    """

    strings = "" 
    for doc in graphs["docs"]:
        for sent in doc["sents"]:
            string = sent["string"]
            strings += string + "\n"

    return strings


def gen_splits(input_dir, output_dir, ellipsis_only, max_len, gen_str_files):
    """
    Generate train/development/test sets following the conventional split for the Penn Treebank.
    """

    input_files = sorted([f for f in input_dir.iterdir()])

    # files in each set
#    train_files = [f for f in input_files if f.name.startswith(("wsj_02","wsj_03", "wsj_04", "wsj_05", "wsj_06", "wsj_07", "wsj_08", "wsj_09", "wsj_10", "wsj_11", "wsj_12", "wsj_13", "wsj_14", "wsj_15", "wsj_16", "wsj_17", "wsj_18", "wsj_19", "wsj_20", "wsj_21"))]
#    dev_files = [f for f in input_files if f.name.startswith("wsj_22")]
    test_files = [f for f in input_files if f.name.startswith("wsj_23")] 

#    train_graphs = gen_graphs(train_files, ellipsis_only, max_len)
#    dev_graphs = gen_graphs(dev_files, ellipsis_only, max_len)
    test_graphs = gen_graphs(test_files, ellipsis_only, max_len)

    # count total for each type of ellipsis
#    print("Total for each type of ellipsis:\n")
#    for type_ in train_graphs["ellipsis_types"]:
#        print(type_ + ": " + str(train_graphs["ellipsis_types"][type_] + dev_graphs["ellipsis_types"][type_] + test_graphs["ellipsis_types"][type_]))

#    with open(output_dir.joinpath("train.json"), "w+") as train_json:
#        json.dump(train_graphs, train_json)
#    with open(output_dir.joinpath("dev.json"), "w+") as dev_json:
#        json.dump(dev_graphs, dev_json)
    with open(output_dir.joinpath("test.json"), "w+") as test_json:
        json.dump(test_graphs, test_json)

#    if gen_str_files:
#         with open(output_dir.joinpath("train.txt"), "w+") as train_str:
#           train_str.write(gen_str(train_graphs))
#        with open(output_dir.joinpath("dev.txt"), "w+") as dev_str:
#            dev_str.write(gen_str(dev_graphs))
#        with open(output_dir.joinpath("test.txt"), "w+") as test_str:
#           test_str.write(gen_str(test_graphs))     


def main(
    input_dir: Path, 
    output_dir: Path,
    gen_str_files: bool = typer.Option(False, help="Generate string files"),
    max_len: bool = typer.Option(False, help="Exclude sentences that exceed the maximum length allowed by BERT"),  
    ellipsis_only: bool = typer.Option(False, help="Exclude sentences that do not contain ellipsis"),
    ):
    
    gen_splits(input_dir, output_dir, gen_str_files=False, max_len=True, ellipsis_only=True)


if __name__ == "__main__":
    typer.run(main)