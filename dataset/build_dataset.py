from pathlib import Path
import typer
import xml.etree.ElementTree as ET
import json
from tag_maps import TAGS_SFG as tag_map


def xml2graph(node, text, tag_map):
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

    # push the root of the tree to the stack
    stack.append((node, 0))
    
    while len(stack) > 0:
       # pop the last element in the stack
        last = stack.pop()
        node = last[0]
        parent = last[1]
        if node.tag == "Constituent":
            # get basic information from the node
            node_type = node.get('type')                
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
                span = [subnode.get("idref") for subnode in node.iter() if subnode.tag == "ConstituentRef"]
                graph[parent]["children"].append(span)
            if ellipsed_node == False:
                # create a graph node
                graph_id = len(tracking_list)
                graph_node = {"id": graph_id, "children": [], "parent": parent, "ellipsed_parents": [], "terminal": terminal, "tag": tag, "text": node_text}
                # add node span to the tracking list
                span = [subnode.get("id") for subnode in node.iter() if subnode.get("type") == "Word"]
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
                for span_id, span in enumerate(tracking_list):
                    if set(child) == set(span):
                        # replace ellipsed node span for node id
                        node["children"][child_id] = span_id  
                        # add parent to the node's ellipsed parents list
                        graph[span_id]["ellipsed_parents"].append(node["id"]) 
        # if terminal, add node's text to the list of terminals
        if node["terminal"] == "yes":
            terminals.append(node["text"])
        # count tokens for a BERT-based system
            bert_len += 4 # left bracket + right bracket + pos + text
        elif node["terminal"] == "no":
            bert_len += 3 # left bracket + right bracket + tag            

    # build sentence string (without duplication of ellipsis as in the original SFGbank)
    string = " ".join(terminals)

    return string, graph, ellipsis, bert_len


def gen_json(files, ellipsis_only, max_len):
    """
    Generate a dictionary containing sentence strings, graphs, and whether they contain ellipsis or not.
    """

    data = {"docs": []}

    for f in files:
        doc = {"doc": f.name, "sents": []}

        doc_tree = ET.parse(f).getroot()
        doc_text = doc_tree[0].text[9:-5]
        doc_parses = doc_tree[1]

        sents = [parse for parse in doc_parses if parse.get("type") == "Clause_Complex"]
        for sent in sents:
            string, graph, ellipsis, bert_len = xml2graph(sent, doc_text, tag_map)
            # exclude sentences without ellipsis
            if ellipsis_only == True and ellipsis == "no":
                continue
            # exclude sentences that exceed the maximum length allowed by BERT
            if max_len == True and bert_len > 512: # maximum length = 512
                continue
            else:
                doc["sents"].append({"string": string, "graph": graph, "ellipsis": ellipsis, "bert_length": bert_len})
        data["docs"].append(doc)

    return data


def gen_splits(input_dir, output_dir, ellipsis_only, max_len):
    """
    Generate train/development/test sets following the conventional split for the Penn Treebank.
    """

    input_files = sorted([f for f in input_dir.iterdir()])

    # files in each set
    train_files = [f for f in input_files if f.name.startswith(("wsj_02","wsj_03", "wsj_04", "wsj_05", "wsj_06", "wsj_07", "wsj_08", "wsj_09", "wsj_10", "wsj_11", "wsj_12", "wsj_13", "wsj_14", "wsj_15", "wsj_16", "wsj_17", "wsj_18", "wsj_19", "wsj_20", "wsj_21"))]
    dev_files = [f for f in input_files if f.name.startswith("wsj_22")]
    test_files = [f for f in input_files if f.name.startswith("wsj_23")] 

    train_graphs = gen_json(train_files, ellipsis_only, max_len)
    dev_graphs = gen_json(dev_files, ellipsis_only, max_len)
    test_graphs = gen_json(test_files, ellipsis_only, max_len)

    with open(output_dir.joinpath("train.json"), "w+") as train_json:
        json.dump(train_graphs, train_json)
    with open(output_dir.joinpath("dev.json"), "w+") as dev_json:
        json.dump(dev_graphs, dev_json)
    with open(output_dir.joinpath("test.json"), "w+") as test_json:
        json.dump(test_graphs, test_json)


def main(
    input_dir: Path, 
    output_dir: Path,
    max_len: bool = typer.Option(False, help="Exclude sentences that exceed the maximum length allowed by BERT"),  
    ellipsis_only: bool = typer.Option(False, help="Exclude sentences that do not contain ellipsis"),
    ):
    
    gen_splits(input_dir, output_dir, ellipsis_only, max_len)


if __name__ == "__main__":
    typer.run(main)