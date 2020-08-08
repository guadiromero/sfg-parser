# PV vs Berkeley constituency evaluation

We used the same evaluation script and corpora from Costetchi (2019) to test the performance of Parsimonious Vole against the Berkeley parser trained on the SFG corpus. To evaluate the Berkeley parser, we preprocessed the text with `tokenize.py`, parsed the constituency trees and extracted constituent spans from them with `ptb2mcg.py`. We deleted duplicates from the gold annotated spans and the spans predicted by Parsimonious Vole with `simplify_gold.py`. We only considered constituency annotations and ignored the SFG features. Below are the results for the OE and OCD corpora as well as an average of both.

|                    | PV Precision        | PV Recall          | PV F1              | Bkl Precision      | Bkl Recall         | Bkl F1             |
|--------------------|---------------------|--------------------|--------------------|--------------------|--------------------|--------------------|
| OE average         | 0.501618645         | 0.971548054        | 0.657268265        | 0.544210148        | 0.937520171        | 0.687475324        |
| OCD average        | 0.61451527697       | 0.90668431018      | 0.73253987998      | 0.76316642293      | 0.94605738557      | 0.84476653326      |
| TOTAL average      | 0.55806696098       | 0.93911618209      | 0.69490407249      | 0.65368828546      | 0.94178877828      | 0.76612092863      |
