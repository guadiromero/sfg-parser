from collections import OrderedDict

# map of SFG original to more concise tags
TAGS_SFG = OrderedDict([
    # clause level
    ("Clause_Complex", "CLX"),
    ("Clause", "CL"),
    # phrase level
    ("Adverbial_Group_Complex", "ADVX"),
    ("Adverbial_Group", "ADVG"),
    ("Conjunction_Group", "CONJG"),
    ("Interjection_Complex", "INTJX"),
    ("Interjection", "INTJ"),
    ("Nominal_Group_Complex", "NGX"),
    ("Nominal_Group", "NG"),
    ("Verbal_Group_Complex", "VGX"),    
    ("Verbal_Group", "VG"),
    ("Particle", "PRT"),
    ("Prepositional_Phrase_Complex", "PPX"),
    ("Prepositional_Phrase", "PP"),
    ])