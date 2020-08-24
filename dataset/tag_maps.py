from collections import OrderedDict

# map of SFG to PTB tags
# source: http://www.sfs.uni-tuebingen.de/~dm/07/autumn/795.10/ptb-annotation-guide/root.html 
TAGS_SFG2PTB = OrderedDict([
    # clause level
    ("Clause_Complex", "S"),
    ("Clause", "S"),
    # phrase level
    ("Adverbial_Group_Complex", "ADVP"),
    ("Adverbial_Group", "ADVP"),
    ("Conjunction_Group", "CONJP"),
    ("Interjection_Complex", "INTJ"),
    ("Interjection", "INTJ"),
    ("Nominal_Group_Complex", "NP"),
    ("Nominal_Group", "NP"),
    ("Verbal_Group_Complex", "VP"),    
    ("Verbal_Group", "VP"),
    ("Particle", "PRT"),
    ("Prepositional_Phrase_Complex", "PP"),
    ("Prepositional_Phrase", "PP"),
    ])

# map of SFG original to more concise tags
TAGS_SFG = {
    # clause level
    "Clause_Complex": "CLX",
    "Clause": "CL",
    # phrase level
    "Adverbial_Group_Complex": "ADVX",
    "Adverbial_Group": "ADVG",
    "Conjunction_Group": "CONJG",
    "Interjection_Complex": "INTJX",
    "Interjection": "INTJ",
    "Nominal_Group_Complex": "NGX",
    "Nominal_Group": "NG",
    "Verbal_Group_Complex": "VGX",    
    "Verbal_Group": "VG",
    "Particle": "PRT",
    "Prepositional_Phrase_Complex": "PPX",
    "Prepositional_Phrase": "PP",
}