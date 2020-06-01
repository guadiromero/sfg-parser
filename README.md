# A Systemic Functional Grammar Parser

## Constituency parsing

### Preprocessing

The SFG data was converted from XML to the Berkeley Parser format by linearizing the trees with first-depth search. Sentences that exceeded the maximum sequence length allowed by BERT (512) were deleted (185 out of 167066). Type this command line if you want to convert the data yourself.

Usage:

```
python xml_to_bkl.py -input_dir 'path to the directory containing the XML data files to convert' -output_dir 'path to the directory where to save the converted data files'
```

Example:

```
python xml_to_bkl.py -input_dir /sfgbank -output_dir /sfgbank-bkl
```

The files were concatenated in three groups: 80% of the files for training, 10% for development and 10% for testing. Type this command line if you want to split the data yourself.

Usage:

```
python build_dataset.py -input_dir 'path to the directory containing the data files' -output_dir 'path to the directory where to save the train/dev/test datasets' --dev_size 'int representing the size of the development set as percentage' --test_size 'int representing the size of the testing set as percentage'
```

Example:

```
python build_dataset.py -input_dir /sfgbank-bkl -output_dir /sfgbank-bkl-split
```


### Training

The [BERT-based Berkeley Neural Parser](https://github.com/nikitakit/self-attentive-parser) was trained with the SFG dataset using the following command:

```
python src/main.py train --use-bert --model-path-base models/en_bert_sfg --bert-model "bert-large-uncased" --num-layers 2 --learning-rate 0.00005 --batch-size 32 --eval-batch-size 16 --subbatch-max-tokens 500 --train-path data/sfgbank-bkl-split/sfgbank-bkl.train --dev-path data/sfgbank-bkl-split/sfgbank-bkl.dev
```

### Results

|                                  | TEST Recall | TEST Precision | TEST FScore |
|----------------------------------|-------------|----------------|-------------|
| CharLSTM + Penn_Treebank         | 93.20       | 93.90          | 93.55       |
| Transformer_ELMO + Penn_Treebank | 94.85       | 95.40          | 95.13       |
| Transformer_BERT + Penn_Treebank | 95.41       | 95.99          | 95.70       |
| Transformer_BERT + SFG_Treebank  | 95.51       | 95.79          | 95.65       |
