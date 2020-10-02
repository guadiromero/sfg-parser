# Transformations for tractable SFG parsing

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

The graphs contain main edges and secondary edges pointing to ellipsed constituents.

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

Results for all edges, non-ellipsed edges and ellipsed-edges.

| All               | UP    | UR    | UF    | LP    | LR    | LF    |
|-------------------|-------|-------|-------|-------|-------|-------|
| start             | 86.49 | 86.49 | 86.49 | 85.13 | 85.13 | 85.13 |
| start-without-pos | 86.6  | 86.6  | 86.6  | 85.21 | 85.21 | 85.21 |
| end               | 87.67 | 87.67 | 87.67 | 86.09 | 86.09 | 86.09 |
| end-extra-node    | 88.82 | 88.82 | 88.82 | 87.52 | 87.52 | 87.52 |

| Ellipsed          | UP    | UR    | UF    | LP    | LR    | LF    |
|-------------------|-------|-------|-------|-------|-------|-------|
| start             | 65.55 | 44.48 | 53.0  | 65.07 | 44.16 | 52.61 |
| start-without-pos | 65.45 | 40.58 | 50.1  | 64.92 | 40.26 | 49.7  |
| end               | 75.6  | 61.36 | 67.74 | 75.6  | 61.36 | 67.74 |
| end-extra-node    | 76.95 | 60.71 | 67.88 | 76.95 | 60.71 | 67.88 |

| Non-ellipsed      | UP    | UR    | UF    | LP    | LR    | LF    |
|-------------------|-------|-------|-------|-------|-------|-------|
| start             | 90.82 | 90.82 | 90.82 | 89.37 | 89.37 | 89.37 |
| start-without-pos | 91.01 | 91.01 | 91.01 | 89.5  | 89.5  | 89.5  |
| end               | 89.77 | 89.77 | 89.77 | 88.15 | 88.15 | 88.15 |
| end-extra-node    | 91.11 | 91.11 | 91.11 | 89.73 | 89.73 | 89.73 |

## Comparison to previous SFG parsing work

We used the same evaluation script and corpora from Costetchi (2020) to compare its performance with that of our system. To evaluate our system, we preprocessed the text with `previous_work_comparison/tokenize.py`, parsed the constituency trees and extracted constituent spans from them with `previous_work_comparison/ptb2mcg.py`. We deleted duplicates from the gold annotated spans and the spans predicted by Costetchi's parser with `previous_work_comparison/simplify_gold.py`. We only considered constituency annotations and ignored the SFG features as well as ellipsis recovery, since Costetchi's system does not handle it. Below are the results for the OE and OCD corpora and an average of both.

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
