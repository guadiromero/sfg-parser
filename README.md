# A Parser for Systemic Functional Grammar

## Preprocessing

### Conversion of constituency from XML to Penn Treebank format

The SFG data was converted from XML to Penn Treebank format by linearizing the trees with first-depth search and mapping the constituency tags. Sentences that exceeded the maximum sequence length allowed (512) were deleted (140 out of 167066), giving a total of 166926 sentences. Type this command line if you want to convert the data yourself.


Usage:

```
python preprocessing/xml2penn.py -input-dir 'path to the directory containing the XML data files to convert' -output-dir 'path to the directory where to save the converted data files' --max-len 'maximum sentence length allowed'
```

Example:

```
python preprocessing/xml2penn.py -input-dir data/sfgbank-unsplit-xml -output-dir data/sfgbank-unsplit-ptb
```

### Dataset split

The files were concatenated into three groups: 80% of the files for training, 10% for development and 10% for testing. Type this command line if you want to split the data yourself.

Usage:

```
python preprocessing/build_dataset.py -input-dir 'path to the directory containing the data files' -output-dir 'path to the directory where to save the train/dev/test datasets' -data-name 'name of the data to save' --dev-size 'int representing the size of the development set as percentage' --test-size 'int representing the size of the testing set as percentage'
```

Example:

```
python preprocessing/build_dataset.py -input-dir data/sfgbank-unsplit-ptb -output-dir data/sfgbank-split-ptb -data-name sfgbank
```

These output files at this step were used to train and evaluate the Berkeley parser.

A README is created in the output directory, listing the files contained in each split.

### Conversion of constituency Penn Treebank format to dependency CoNLL format

The train/dev/test splits were converted from the constituency Penn Treebank format to the dependency CoNLL format using [StanfordNLP](https://nlp.stanford.edu/software/lex-parser.html#Download) (see relevant [FAQ](https://nlp.stanford.edu/software/parser-faq.shtml#s) and [StanfordNLP manual](https://nlp.stanford.edu/software/dependencies_manual.pdf))

The conversion was done by using the following command for each of the splits:

```
java -cp stanford-parser-full-2018-10-17/stanford-parser.jar edu.stanford.nlp.trees.EnglishGrammaticalStructure -treeFile data/sfgbank-split-ptb/sfg-train.ptb -basic -conllx > data/sfgbank-split-conll/sfg-train.conll
```

### Conversion of dependency CoNLL format to spaCy's JSON format

The fine-grained PoS tags in each of the splits were mapped to [spaCy's coarse-grained tags](https://github.com/explosion/spaCy/blob/master/spacy/lang/en/tag_map.py), using the following script:

Usage:

```
python preprocessing/conll2spacy.py -input-file 'path to the input file' -output-file 'path to the output file'
```

Example:

```
python preprocessing/conll2spacy.py -input-file data/sfgbank-split-conll/sfgbank-train.conll -output-file data/sfgbank-split-conll-coarse/sfgbank-train.conll
```

The splits were then converted from CoNLL to JSON format by using [spaCy's converter](https://spacy.io/api/cli#convert):

```
python -m spacy convert data/sfgbank-split-conll-coarse/sfgbank-train.conll data/sfgbank-split-json/ --converter conll
```

These output files were used to train and evaluate spaCy's dependency parser

### Conversion of JSON format to raw text

This function outputs the raw text that is fed to the parsers for evaluation.

Usage:

```
python preprocessing/json2txt.py -input-file 'path to the input file in json format' -output-file 'path to the file where to save the output in txt format'
```

Example:
```
python preprocessing/json2txt.py -input-file data/sfgbank-split-json/sfgbank-test.json -output-file data/sfgbank-split-text/sfgbank-test.txt 
```

## Constituency parsing

### Training

The [BERT-based Berkeley Neural Parser](https://github.com/nikitakit/self-attentive-parser) was trained with the SFG dataset using the following command:

```
python src/main.py train --use-bert --model-path-base models/en_bert_sfg --bert-model "bert-large-uncased" --num-layers 2 --learning-rate 0.00005 --batch-size 32 --eval-batch-size 16 --subbatch-max-tokens 500 --train-path data/sfgbank-split-penn/sfgbank-train.penn --dev-path data/sfgbank-split-penn/sfgbank-dev.penn --predict-tags
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
spacy train data/sfgbank-split-json/sfgbank-train.json data/sfgbank-split-json/sfgbank-dev.json config.cfg -o models/spacy-trained-parser
```

### Evaluation

The model was evaluated with the following command line:

```
python -m spacy evaluate models/model-1 data/sfgbank-split-json/sfgbank-test.json -G > models/model-1/results.txt
```

The following different models and their accuracy scores can be found in the `models` and `results` directories, respectively.

- `results-200.txt`: Trained on a sample of 200 sentences (80:20 split for train/dev) and evaluated on those same 200 sentences.

- `results-200-dev.txt`: Trained on a sample of 200 sentences (80:20 split for train/dev) and evaluated on the dev split.

- `results-6000.txt`: Trained on a sample of 6000 sentences (5000 train/1000 dev) and evaluated on those same 6000 sentences.

- `results-6000-dev.txt`: Trained on a sample of 6000 sentences (5000 train/1000 dev) and evaluated on the dev split.

- `results-full-model-best.txt`: Best model trained on the full corpus, with a split of 80% for training, 10% for development and 10% for testing. 

- `results-full-model-final.txt`: Final model trained on the full corpus, with a split of 80% for training, 10% for development and 10% for testing.

## Parser comparison

The raw test sentences were parsed using each model. For the Berkeley parser, the following command line was used:

```
python src/main.py parse --model-path-base models/berkeley/en_bert_sfg_dev=95.79.pt --input-path data/sfgbank-split-text/sfgbank-test.txt --output-path -output-file data/sfgbank-parsed/berkeley/sfgbank-test-parsed.txt
```

The output was further transformed using StanfordNLP's constituencies to dependencies and spaCy's CoNLL to JSON converters (see "Conversion of constituency Penn Treebank format to dependency CoNLL format" and "Conversion of dependency CoNLL format to spaCy's JSON format" above). 

The following script was used for parsing the test sentences with spaCy's parser and converting them to the appropriate JSON format.

Usage:
```
python spacy_parse.py -input-file 'path to txt file containing the raw text to parse' -output-file 'path to the file where to save the output of the parser' -model 'path to the directory containing spacy's trained model'
```

Example:
```
python spacy_parse.py -input-file data/sfgbank-split-text/sfgbank-test.txt -output-file data/sfgbank-parsed/spacy/sfgbank-test-parsed.json -model models/spacy/full/model-best/
```

The two parsers were evaluated on the dependencies task, using the `eval.py` script. 

Usage:
```
python eval/eval.py -predicted 'path to the json file containing the predictions' -gold 'path to the json file containing the gold data'
```

Example:
```
python eval/eval.py -predicted data/sfgbank-parsed/spacy/sfgbank-test-parsed.json -gold data/sfgbank-split-json/sfgbank-test.json 
```

These were the scores achieved by each parser:

|          | UAS   | LAS   |
|----------|-------|-------|
| Berkeley | 95.57 | 93.99 |
| spaCy    | 91.99 | 89.84 |
