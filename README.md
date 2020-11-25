# Transformations for tractable SFG parsing

## Overview

This repository contains the code that was used to train and evaluate the models for my master thesis at Saarland University.

**Abstract:** The need to build syntactic parsers with improved usability have fueled a renewed interest in Systemic Functional Grammar (SFG). Among its key features, SFG presents a flatter constituency structure, makes ellipsis explicit and appends functional tags to its constituents. We concentrate our efforts on the first two aspects as they are the most challenging to predict, and present the task of SFG constituency parsing and ellipsis resolution, including a dataset and an evaluation method. We represent ellipsis with secondary edges that form directed acyclic graphs (DAGs) and propose a method for predicting these graphs via tractable DAG to tree transformations. The suggested strategies remove the secondary edges and encode their information in the constituency labels, so that standard tree parsers can be used and the original DAG representations can be later recovered. Experiments with different transformations show that this is a viable approach and that some representations are more learnable than others. Our system outperforms the previous work on SFG parsing and handles a wider arrange of ellipsis types, a feature with potential applications inside and outside the SFG domain.

## Requirements

Install [Typer](https://typer.tiangolo.com/) and [NLTK](https://www.nltk.org/).

```
pip install typer
pip install --user -U nltk
```

Follow the official instructions to install the [Berkeley parser](https://github.com/nikitakit/self-attentive-parser).

## Dataset

Build the ellipsis corpus by converting the original SFGbank to graphs and using the conventional splits of the Penn Treebank:

- Training: Sections 2-21 of the WSJ
- Development: Section 22 of the WSJ
- Testing: Section 23 of the WSJ

The graphs contain main edges and secondary edges pointing to elided constituents.

Usage: 
```
python dataset/build_dataset.py [OPTIONS] INPUT_DIR OUTPUT_DIR
```

| Argument        | Type     | Description                                                      | Default |
|-----------------|----------|------------------------------------------------------------------|---------|
| INPUT_DIR       | Required | Path to the directory containing the original SFGbank            | -       |
| OUTPUT_DIR      | Required | Path to the directory where to save the dataset                  | -       |
| --gen-str-files | Optional | Exclude sentences that exceed the maximum length allowed by BERT | False   |
| --max-len       | Optional | Exclude sentences that do not contain ellipsis                   | False   |

Example:
```
python dataset/build_dataset.py data/sfgbank data/graphs --gen-str-files --max-len
```

## Preprocessing

Convert the graphs to phrase-structure trees, using a specific strategy to encode ellipsis.

Usage:
```
python preprocessing/graph2tree.py [OPTIONS] INPUT_DIR OUTPUT_DIR
```

| Argument        | Type     | Description                                                                      | Default     |
|-----------------|----------|----------------------------------------------------------------------------------|-------------|
| INPUT_DIR       | Required | Path to the directory containing the dataset                                     | -           |
| OUTPUT_DIR      | Required | Path to the directory where to save the trees                                    | -           |
| --strategy TEXT | Optional | Strategy for encoding ellipsis: start / start-without-pos / end / end-extra-node | end-extra-node |
Example:
```
python preprocessing/graph2tree.py data/graphs data/trees-end-extra-node --strategy end-extra-node
```

## Training

Train the Berkeley parser with the trees encoding ellipsis.

```
python src/main.py train --use-bert --model-path-base models/end-extra-node --bert-model "bert-large-uncased" --num-layers 2 --learning-rate 0.00005 --batch-size 32 --eval-batch-size 16 --subbatch-max-tokens 500 --train-path data/end-extra-node/train.txt --dev-path data/end-extra-node/dev.txt --predict-tags
```

## Parsing

Parse the test sentences with the trained model.

```
python src/main.py parse --model-path-base models/end-extra-node/_dev\=93.12.pt --input-path data/strings/test.txt --output-path data/end-extra-node-predicted/test.txt --eval-batch-size 16
```

## Postprocessing

Convert the predicted trees to graphs, recovering ellipsis with the chosen strategy.

Usage:
```
python postprocessing/graph2tree.py [OPTIONS] INPUT_DIR OUTPUT_DIR
```

| Argument        | Type     | Description                                                                      | Default     |
|-----------------|----------|----------------------------------------------------------------------------------|-------------|
| INPUT_DIR       | Required | Path to the directory containing the dataset                                     | -           |
| OUTPUT_DIR      | Required | Path to the directory where to save the trees                                    | -           |
| --strategy TEXT | Optional | Strategy for encoding ellipsis: start / start-without-pos / end / end-extra-node | end-extra-node |

Example:
```
python postprocessing/graph2tree.py data/trees-end-extra-node-predicted data/graphs-end-extra-node-predicted --strategy end-extra-node
```

## Evaluation

Evaluate the predicted graphs. To avoid alignment issues, the graphs are evaluated as dependencies.

Usage:
```
python eval/eval.py GOLD_FILE PREDICTED_FILE
```

| Argument       | Type     | Description                                           | Default |
|----------------|----------|-------------------------------------------------------|---------|
| GOLD_FILE      | Required | Path to the file containing the gold test graphs      | -       |
| PREDICTED_FILE | Required | Path to the file containing the predicted test graphs | -       |

Example:
```
python eval/eval.py data/graphs/test.json data/graphs-end-extra-node-predicted/test.json
```

## Results

Results for all edges, non-elided edges and elided-edges.

| All edges                         | UP    | UR    | UF    | LP    | LR    | LF    |
|-----------------------------------|-------|-------|-------|-------|-------|-------|
| start                             | 86.5  | 86.5  | 86.5  | 85.1  | 85.1  | 85.1  |
| start-without-pos                 | 86.6  | 86.6  | 86.6  | 85.2  | 85.2  | 85.2  |
| end                               | 87.7  | 87.7  | 87.7  | 86.1  | 86.1  | 86.1  |
| end-extra-node                    | 88.8  | 88.8  | 88.8  | 87.5  | 87.5  | 87.5  |
| start-end-extra-node              | 88.9  | 88.9  | 88.9  | 87.3  | 87.3  | 87.3  |
| start-end-extra-node-heuristic    | 89.1  | 89.1  | 89.1  | 87.6  | 87.6  | 87.6  |
| sdp                               | 88.0  | 88.0  | 88.0  | 86.5  | 86.5  | 86.5  |

| Elided edges                      | UP    | UR    | UF    | LP    | LR    | LF    |
|-----------------------------------|-------|-------|-------|-------|-------|-------|
| start                             | 65.6  | 44.5  | 53.0  | 65.1  | 44.2  | 52.6  |
| start-without-pos                 | 65.5  | 40.6  | 50.1  | 64.9  | 40.3  | 49.7  |
| end                               | 75.6  | 61.4  | 67.7  | 75.6  | 61.4  | 67.7  |
| end-extra-node                    | 77.0  | 60.7  | 67.9  | 77.0  | 60.7  | 67.9  |
| start-end-extra-node              | 86.6  | 62.7  | 72.7  | 84.3  | 61.0  | 70.8  |
| start-end-extra-node-heuristic    | 87.0  | 67.2  | 75.8  | 83.2  | 64.3  | 72.6  |
| sdp                               | 81.2  | 77.0  | 79.0  | 80.5  | 76.3  | 78.3  |

| Non-elided edges                  | UP    | UR    | UF    | LP    | LR    | LF    |
|-----------------------------------|-------|-------|-------|-------|-------|-------|
| start                             | 90.8  | 90.8  | 90.8  | 89.4  | 89.4  | 89.4  |
| start-without-pos                 | 91.0  | 91.0  | 91.0  | 89.5  | 89.5  | 89.5  |
| end                               | 89.8  | 89.8  | 89.8  | 88.2  | 88.2  | 88.2  |
| end-extra-node                    | 91.1  | 91.1  | 91.1  | 89.7  | 89.7  | 89.7  |
| start-end-extra-node              | 91.2  | 91.2  | 91.2  | 89.5  | 89.5  | 89.5  |
| start-end-extra-node-heuristic    | 91.0  | 91.0  | 91.0  | 89.7  | 89.7  | 89.7  |
| sdp                               | 90.1  | 90.1  | 90.1  | 88.6  | 88.6  | 88.6  |

## Comparison to previous SFG parsing work

We used the same evaluation method and corpora from [Costetchi (2020)](https://media.suub.uni-bremen.de/handle/elib/4281) to compare its performance with that of our system. To evaluate our system, we preprocessed the text with `previous_work_comparison/tokenize.py`, parsed the constituency trees and extracted constituent spans from them with `previous_work_comparison/ptb2mcg.py`. We deleted duplicates from the gold annotated spans and the spans predicted by Costetchi's parser with `previous_work_comparison/simplify_gold.py`. We only considered constituency annotations and ignored the SFG features as well as ellipsis recovery, since Costetchi's system does not handle it. Below are the results for the OE and OCD corpora and an average of both.

| OE corpus        | Precision | Recall | FScore |
|------------------|-----------|--------|--------|
| Costetchi (2020) | 50.16     | 97.15  | 65.73  |
| Our system       | 54.42     | 93.75  | 68.75  |

| OCD corpus       | Precision | Recall | FScore |
|------------------|-----------|--------|--------|
| Costetchi (2020) | 61.45     | 90.67  | 73.25  |
| Our system       | 76.32     | 94.61  | 84.48  |

| Average          | Precision | Recall | FScore |
|------------------|-----------|--------|--------|
| Costetchi (2020) | 55.81     | 93.91  | 69.49  |
| Our system       | 65.36     | 94.18  | 76.61  |
