# A Systemic Functional Grammar Parser

## Base groups

### Data

The data was split into training and testing sets, using a 80:20 ratio. Annotations correspond to four base groups: Adverbial_Group, Conjunction_Group, Nominal_Group and Verbal_Group. 

The embedded structure of this layer was simplified by considering only low-level base groups. For example, for the sentence "This is harder than I thought", there is a Nominal_Group "harder than I thought" and an embedded Verbal_Group "I thought". Only the lower-level group "I thought" is considered in this case. This simplification was necessary because the NER model used in this experiment cannot handle embedded entities. In next experiments, we could try something like the "Multi-grained Named Entity Recognition" (Congying et al, 2019) approach, if it is important to keep this embedded structure. 

Another problem in the data is that whenever a word is of type="Ellipsis", it has a ConstituentRef attribute indicating the constituent to which it makes reference, but it has no StringRef attribute from which to infer the position of the word in the text. Without this information, I cannot find a way to extract the text of base groups that contain only type="Ellipsis" elements. For this reason, I simply skipped such groups for now.

### Experiment results

For this experiment, spaCy's NER model was trained with the following parameters:

Epochs = 100 

Batches = starting with a size of 4.0, and increasing size with a 1.001 factor until reaching 32.0

Results:

|                   | Precision         | Recall            | F1                |
|-------------------|-------------------|-------------------|-------------------|
| All               | 92.45114328665242 | 93.52184596175857 | 92.98341244484409 |
| Adverbial_Group   | 84.18502891076731 | 87.15418217116971 | 85.64387917329094 |
| Conjunction_Group | 90.78341013824884 | 87.81575037147103 | 89.27492447129909 |
| Nominal_Group     | 92.47136250888104 | 93.67873423156087 | 93.0711328566052  |
| Verbal_Group      | 94.31948036326457 | 95.51143457474345 | 94.91171531024466 |

### How to reproduce the results

#### Parse the data

This step is not necessary, as train_data.json and test_data.json are provided in this repository. These are the instructions if you want to parse the data from scratch.

Usage:

```
python parse_data.py -data_dir 'path to the directory containing the XML data files'
```

Example:

```
python parse_data.py -data_dir sfgbank
```

#### Run the NER model 

Usage:

```
python ner.py -train_data 'path to the file containing the training data' -test_data 'path to the file containing the testing data'
```

Example:

```
python ner.py -train_data train_data.json -test_data test_data.json
```

Additionally, use the --do_train flag if you want to train the model from scractch instead of just loading the one provided in this repository.
