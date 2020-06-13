# A Parser for Systemic Functional Grammar

## Preprocessing

### Conversion of constituency from XML to Penn Treebank format

The SFG data was converted from XML to Penn Treebank format by linearizing the trees with first-depth search and mapping the constituency tags. Sentences that exceeded the maximum sequence length allowed (512) were deleted (185 out of 167066), giving a total of 167881 sentences. Type this command line if you want to convert the data yourself.

Usage:

```
python xml2penn.py -input-dir 'path to the directory containing the XML data files to convert' -output-dir 'path to the directory where to save the converted data files' --max-len 'maximum sentence length allowed'
```

Example:

```
python xml2penn.py -input-dir data/sfgbank-unsplit-xml -output-dir data/sfgbank-unsplit-penn
```

### Dataset split

The files were concatenated into three groups: 80% of the files for training, 10% for development and 10% for testing. Type this command line if you want to split the data yourself.

Usage:

```
python build_dataset.py -input-dir 'path to the directory containing the data files' -output-dir 'path to the directory where to save the train/dev/test datasets' -data-name 'name of the data to save' --dev-size 'int representing the size of the development set as percentage' --test-size 'int representing the size of the testing set as percentage'
```

Example:

```
python build_dataset.py -input-dir data/sfgbank-unsplit-penn -output-dir data/sfgbank-split-penn -data-name sfgbank-penn
```

These output files at this step were used to train and evaluate the Berkeley parser.

### Conversion of constituency Penn Treebank format to dependency CoNLL format

The train/dev/test splits were converted from the constituency Penn Treebank format to the dependency CoNLL format using [StanfordNLP](https://nlp.stanford.edu/software/lex-parser.html#Download) (see relevant [FAQ](https://nlp.stanford.edu/software/parser-faq.shtml#s) and [StanfordNLP manual](https://nlp.stanford.edu/software/dependencies_manual.pdf))

The conversion was done by using the following command for each of the splits:

```
java -cp stanford-parser.jar edu.stanford.nlp.trees.EnglishGrammaticalStructure -treeFile data/sfgbank-split-penn/sfg-train.penn -nonCollapsed -conllx > data/sfgbank-split-conll/sfg-train.conll
```

### Conversion of dependency CoNLL format to spaCy's JSON format

The fine-grained PoS tags in each of the splits were mapped to [spaCy's coarse-grained tags](https://github.com/explosion/spaCy/blob/master/spacy/lang/en/tag_map.py), using the following script:

Usage:

```
python map_pos_tags.py -input-file 'path to the input file' -output-file 'path to the output file'
```

Example:

```
python map_pos_tags.py -input-file data/sfgbank-split-conll/sfgbank-train.conll -output-file data/sfgbank-split-conll-coarse/sfgbank-train.conll
```

The splits were then converted from CoNLL to JSON format by using [spaCy's converter](https://spacy.io/api/cli#convert):

```
python -m spacy convert data/sfgbank-split-conll-coarse/sfgbank-train.conll data/sfgbank-split-json/ --converter conll
```

These output files were used to train and evaluate spaCy's dependency parser

## Constituency parsing

### Training

The [BERT-based Berkeley Neural Parser](https://github.com/nikitakit/self-attentive-parser) was trained with the SFG dataset using the following command:

```
python src/main.py train --use-bert --model-path-base models/en_bert_sfg --bert-model "bert-large-uncased" --num-layers 2 --learning-rate 0.00005 --batch-size 32 --eval-batch-size 16 --subbatch-max-tokens 500 --train-path data/sfgbank-split-penn/sfgbank-train.penn --dev-path data/sfgbank-split-penn/sfgbank-dev.penn
```

### Evaluation

The trained model was tested using the following command:

```
python src/main.py test --model-path-base models/en_bert_sfg/en_bert_sfg_dev=95.79.pt
```

These are the scores achieved by our model, as well as the three models provided in the Berkeley Parser repository.

|                                  | Recall      | Precision      | FScore      |
|----------------------------------|-------------|----------------|-------------|
| CharLSTM + Penn_Treebank         | 93.20       | 93.90          | 93.55       |
| Transformer_ELMO + Penn_Treebank | 94.85       | 95.40          | 95.13       |
| Transformer_BERT + Penn_Treebank | 95.41       | 95.99          | 95.70       |
| Transformer_BERT + SFG_Treebank  | 95.51       | 95.79          | 95.65       |


## Dependency parsing

### Training

spaCy's v3 dependency parser was trained using the following [command line](https://spacy.io/api/cli#train):

```
spacy train data/sfgbank-split-json/sfgbank-train.json data/sfgbank-split-json/sfgbank-dev.json defaults.cfg -o models/spacy
```

### Evaluation

The model was evaluated with the following command line:

```
python -m spacy evaluate spacy-trained-parser data/sfgbank-split-json/sfgbank-test.json 
```

These are the scores achieved by the model:

Time      13.55 s
Words     248063
Words/s   18301
TOK       90.40
TAG       5.52
POS       0.09
MORPH     98.14
UAS       22.44
LAS       1.15
NER P     0.00
NER R     0.00
NER F     0.00
Textcat   0.00
Sent P    100.00
Sent R    9.14
Sent F    16.76
