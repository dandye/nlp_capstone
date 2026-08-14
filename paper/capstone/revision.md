

Although there has been a shift in NER to using prompt-based extraction from LLMs, the need for domain-specific fine-tuning remains crucial for high-performance extraction from unstructured data. This paper has demonstrated the effectiveness of fine-tuning.

The speed, cost, precision, and privacy of local, fine-tuned, task-specific models makes them an attractive alternative to proprietary models for many use-cases, however as we have seen they do not always outperform fine-tuned smaller models. In this paper, we have shown that the span-matching architecture of GLiNER retains zero-shot generalization to entity classes the training labels never covered, while a softmax head predicts only what it saw. We also explore the trade-off between fine-tuned models and LLMs in terms of performance, speed, cost, and privacy. 

As with many neural network projects, a significant portion of the work involved the curation of high quality training and evaluation data. While there have been several attempts to create datasets for CTI NER, they have suffered from schema fragmentation and the difficulty of acquiring high-quality human annotations. 

For this project, we leveraged a heuristic dataset of 160 documents annotated for 54 entity types by a dictionary-based system using STIX indicators, IOC patterns, and regular expressions. We refer to this as our silver dataset. 

We attempted to mitigate the noise in this dataset using an ensemble approach that combined agreement between the dictionary annotator and a zero-shot LLM to produce high-quality training labels. This did not work well. We then pivoted to using a frontier LLM (Claude Sonnet) to create a gold dataset of 20 documents. 

We found that this dataset was a good starting point for fine-tuning, but it was not perfect. We found that the dictionary-based system was not able to capture all of the entity types that we were interested in, and that it was not always able to capture the correct spans of text. 

Follow on work will include using regular expressions in addition to the spans that are traditionally used.


"...yet extracting structured information from them remains
largely manual." CISA sometimes provides the structured data in-document in the form of bulleted lists of IoCs and in STIX JSON format. It would be useful to reference this in the paper. Acknowledging this as an available source of structure that we do not leverage in this paper is important.

There are some interesting challenges.

"DEEP PANDA" is an entity (a threat actor) but "deep" and "panda" are dictionary words not semantically related.
The capitalization is a great signifier but is lost in lowercasing for training.

----

I propose a modification to the Google OKF to include the known entities in the yaml frontmatter.
Should they be regex to differentiate from the non-entity usage of those words? TBD.

For example:
```yaml
...
entities-cti:
  threat-actor:
   - DEEP PANDA   
```

----

I propose a markdown convention for noting the presence of these entities and a side-car (or yaml frontmatter) data file that supplies additional information.


"...attribute the file to DEEP PANDA based on the..."
"...attribute the file to [DEEP PANDA](`ACT__DEEP_PANDA`) based on the..."


----

"proposes exhaustive entity spans, verbatim-matched back to the
source text and rejected if they do not match exactly, and further gated by
per-label span-format validators (hash length and charset, CVE/CWE/ATT\&CK
technique-ID grammar, IP/email format including defanged forms, TLP
enumeration) so structurally malformed proposals never enter the gold set."

that process was really buggy and needs rethinking.

----


# Future work

## Rule-based methods

MD5, SHA1, SHA256, and other hash formats are easily detected with regex (when artifacts don't break the strings)
Regexes for email addresses, domain names (with known TLDs) can also be used.
Pre-processing those with regex can improve the NER results significantly.


