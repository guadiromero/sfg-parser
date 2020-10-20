from pathlib import Path
import typer
from nltk import ParentedTree
import re


def read_file(file_):
    """
    """

    trees = []

    with open(file_, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        tree = ParentedTree.fromstring(line)  
        trees.append(tree)

    return trees  


def get_spans(tree):
    """
    """

    spans = []

    # constuct a dictionary of terminals with their treepositions and correspondent indexes
    terminals_list = [st.treeposition() for st in tree.subtrees() if st.height() == 2]
    terminals_dict = {pos:index for index,pos in enumerate(terminals_list)}

    # for each non-terminal
    for st in tree.subtrees():
        if st.height() > 2:
            if "start" in st.label() or "end" in st.label():
                # get non-terminal span
                leaves = [terminals_dict[sst.treeposition()] for sst in st.subtrees() if sst.height() == 2]
                splitted_label = re.split("(start|end)", st.label())
                simplified_label = splitted_label[0]    
                start_labels = True if len([split for split in splitted_label if split == "start"]) > 0 else False
                end_labels = True if len([split for split in splitted_label if split == "end"]) > 0 else False   
                span = ((leaves[0], leaves[-1]), simplified_label, (start_labels, end_labels))
                spans.append(span)

    return spans


def count_correct(gold_spans, predicted_spans, check_labels=False):
    """
    """

    if check_labels == False:
        gold_spans = [span[0] for span in gold_spans]
        predicted_spans = [span[0] for span in predicted_spans]  

    common_spans = [span for span in gold_spans if span in predicted_spans]
    correct = len(common_spans)

    return correct


def score(gold_file, predicted_file):
    """
    """

    correct_unlabeled = 0
    correct_labeled = 0
    total_gold = 0
    total_predicted = 0

    gold_trees = read_file(gold_file)
    predicted_trees = read_file(predicted_file)

    for gold_tree, predicted_tree in zip(gold_trees, predicted_trees):
        gold_spans = get_spans(gold_tree)
        predicted_spans = get_spans(predicted_tree)
        correct_unlabeled += count_correct(gold_spans, predicted_spans)
        correct_labeled += count_correct(gold_spans, predicted_spans, check_labels=True)
        total_gold += len(gold_spans)
        total_predicted += len(predicted_spans)

    unlabeled_p = correct_unlabeled / total_predicted
    unlabeled_r = correct_unlabeled / total_gold
    unlabeled_f = 2 * ((unlabeled_p * unlabeled_r) / (unlabeled_p + unlabeled_r))
    labeled_p = correct_labeled / total_predicted
    labeled_r = correct_labeled / total_gold
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

    score(gold_file, predicted_file)


if __name__ == "__main__":
    typer.run(main)