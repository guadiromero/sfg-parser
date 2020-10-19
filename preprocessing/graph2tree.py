from pathlib import Path
import typer
import json
from nltk import Tree, ParentedTree
import re


def get_ellipsis_tag_from_graph(graph, target_node):
    """
    Given a graph and a node, get the starting node ellipsis tag for it.
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
    Given a tree and a tree position, get the ending node ellipsis tag for it.
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
    Given a tree and an ending node ellipsis tag, get the tree position for it.
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


def traverse_graph(graph):  
    """
    Convert a single graph to a phrase-structure tree, without encoding ellipsis.

    Example: (CLX (CL (NG (PRP They)) (VG (VBD were) (VBG drinking)) (NG (NN tea))) (CL (CONJG (CC and)) (VG (VBG eating)) (NG (NNS scons))))
    """

    def traverse(graph, node):

        children = [int(c) for c in graph[node]["children"]]
        tagged_children = []
        for child in children:
            ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
            # if the child is explicit
            if node not in ellipsed_parents:
                if graph[child]["terminal"] == "yes":
                    tagged_children.append(ParentedTree(graph[child]["tag"], [graph[child]["text"]]))
                else:
                    tagged_children.append(traverse(graph, child))
            
        tree = ParentedTree(graph[node]["tag"], tagged_children)

        return tree

    tree = traverse(graph, 0)

    return tree
  

def traverse_graph_start(graph):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appendig a tag to the starting node of the ellipsis edge.

    Example: (CLX (CL (NG (PRP They)) (VG (VBD were) (VBG drinking)) (NG (NN tea))) (CL (CONJG (CCstartNG0 and)) (VGstartVBD0 (VBG eating)) (NG (NNS scons))))
    """

    def traverse(graph, node):

        children = [int(c) for c in graph[node]["children"]]
        tagged_children = []
        for child in children:
            ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
            # if the child is explicit
            if node not in ellipsed_parents:
                if graph[child]["terminal"] == "yes":
                    tagged_children.append(ParentedTree(graph[child]["tag"], [graph[child]["text"]]))
                else:
                    tagged_children.append(traverse(graph, child))
            # if the child is ellipsed
            else:
                ellipsis_tag = get_ellipsis_tag_from_graph(graph, child)
                tagged_children.append(ParentedTree(ellipsis_tag, []))
            
        tree = ParentedTree(graph[node]["tag"], tagged_children)

        return tree
    
    tree = traverse(graph, 0)
    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        # append starting_node tag to the previous node
        if tree[pos].label().startswith("start"):
            prev_pos_i = pos_i + 1
            prev_pos = rev_positions[prev_pos_i]
            tree[prev_pos].set_label(tree[prev_pos].label() + tree[pos].label())
            del tree[pos]

    return tree  


def traverse_graph_start_without_pos(graph):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appendig a tag to the starting node of the ellipsis edge.
    Append ellipsis tags only to non-terminals.

    Example: (CLX (CL (NG (PRP They)) (VG (VBD were) (VBG drinking)) (NG (NN tea))) (CL (CONJGstartNG0 (CC and)) (VGstartVBD0 (VBG eating)) (NG (NNS scons))))
    """

    def traverse(graph, node):

        children = [int(c) for c in graph[node]["children"]]
        tagged_children = []
        for child in children:
            ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
            # if the child is explicit
            if node not in ellipsed_parents:
                if graph[child]["terminal"] == "yes":
                    tagged_children.append(ParentedTree(graph[child]["tag"], [graph[child]["text"]]))
                else:
                    tagged_children.append(traverse(graph, child))
            # if the child is ellipsed
            else:
                ellipsis_tag = get_ellipsis_tag_from_graph(graph, child)
                tagged_children.append(ParentedTree(ellipsis_tag, []))
            
        tree = ParentedTree(graph[node]["tag"], tagged_children)

        return tree
    
    tree = traverse(graph, 0)
    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        # append starting_node tag to the previous non-terminal node
        if tree[pos].label().startswith("start"):
            prev_pos_i = pos_i + 1
            while tree[rev_positions[prev_pos_i]].height() == 2:
                prev_pos_i += 1
            prev_pos = rev_positions[prev_pos_i]
            tree[prev_pos].set_label(tree[prev_pos].label() + tree[pos].label())
            del tree[pos]

    return tree  


def traverse_graph_end(graph):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by appending a tag to the ending node of the ellipsis edge.

    Example: (CLX (CL (NGendCC0 (PRP They)) (VG (VBDendVG1 were) (VBG drinking)) (NG (NN tea))) (CL (CONJG (CC and)) (VG (VBG eating)) (NG (NN scons))))
    """

    # get tree with starting node tags

    def traverse(graph, node):

        children = [int(c) for c in graph[node]["children"]]
        tagged_children = []
        for child in children:
            ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
            # if the child is explicit
            if node not in ellipsed_parents:
                if graph[child]["terminal"] == "yes":
                    tagged_children.append(ParentedTree(graph[child]["tag"], [graph[child]["text"]]))
                else:
                    tagged_children.append(traverse(graph, child))
            # if the child is ellipsed
            else:
                ellipsis_tag = get_ellipsis_tag_from_graph(graph, child)
                tagged_children.append(ParentedTree(ellipsis_tag, []))
            
        tree = ParentedTree(graph[node]["tag"], tagged_children)

        return tree

    tree = traverse(graph, 0)

    # get ending node tags
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

    # insert ending node tags
    for index, st in enumerate(tree.subtrees()):
        for end_location, end_tag in end_tags:
            if st.treeposition() == end_location:
                st.insert(index, ParentedTree(end_tag, []))

    # delete starting node tags
    subtrees = [st for st in tree.subtrees()]
    reversed_subtrees = [st for st in reversed(subtrees)]
    for st in reversed_subtrees:
        if st.label().startswith("start"):
            del tree[st.treeposition()]

    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        # append ending node tag to the parent of the current node
        if tree[pos].label().startswith("end"):
            parent_pos = tree[pos].parent().treeposition()
            tree[parent_pos].set_label(tree[parent_pos].label() + tree[pos].label())
            del tree[pos] 

    return tree


def traverse_graph_end_extra_node(graph):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by wrapping the ending node of the ellipsis edge with an extra node.

    Example: (CLX (CL (NGendCC0 (NG (PRP They))) (VG (VBDendVG1 (VBD were)) (VBG drinking)) (NG (NN mate))) (CL (CONJG (CC and)) (VG (VBG eating)) (NG (NN pastafrola))))
    """

    # get tree with ending tags
    tree = traverse_graph_end(graph)

    # wrap each constituent that has ending tags with an extra node

    def traverse(tree):
        children = []
        for subtree in tree:
            if type(subtree) == str:
                children.append(subtree)
            else:
                splits = re.split("(end)", subtree.label())
                const_tag = splits[0]
                ellipsis_tag = "".join(splits[1:])  
                if len(ellipsis_tag) > 0:
                    children.append(Tree(subtree.label(), [Tree(const_tag, [sst for sst in subtree])]))
                else:
                    children.append(traverse(subtree))

        return Tree(tree.label(), children)

    tree = traverse(tree)

    return tree


def traverse_graph_start_end_extra_node(graph):  
    """
    Convert a single graph to a phrase-structure tree, 
    encoding ellipsis by wrapping the start and ending nodes of the ellipsis edge with extra nodes.

    Example: (CLX (CL (NGend0 (PRP They)) (VG (VBDend1 were) (VBG drinking)) (NG (NN tea))) (CL (CONJG (CCstart0 (CC and))) (VGstart1 (VG (VBG eating)) (NG (NN scons))))
    """

    # get tree with starting node tags

    def traverse(graph, node):

        children = [int(c) for c in graph[node]["children"]]
        tagged_children = []
        for child in children:
            ellipsed_parents = [int(p) for p in graph[child]["ellipsed_parents"]]
            # if the child is explicit
            if node not in ellipsed_parents:
                if graph[child]["terminal"] == "yes":
                    tagged_children.append(ParentedTree(graph[child]["tag"], [graph[child]["text"]]))
                else:
                    tagged_children.append(traverse(graph, child))
            # if the child is ellipsed
            else:
                ellipsis_tag = get_ellipsis_tag_from_graph(graph, child)
                tagged_children.append(ParentedTree(ellipsis_tag, []))
            
        tree = ParentedTree(graph[node]["tag"], tagged_children)

        return tree

    tree = traverse(graph, 0)

    # get ending node tags
    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    end_tags = []
    ellipsis_id = 0 # assign an id to each ellipsis start and end nodes
    for pos_i, pos in enumerate(positions):
        if tree[pos].label().startswith("start"):
            ellipsis_tag = tree[pos].label().split("start")[-1]
            tree[pos].set_label("start" + str(ellipsis_id))
            end_location = get_ellipsis_location(tree, ellipsis_tag)
            end_tag = "end" + str(ellipsis_id)
            end_tags.append((end_location, end_tag))
            ellipsis_id += 1

    # insert ending node tags
    for index, st in enumerate(tree.subtrees()):
        for end_location, end_tag in end_tags:
            if st.treeposition() == end_location:
                st.insert(index, ParentedTree(end_tag, []))

    positions = [pos for pos in tree.treepositions() if pos not in tree.treepositions("leaves")]
    rev_positions = [pos for pos in reversed(positions)]
    for pos_i, pos in enumerate(rev_positions):
        # append start tag to the previous node
        if tree[pos].label().startswith("start"):
            prev_pos_i = pos_i + 1
            prev_pos = rev_positions[prev_pos_i]
            tree[prev_pos].set_label(tree[prev_pos].label() + tree[pos].label())
            del tree[pos]
        # append end tag to the parent of the current node
        elif tree[pos].label().startswith("end"):
            parent_pos = tree[pos].parent().treeposition()
            tree[parent_pos].set_label(tree[parent_pos].label() + tree[pos].label())
            del tree[pos] 

    # wrap each constituent that has end or start tags with extra nodes

    def add_extra_nodes(tree):
        children = []
        for subtree in tree:
            if type(subtree) == str:
                children.append(subtree)
            else:
                splits = re.split("(start|end)", subtree.label())
                const_tag = splits[0]
                ellipsis_tag = "".join(splits[1:])  
                if len(ellipsis_tag) > 0:
                    children.append(Tree(subtree.label(), [Tree(const_tag, [sst for sst in subtree])]))
                else:
                    children.append(add_extra_nodes(subtree))

        return Tree(tree.label(), children)

    tree = add_extra_nodes(tree)

    return tree


def get_string(tree):
    """
    Get string representation from a tree.
    """           

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
                    graph = sent["graph"]
                    if strategy == "start":
                        tree = traverse_graph_start(graph)
                    elif strategy == "start-without-pos":
                        tree = traverse_graph_start_without_pos(graph)
                    elif strategy == "end":
                        tree = traverse_graph_end(graph)
                    elif strategy == "end-extra-node":
                        tree = traverse_graph_end_extra_node(graph)
                    elif strategy == "start-end-extra-node":
                        tree = traverse_graph_start_end_extra_node(graph)
                    tree_string = get_string(tree)
                    trees += tree_string + "\n"
        with open(output_dir.joinpath(f.name).with_suffix(".txt"), "w+") as tree_files:
            tree_files.write(trees)


def main(
    input_dir: Path, 
    output_dir: Path, 
    strategy: str = typer.Option("end-extra-node", help="Strategy for encoding ellipsis: start, start-without-pos, end, end-extra-node, start-end-extra-node"),
    ):
    
    convert_treebank(input_dir, output_dir, strategy)


if __name__ == "__main__":
    typer.run(main)