Contents lists available at ScienceDirect
Expert Systems With Applications
journal homepage: www.elsevier.com/locate/eswa
LETNER: Label-EﬃcienT  named entity recognition for cyber threat 
intelligence
Yue Wang
 a,∗, Duoyi Zhang
 a, Md Abul Bashar
 a, Mahinthan Chandramohan b, 
Richi Nayak
 a
a School of Computer Science, Centre for Data Science, Queensland University of Technology, 4000, Brisbane, Queensland, Australia
b Oracle Labs, 4000, Brisbane, Queensland, Australia
a r t i c l e  i n f o
Keywords:
Cyber threat intelligence
Span-based NER
Label-eﬃciency
Data annotation
Gating mechanism
Orthogonal regularisation
Decision making
 a b s t r a c t
Named Entity Recognition (NER) from open-source security reports has become a crucial task in Cyber Threat 
Intelligence (CTI) to enable knowledge extraction and support proactive cyber defence. However, existing fully 
supervised NER approaches struggle to adapt to the dynamic and linguistically complex nature of CTI text. To 
address these challenges, we propose Label-Eﬃcient  Named Entity Recognition (LETNER), a model designed to 
handle multi-token, sparsely distributed, and ﬁne-grained CTI entity patterns while maintaining low annotation 
demand. LETNER leverages Convolutional Neural Networks (CNNs) and a gating mechanism to learn dynamic 
span-based representations, and introduces an orthogonal regularisation to align entity-span relationships in a 
shared metric space for eﬀective similarity-based inference. Furthermore, a cost-aware evaluation framework is 
presented to jointly quantify annotation eﬀort and model performance, providing practical insights for decision-
making in low-resource settings. Experimental results on a complex CTI dataset containing 22 ﬁne-grained entity 
classes show that LETNER signiﬁcantly outperforms baseline models, achieving high performance using only 10% 
of the annotated data.
1.  Introduction
In recent years, the growing frequency and sophistication of cyber 
threats and corresponding incidents has underscored the urgent need for 
proactive, data-driven cyber defence  (Wang et al., 2023). Cyber Threat 
Intelligence (CTI), which involves collecting and extracting evidence 
based knowledge about cyber threats plays a pivotal role by enabling 
organisations to identify, analyse, and anticipate threats targeting their 
digital infrastructure (Rahman et al., 2020). A fundamental component 
of CTI is the knowledge extraction of key entities from unstructured doc-
uments, such as malware names, threat actions, Indicators of Compro-
mise (IOCs), and Tactics, Techniques, and Procedures (TTPs) (Mahboubi 
et al., 2024; Zhou et al., 2018). Accurately recognising these entities 
is critical for understanding threat actor’s behaviours, constructing CTI 
knowledge bases, and supporting timely responses to potential cyber 
incidents.
The above mentioned knowledge extraction process is commonly 
achieved through Named Entity Recognition (NER), a core Natural 
Language Processing (NLP) task that identiﬁes and categorises mean-
ingful entities within text (Li et al., 2020), as shown in Fig. 1. Re-
∗ Corresponding author.
 E-mail addresses: y355.wang@hdr.qut.edu.au (Y. Wang), d25.zhang@qut.edu.au (D. Zhang), m1.bashar@qut.edu.au (M.A. Bashar), 
mahin.chandramohan@oracle.com (M. Chandramohan), r.nayak@qut.edu.au (R. Nayak).
cent advances in deep learning have introduced powerful NER mod-
els, including token-classiﬁcation architectures that leverage pre-trained 
transformers to classify tokens into entity labels (Evangelatos et al., 
2021; Shin et al., 2021), and sequence-labelling models that use Con-
ditional Random Fields (CRFs) to enforce dependencies under the BIO 
(Begin-Inside-Outside) labelled sequence (Ahmed et al., 2024; Dioní-
sio et al., 2019; Finkel et al., 2005; Huang et al., 2015). Meanwhile, 
metric learning-based NER approaches (Chen et al., 2023; Yang & 
Katiyar, 2020; Zaratiana et al., 2024) have emerged, aiming to learn 
semantic relationships between tokens and labels in a shared met-
ric space and enabling similarity-based inference even with limited
supervision.
Despite these advances, applying existing NER approaches to CTI 
data remains challenging due to both evolving nature of cyber threats 
and the domain speciﬁc linguistic patterns. The CTI landscape changes 
continuously as new malware families, threat groups, and attack tech-
niques emerge (Mahboubi et al., 2024). This constant evolution makes it 
infeasible to maintain a fully supervised dataset, as unseen entity types 
and naming conventions appear faster than annotated corpora can be 
updated. Furthermore, CTI annotation requires expert domain knowl-
https://doi.org/10.1016/j.eswa.2026.132470
Received 12 December 2025; Received in revised form 24 February 2026; Accepted 13 April 2026
Expert Systems With Applications 324 (2026) 132470 
Available online 15 April 2026 
0957-4174/© 2026 The Author(s). Published by Elsevier Ltd. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

Y. Wang et al.
Fig. 1. Example of CTI NER task, derived from the APTNER dataset (Wang et al., 
2022).
edge, making it labour-intensive, costly, and diﬃcult  to scale (Wang 
et al., 2023, 2025).
CTI text also exhibits unique linguistic complexity: entities often 
span multiple tokens (e.g., remote code execution, command and control 
server), and the meaning of entity labels often require domain knowl-
edge to interpret and may overlap semantically across entity classes 
(e.g., TOOL, MAL, ACT). Fully supervised NER models trained on histor-
ical data therefore struggle to generalise to new or shifting terminology, 
leading to degraded performance in real-world applications. These chal-
lenges highlight the urgent need for label-eﬃcient  NER models that can 
achieve strong generalisation with minimal annotation while adapting 
to emerging threat contexts.
Label eﬃciency,  originally introduced in computer vision, refers to 
a model’s ability to generalise eﬀectively with a minimal amount of la-
belled data (Luo et al., 2017; Shen et al., 2023). In this paper, we ex-
tend this concept to evaluate NER models in terms of their trade-oﬀ 
between performance and annotation demand, as illustrated in Fig. 2. 
Consider two supervised NER models: Model 1 is trained with 80% of 
annotated data, while Model 2 is trained with only 60%. If both mod-
els achieve comparable performance, Model 2 can be considered more 
label-eﬃcient,  as it attains similar accuracy with fewer labelled exam-
ples. This property is particularly valuable in CTI NER, where annotation 
is costly, data distribution shifts rapidly, and timely model adaptation 
is critical for proactive cyber defence.
In this paper, we propose Label-EﬃcienT  Named Entity Recognition 
(LETNER), a novel model designed to address the linguistic complexity 
in CTI text. LETNER integrates a dual-encoder metric learning archi-
tecture, a span-CNN-Gate module and an orthogonal regularisation to 
enhance eﬀective entity-span alignment and entity recognition while 
archives great label eﬃciency.  Speciﬁcally, our key contributions in-
clude:
1. We introduce LETNER, a label-eﬃcient  NER model that leverages 
metric learning to eﬀectively learn entity-span relationships in a 
shared metric space, achieving strong performance with only 10% 
of the training data, reducing annotation demands in evolving CTI 
environments.
2. LETNER integrates three novel components, namely, bi-encoder, 
span-CNN-Gate, and orthogonal regularisation, to eﬀectively address 
domain-speciﬁc entity dependencies and entity-label alignment chal-
lenges in security-related text.
Fig. 2. Label eﬃciency  concept illustration: A model trained on 60% labelled 
data achieves performance comparable to a model trained on 80% labelled data 
(𝑝1 ≈ 𝑝2).
3. LETNER outperforms Flair NER (Akbik et al., 2019) by 11.8% in F1-
score while using only 10% of the training data, demonstrating its 
eﬀectiveness for real-world CTI applications.
4. We develop a label eﬃciency  evaluation based on the Point of Dimin-
ishing Returns (PoDR) law (Shephard & Färe, 1974), systematically 
analysing the cost-performance trade-oﬀ across varying annotation 
levels (10-80%). This is the ﬁrst comprehensive study of label eﬃ-
ciency in CTI-NER.
2.  Background and related works
Building on the motivation for label-eﬃcient  NER in the dynamic 
CTI landscape, this section reviews prior works in both CTI-speciﬁc and 
general-domain NER research. We ﬁrst summarise the existing datasets 
used for CTI NER tasks and their domain-speciﬁc challenges, followed 
by a review of existing NER approaches applied in cyber security con-
texts. Finally, we discuss advances in general-domain NER that have 
the potential to inform CTI applications. This discussion highlights cur-
rent research gaps and positions the proposed LETNER model within the 
broader development of label-eﬃcient  NER.
2.1.  NER datasets in the CTI domain
Due to data privacy restrictions and annotation challenges in the 
security domain, only a limited number of open-source NER datasets 
exist for CTI, each adopting distinct annotation schemes and present-
ing unique challenges. The ﬁrst publicly available CTI NER dataset, 
DNRTI (Wang et al., 2020), uses the BIOS format and contains 14 entity 
classes, where the “S” label denotes single-token entities, in addition 
to the Beginning-Inside-Outside (BIO) labelling scheme. A more recent 
dataset, APTNER (Wang et al., 2022), provides a large-scale benchmark 
for CTI research, sourced from Advanced Persistent Threat (APT) reports 
across multiple platforms. APTNER includes 22 entity classes annotated 
in BIOES format, where the “E” label explicitly marks the end of an 
entity to better delineate boundaries between closely related entities.
Compared with general-domain NER, which typically includes up to 
six common classes such as Person (PER), Organisation (ORG), and Lo-
cation (LOC) (Honnibal & Montani, 2020), CTI NER is inherently more 
complex. Models must recognise a much larger number of ﬁne-grained, 
semantically related entity types (e.g., up to 22 in APTNER). These en-
tity classes often suﬀer from severe class imbalance due to the long and 
sparse nature of CTI documents. Moreover, the semantic meaning of 
CTI labels is often non-intuitive and requires domain expertise to inter-
pret. For instance in APTNER (Wang et al., 2022), the label “APT” refers 
to Advanced Persistent Threats, while “ACT” denotes attacker actions 
or behaviours. Such subtle semantic distinctions make label interpreta-
tion ambiguous, posing additional challenges for both human annota-
tors and NER models to align tokens with their correct entity classes. 
Consequently, CTI NER task require careful model design to handle the 
domain speciﬁc challenges and linguistic patterns.
2.2.  Existing NER methods for the CTI domain
Most existing deep learning-based NER approaches in the CTI 
domain follow traditional token-classiﬁcation or sequence-labelling 
paradigms under a fully supervised setting (Ahmed et al., 2024; Dionísio 
et al., 2019, 2020; Evangelatos et al., 2021; Shin et al., 2021). In token-
classiﬁcation approaches, token embeddings are ﬁrst derived from pre-
trained transformers, followed by fully connected layers that directly 
assign each token to a predeﬁned label. Evangelatos et al. (2021) con-
ducted a comparative study by ﬁne-tuning various transformer-based 
models on the DNRTI dataset (Wang et al., 2020), treating NER as a 
token-classiﬁcation task without explicitly modelling entity sequence 
dependencies. Their results showed that when given suﬃcient  labelled 
dataset, BERT-base and XLNet achieved satisfactory performance among 
evaluated baselines.
Expert Systems With Applications 324 (2026) 132470 
2 

Y. Wang et al.
On the other hand, most sequence-labelling based NER methods, aim 
to capture sequential dependencies through Conditional Random Fields 
(CRFs) integrated with neural encoders such as BiLSTMs or transform-
ers (Finkel et al., 2005; Huang et al., 2015). For example, Dionísio et al. 
(2019, 2020) employed a BiLSTM-CRF model in a multi-task learning 
framework to detect CTI entities from a self-collected Twitter dataset. In 
this model, the BiLSTM component learns character-level embeddings, 
while the CRF layer enforces sequence consistency according to the BIO 
labelling scheme. More recently, Ahmed et al. (2024) proposed a joint 
NER and Relation Extraction (RE) framework to simultaneously identify 
entities and their relationships from unstructured cyber threat reports. 
Using a self-constructed dataset, they evaluated several deep learning 
models. Their ﬁndings indicated that a RoBERTa-BiGRU-CRF model, 
which combines transformer-derived token embeddings with CRF-based 
sequence constraints, achieved the best results among the tested base-
lines.
While these token-classiﬁcation and sequence-labelling methods 
have contributed to progress in CTI NER, they heavily depend on fully 
supervised data to learn sparsely distributed entity classes indepen-
dently. This reliance on large annotated datasets is impractical in the 
fast-evolving CTI landscape, where maintaining up-to-date training data 
is infeasible. Consequently, such models struggle to adapt to emerg-
ing threats in real world applications, highlighting the need for label-
eﬃcient  NER approaches that can operate eﬀectively with limited an-
notation.
2.3.  Advancements in general-domain NER and their potentials for CTI
Recent advancements in general-domain NER have expanded be-
yond traditional token-classiﬁcation and sequence-labelling methods, 
introducing new paradigms with strong potential for CTI applications. 
Metric learning has shown particular promise due to its inherently label-
eﬃcient  design. Instead of learning independent decision boundaries for 
each entity class from large annotated datasets, metric learning focuses 
on learning the semantic relationships between entity tokens and their 
corresponding labels in a shared metric space (Kaya & Bilge, 2019). 
Within this space, positive token-entity pairs (which belonging to the 
same class) are drawn closer together, while negative ones are pushed 
further apart. This relational learning objective enables models to gener-
alise eﬀectively from limited supervision, operating successfully in few-
shot or even zero-shot settings (Chen et al., 2023; Yang & Katiyar, 2020). 
Although this paradigm has been widely adopted in general-domain 
NER, its application to CTI remains challenging due to the unique lin-
guistic characteristics of cyber security text. These include the ambigu-
ity of domain-speciﬁc labels (e.g., APT vs. ACT), and the large number 
of ﬁne-grained and sparsely distributed entity classes, which can lead 
to misalignment between correct token and label representations in the 
learnt space.
Another promising line of research is span-based NER, which mod-
els entities as continuous spans of tokens rather than independent to-
ken predictions (Zaratiana et al., 2022, 2024). Unlike token-level ap-
proaches, span-based models enumerate potential token sequences and 
perform classiﬁcation at the span level, enabling more eﬀective detec-
tion of multi-word entities, which are frequently observed in CTI text, 
such as “remote code execution”. GLiNER (Zaratiana et al., 2024), for 
instance, is a metric-learning-based NER model that learns semantic re-
lationships between spans and entity labels within a shared latent space, 
achieving state-of-the-art performance on general-domain benchmarks. 
However, GLiNER constructs span embeddings primarily through con-
catenation or mean pooling of boundary tokens, without explicitly mod-
elling intra-span dependencies. This limitation becomes critical in CTI, 
where entities are often long, noisy, irregular, and semantically com-
plex. As a result, span representations learned by direct aggregation 
methods may fail to capture meaningful internal token interactions, re-
ducing their eﬀectiveness for CTI text.
Meanwhile, generative methods using open-source Large Lan-
guage Models (LLMs) such as the Llama (Dubey et al., 2024) and 
DeepSeek (Guo et al., 2025) have demonstrated impressive generalisa-
tion capabilities without task-speciﬁc ﬁne-tuning. Despite their versatil-
ity, these models pose signiﬁcant barriers to practical CTI deployment, 
including high computational costs, inconsistent structured outputs, and 
the risk of generating hallucinated or unveriﬁable information.
Despite these advancements, Table 1 highlights several gaps that 
existing methods, whether metric-learning-based, span-based, or LLM-
driven, fail to address for CTI NER: (1) maintaining label eﬃciency  un-
der limited supervision, (2) accurately identifying entities with variable 
span lengths, and (3) distinguishing among a large set of ﬁne-grained 
and semantically related classes. (4) remain lightweight in model size 
for local deployment. These gaps motivate the development of the pro-
posed LETNER model, introduced in the next section, which is explicitly 
designed to be label-eﬃcient  and tailored to the linguistic and structural 
complexity of CTI text.
3.  Methodology
The section introduces the proposed LETNER model. We start with 
the problem deﬁnition, then explain each core component of LERNER 
model architecture, followed by the model training, inference and label 
eﬃciency  evaluation.
3.1.  Problem deﬁnition: Span-based and label-eﬃcient  NER
Let 𝐷 = {𝐷train, 𝐷test} be a corpus consisting of sentences, where 
each sentence 𝑋 = {𝑥1, 𝑥2, … , 𝑥𝑛} is a sequence of 𝑛 tokens (e.g., words). 
In the training set 𝐷train, each sentence is annotated with token-level la-
bels 𝑙 = {𝑦1, 𝑦2, … , 𝑦𝑛}, where each label 𝑦 ∈  ∪ 𝑂 denotes either an 
entity class in   or the non-entity class 𝑂. The set   includes prede-
ﬁned entity classes relevant to CTI, such as malware, vulnerabilities, 
and locations.
Span-based NER. A traditional NER model assigns a label to 
each token in a sentence, producing a predicted label sequence ̂ 𝑦=
{ ̂ 𝑦1, ̂ 𝑦2, … , ̂ 𝑦𝑛}. In the context of span-based prediction for NER, instead 
of assigning individual token labels, the model is trained to recognise 
continuous spans 𝑠𝑖∶𝑖+𝑗 of tokens that collectively form entities, where 
𝑖 represents the starting position of the span (𝑖𝑡ℎ token) and 𝑗 indicates 
the ending position (𝑗𝑡ℎ token). For example, Under BIO tagging, a la-
bel sequence such as 𝑙 = {𝑂, 𝑂, 𝐵-𝑡, 𝐼-𝑡, 𝐼-𝑡, 𝐼-𝑡} uniquely deﬁnes the span 
𝑠2∶5 of type 𝑡. This formulation enables the model to capture entities 
of variable length while preserving contextual coherence. In CTI text, 
entity mentions such as malware names, attack campaigns, and threat 
actors frequently consist of multi-token expressions with complex struc-
tures. Span-based prediction therefore provides a more robust represen-
tation for extracting such entities. In LETNER, this capability is realised 
through the Span-CNN-Gate module introduced in Section 3.2.2.
Label-eﬃcient  NER. While span-based NER addresses structural 
challenges in CTI entity recognition, real-world applications face an ad-
ditional resource challenge: obtaining high-quality security-domain an-
notations is expensive and time-consuming. In practical CTI settings, 
the volume of labelled data directly determines annotation eﬀort and 
deployment cost, while performance improvements tend to diminish 
as additional annotations are collected. This behaviour reﬂects the 
law of diminishing returns, a principle describing reduced marginal 
gains as resource investment increases (Shephard & Färe, 1974). There-
fore, beyond maximising NER recognition accuracy, a label-eﬃcient  
model should achieve strong performance on 𝐷test with minimal la-
belled data. In other words, let |𝐷train| denote the size of the train-
ing set. Label-eﬃcient  NER refers to the ability of a model to achieve 
comparable performance on 𝐷test even when trained with a reduced 
subset 𝐷′
train ⊂ 𝐷 train where |𝐷′
train| ≪ |𝐷train|. We address this objec-
tive through a metric-learning-based training strategy designed to gen-
eralise from sparse annotations, as described in Section 3.3. A formal 
Expert Systems With Applications 324 (2026) 132470 
3 

Y. Wang et al.
Table 1 
Gaps in existing NER methods under diﬀerent categories.
 Method  Category  Label-eﬃcient  Multi-token span  Fine-grained classes  Lightweight
 BiLSTM-CRF (Dionísio et al., 2019, 2020)  Sequence labelling × × × ✓
 BERT-based (Evangelatos et al., 2021)  Token classiﬁcation × × × ✓
 RoBERTa-BiGRU-CRF (Ahmed et al., 2024)  Sequence labelling × × × ✓
 GLiNER (Zaratiana et al., 2024)  Metric learning ✓ ✓ × ✓
 LLMs (Dubey et al., 2024; Guo et al., 2025)  Generative methods ✓ × × ×
Fig. 3. Overall architecture of the proposed LETNER model.
cost-performance evaluation framework based on label eﬃciency  is in-
troduced in Section 3.5.
3.2.  Model architecture
The proposed model, illustrated in Fig. 3, is built on metric learning 
principles which aims to project tokens from a sequence and semantic 
entity label descriptions into a shared metric space while leveraging lim-
ited labelled data to optimise positive and negative token-entity pairs. 
The architecture consists of three main components: (1) a dual-encoder 
for feature extraction, (2) two neural networks to reﬁne entity and span 
representations, and (3) a similarity module to compute similarity matri-
ces for model training and inference. Each component is detailed below.
3.2.1.  Dual-encoder
Diﬀerent from existing models (Zaratiana et al., 2024) that use the 
same BERT encoder to extract features for both token sequences and en-
tity labels, we introduce a dual-encoder design where token-level em-
beddings and sentence-level entity label embeddings are extracted sep-
arately This allow LETNER to capture the semantic relationships be-
tween tokens and their corresponding entity labels in a shared latent 
space. This explicit alignment is particularly beneﬁcial in the CTI do-
main, where many entity labels-such as APT and ACT-are semantically 
ambiguous and context-dependent. By integrating dual encoders with 
a metric-learning objective, LETNER encourages tokens to be closer to 
the correct entity labels while pushing apart unrelated ones, improving 
discriminative power and robustness in scenarios with large numbers of 
ﬁne-grained, closely related CTI entity classes.
Inputs: The model takes two primary inputs: (1) a text sequence 
containing tokens to be classiﬁed and (2) a set of entity labels (e.g., 
APT, MAL, ACT, LOC) to be identiﬁed within the text. Unlike general-
domain NER labels (e.g., Location, Person, Date), CTI entity labels are 
more complex and often require domain knowledge to interpret, such 
as MAL (Malware), APT (Advanced Persistent Threat), and ACT (threat 
actions for malicious activities). To address this, we enrich entity labels 
by converting them into semantic descriptions, enabling the model to 
better capture the relationships between tokens and entities within a 
shared metric space  (Chen et al., 2023).
Speciﬁcally, we used domain expertise to deﬁne semantic descrip-
tions for entity labels based on established CTI knowledge bases, such 
as STIX 1 and MITRE ATT&CK.2 For each entity label, domain experts 
leverages an LLM (e.g. ChatGPT 3) to generate a structured semantic de-
scription of approximately 128 tokens, which is optimised for Sentence-
BERT (Reimers & Gurevych, 2019). We employ prompt engineering Wu 
et al. (2025) to instruct the LLM to simulate a threat intelligence analyst 
generating descriptions informed by real-world examples (i.e. training 
data) and CTI frameworks (i.e. MITRE ATT&CK and STIX). Domain ex-
perts then carefully review each label description to ensure accuracy 
1 https://stixproject.github.io/
2 https://attack.mitre.org/
3 https://chatgpt.com/
Expert Systems With Applications 324 (2026) 132470 
4 

Y. Wang et al.
and relevance. This approach provides two key beneﬁts: it ensures a 
consistent format across multiple entity descriptions and reduce manual 
eﬀort while preserving high-quality label deﬁnitions. For example, the 
MAL entity label (from the APT dataset) is transformed into the follow-
ing description: “Software intended for malicious purposes, including 
commercial, custom, or open-source. Examples: PlugX, CHOPSTICK.”
Feature extraction: The LETNER architecture employs a dual-
encoder architecture to process the text sequence and entity descrip-
tions separately. The TokenEncoder captures the semantic features of 
the text sequence at the token level, while the EntityEncoder encodes 
entity descriptions (from the previous step) at the sentence level. This 
design preserves structural distinctions between tokens and entity de-
scriptions, enabling better alignment in shared representation space.
TokenEncoder: For a token-level text sequence 𝑋 = {𝑥1, 𝑥2, … , 𝑥𝑛}, 
we employ a pre-trained TokenEncoder model, such as BERT, to obtain 
contextual embeddings for each token:
𝐻 = BERT(𝑋) = { ℎ1, ℎ2, … , ℎ𝑛}, ℎ 𝑖 ∈ ℝ𝑑
where ℎ𝑖 represents the contextual embedding for token 𝑥𝑖 and 𝑑 denotes 
the hidden dimension size.
EntityEncoder: Since each entity label has been converted into a short 
semantic description in the previous step, it can be encoded into a vec-
tor using a BERT-based entity encoder, such as SentenceTransformers 
(SBERT) (Reimers & Gurevych, 2019), to eﬀectively capture sentence-
level semantics. Unlike standard BERT models that rely on the [CLS] to-
ken, SBERT undergoes sentence-level pretraining based on contrastive 
learning, making it more eﬀective for encoding entity descriptions. Since 
SBERT models are compact, the dual-encoder setup maintains compu-
tational eﬃciency  while allowing ﬂexibility for real-world deployment, 
enabling seamless integration of diﬀerent SBERT variants. Additionally, 
because class descriptions remain ﬁxed, their embeddings can be pre-
computed and stored, further reducing computational overhead. Given 
an entity description 𝑐𝑘 𝑇𝑘 (which may consist of one or more sentences), 
the entity embedding is computed as:
𝑣𝑘 = EntityEncoder(𝑇𝑘), 𝑣 𝑘 ∈ ℝ𝑑𝑠
where 𝑑𝑠 represents the sentenceBERT’s output dimension.
3.2.2.  Representations reﬁnement
After extracting features using the dual-encoder, we introduce two 
neural modules to reﬁne entity and token representations separately. 
A feedforward neural network is applied to project entity embeddings 
into a target metric space, while a Span-CNN-Gate module is designed 
to convert token embeddings into span representations within the same 
metric space.
The introduction of the Span-CNN-Gate module is motivated by the 
inherent challenges of CTI text. In cyber security corpora, entity men-
tions (such as malware names, tools, and threat actions) often span mul-
tiple tokens and exhibit structured patterns. Simple token-level embed-
dings may fail to capture these local n-gram dependencies, while naïve 
span aggregation can introduce noisy or irrelevant context. To address 
this, we leverage CNNs to learn multi-token patterns eﬃciently  and in-
tegrate a gating mechanism to selectively ﬁlter out irrelevant features, 
ensuring robust and semantically meaningful span representations.
Entity representations: To further process the entity embeddings 
𝑣𝑘, we apply a feed forward neural network 𝑓entity to obtain reﬁned 
entity representations:
𝑒𝑘 = 𝑓entity(𝑣𝑘), 𝑒 𝑘 ∈ ℝ𝑑ℎ
where 𝑑ℎ is a hyperparameter representing the hidden dimension of the 
entity representations in the target metric space.
Span representations: Span-CNN-gate. This module combines con-
volutional neural networks (CNNs) and a gating mechanism (Zhang 
et al., 2024) to learn local token dependencies while ﬁltering out noise 
eﬀectively. We adopted CNNs to learn n-gram patterns in CTI data, 
where malware names and attack indicators often follow structured 
token patterns. For example: “Cobalt Strike(TOOL) appears to be one 
of BRONZE PRESIDENT(APT)’s preferred remote access tools”. In this 
case, malware names, tools, and tactics frequently span multiple tokens, 
which CNNs can eﬀectively capture through convolutional operations. 
However, CNNs may also introduce irrelevant dependencies due to their 
broad span coverage (generated due to the convolution operation among 
all possible span combinations), leading to noisy representations. To ad-
dress this challenge, we integrate a gating mechanism that selectively ﬁl-
ters out noisy dependencies (Zhang et al., 2024, 2023) and learns more 
robust span representations. Fig. 4 illustrates the proposed Span-CNN-
Gate module to compute span representations for a span starting at to-
ken 𝑥𝑖 and ending at 𝑥𝑖+𝑗 .
Each token 𝑖 is represented by an embedding spanning size 𝑗, de-
noted as ℎ𝑖∶𝑖+𝑗 ∈ ℝ𝑑ℎ×𝑗 . To capture n-gram patterns, we apply a set of 
CNN ﬁlters with diﬀerent kernel sizes, where each kernel of window 
size 𝑗 captures j-gram semantic features while simultaneously learning 
gating scores. Window size 𝑗 is a hyper-parameter deﬁned by the user 
to capture 𝑗-gram patterns from the dataset.
The semantic representation 𝑠𝑠
𝑖∶𝑖+𝑗 is computed using a convolution 
operation with kernel 𝑤(𝑗)
𝑠 ∈ ℝ𝑗 and bias 𝑏(𝑗)
𝑠 ∈ ℝ𝑗 , followed by a Tanh 
activation to introduce non-linearity. 
𝑠𝑠
𝑖∶𝑖+𝑗 = 𝑇 𝑎𝑛ℎ(ℎ𝑖∶𝑖+𝑗 ∗ 𝑤(𝑗)
𝑠 + 𝑏(𝑗)
𝑠 ) (1)
Similarly, a gating function is applied through another convolution 
layers using kernel 𝑤(𝑗)
𝑔  and bias 𝑏(𝑗)
𝑔 , followed by a Sigmoid activation 
to selectively ﬁlter out less informative features. 
𝑠𝑔
𝑖∶𝑖+𝑗 = 𝑆𝑖𝑔𝑚𝑜𝑖𝑑 (ℎ𝑖∶𝑖+𝑗 ∗ 𝑤(𝑗)
𝑔 + 𝑏(𝑗)
𝑔 ) (2)
The ﬁnal span representation 𝑠𝑖∶𝑖+𝑗 is obtained through element-wise 
multiplication of the semantic and gating outputs, preserving relevant 
spans while ﬁltering noises. 
𝑠𝑖∶𝑖+𝑗 = 𝑠𝑠
𝑖∶𝑖+𝑗 ⊙ 𝑠𝑔
𝑖∶𝑖+𝑗 (3)
The resulting feature matrix 𝑠𝑖∶𝑖+𝑗 ∈ ℝ𝑑ℎ×𝑀 , where 𝑀 is the number 
of diﬀerent kernel sizes used, enables the model to ﬂexibly capture hier-
archical token interactions while dynamically ﬁltering irrelevant infor-
mation. In summary, CNN-gate transforms token-level embeddings into 
span-level representations, facilitating robust entity span recognition for 
NER.
3.2.3.  Similarity module
The similarity module serves as the core component for classifying 
spans into entity classes in the LERNER model. The purpose is to quan-
tify the semantic alignment between span representations and entity 
representations. This is achieved through a similarity score computed 
via a dot product. Speciﬁcally, the similarity score between a span rep-
resentation 𝑠𝑖∶𝑗 and an entity representation 𝑒𝑘 is computed by the fol-
lowing equation:
sim(𝑒𝑘, 𝑠𝑖∶𝑖+𝑗 ) = 𝑒𝑘 ⋅ 𝑠𝑖∶𝑖+𝑗 (4)
This results in a similarity matrix 𝑆 ∈ ℝ𝐾×𝑁 , where 𝐾 represents the 
total number of entity representations and 𝑁 denotes the total number 
of span representations in a batch. This matrix captures the semantic re-
lationships between all entity-span representations in the metric space, 
serving as the foundation for both training and inference, as detailed in 
the following subsections.
3.3.  Model training
Training LETNER eﬀectively requires balancing the dual objectives 
of correctly associating spans with entity labels and maintaining a dis-
criminative embedding space. To this end, we leverage a limited set of 
labelled ground-truth data (one-hot encoded) to optimise the similarity 
matrix sim(𝑒𝑘, 𝑠𝑖∶𝑖+𝑗 ) produced by the Similarity Module. Each entry in 
this matrix captures the likelihood that a span 𝑠𝑖∶𝑖+𝑗 corresponds to an 
Expert Systems With Applications 324 (2026) 132470 
5 

Y. Wang et al.
Fig. 4. Graphical illustration of the Span-CNN-Gate. Using a stride size of 1 and a maximum window size 𝑗 (ranging from 1 to 𝑗), the CNN layers generate contiguous 
span features from unigrams to 𝑗-grams, enabling the model to capture variable-length entity mentions.
entity 𝑒𝑘: a value of 1 indicates a correct mapping (positive pair), while 
0 denotes an incorrect mapping (negative pair). The overarching goal 
is to maximise similarity for true entity-span pairs while ensuring clear 
separation between diﬀerent entity classes.
A fundamental challenge in metric learning is the risk of prototype 
collapse, where learned entity embeddings become too similar, reduc-
ing the model’s ability to discriminate between classes (Gautam et al., 
2022). In CTI, this problem is particularly severe because some entity 
classes ( e.g., malware names, attack tools, and threat actions ) often 
share overlapping semantics. If the embeddings of these classes are not 
well-separated, mis-classiﬁcation becomes more likely. Our key contri-
bution addresses this issue: we introduce a soft orthogonal loss during 
model training to explicitly encourage diversity among entity embed-
dings, enhancing the model’s discriminative power while retaining ﬂex-
ibility.
3.3.1.  Enforcing intra-class similarity through classiﬁcation
We use a binary classiﬁcation loss to align the similarity matrix with 
one-hot encoded ground-truth labels, as in previous work (Zaratiana 
et al., 2024). The binary classiﬁcation loss function is formulated as:
BCE = − 1
|𝑃 |
∑
(𝑒𝑘,𝑠𝑖∶𝑖+𝑗 )∈𝑃
log(𝜎(sim(𝑒𝑘, 𝑠𝑖∶𝑖+𝑗 ))) − 1
|𝑁|
∑
(𝑒𝑘,𝑠𝑖∶𝑖+𝑗 )∈𝑁
log(1 − 𝜎(sim(𝑒𝑘, 𝑠𝑖∶𝑖+𝑗 ))) (5)
where 𝑃 and 𝑁 represent positive (1) and negative pairs from the 
ground truth information (0) respectively, and 𝜎 is the Sigmoid func-
tion, ensuring outputs are in the probability [0,1] range. Since BCE loss 
only requires binary supervision, it allows LETNER to leverage limited 
annotations eﬃciently  while still learning meaningful entity-span rela-
tionships.
3.3.2.  Orthogonal regularisation to improve entity diversity
To preserve diversity among learnt entity representations, we intro-
duce a novel trace-based soft orthogonality constraint. This regularisa-
tion technique minimises correlations between entity representations, 
ensuring they remain distinct within the learned metric space (Luong 
et al., 2022). Unlike strict orthogonality constraints, the soft orthogonal-
ity constraint allows more ﬂexibility in representation learning, gradu-
ally guiding entity embeddings apart without sacriﬁcing variability. The 
trace-based soft orthogonality loss function is deﬁned as:
orth =
∑ ||||
Tr
(
̄𝜙𝑘
𝑇 ̄𝜙𝑘 − 𝐼𝑀
) ||||
(6)
where ̄𝜙𝑘 represents the mean-centred entity representations, and 𝐼𝑀 is 
an 𝑀 × 𝑀 identity matrix. The trace function Tr(⋅) captures the sum of 
eigenvalues, capturing the variance within all present entity represen-
tations. By ensuring this trace remains close to the identity matrix sum, 
we promote diversity of learnt entity representations while maintain-
ing ﬂexibility in the learned metric space. This regularisation technique 
is particularly eﬀective for CTI NER, where entity classes often share
Expert Systems With Applications 324 (2026) 132470 
6 

Y. Wang et al.
semantic similarities. By preventing entity representations from collaps-
ing into overly similar representations, this approach improves entity 
diﬀerentiation, leading to improved NER performance.
3.3.3.  Overall loss function
The overall objective function is expressed as a weighted combina-
tion of the binary classiﬁcation loss and the orthogonal regularisation 
loss:
 = 𝛽BCE + (1 − 𝛽)orth (7)
where 𝛽 is a hyper-parameter that balances the contribution of two 
losses. This ensures the model maintains both intra-class coherence (by 
strengthening correct entity-span relationships) and inter-class diversity 
(by encouraging orthogonality between entities). By eﬀectively manag-
ing this trade-oﬀ, the model enhances both precision and recall, leading 
to more robust NER performance.
3.4.  Model inference
Once training is complete, the trained LETNER model can classify 
new spans by mapping them to a set of entities. In metric learning, the 
Nearest Neighbour(NN) is a widely used approach for inference, where 
the entity label for an unknown span is determined based on its prox-
imity to learned entity representations (Yang & Katiyar, 2020).
In LETNER, we assign labels to spans by computing their similarity 
to entity representations using the dot product:
𝜃(𝑖, 𝑗, 𝑘) = 𝑒𝑘 ⋅ 𝑠𝑖∶𝑖+𝑗
where 𝜃(𝑖, 𝑗, 𝑘) represents the similarity score between the span repre-
sentation 𝑠𝑖∶𝑖+𝑗 and the entity representations 𝑒𝑘. To determine whether 
a span belongs to an entity class, we apply a threshold 𝜏( e.g. 𝜏 = 0.5). 
If the similarity score exceeds the threshold, i.e.,
𝜃(𝑖, 𝑗, 𝑘) > 𝜏
then the span 𝑠𝑖∶𝑖+𝑗 is classiﬁed as entity 𝑐𝑘. Since NER task requires 
that predicted spans do not overlap, we employ a greedy span selection 
algorithm, as introduced in  Zaratiana et al. (2022), to enforce this con-
straint during inference. After computing similarity scores for all pos-
sible spans (𝑖, 𝑗) and entity representations 𝑒𝑘, only spans with scores 
exceeding the threshold 𝜏 are considered valid entity candidates. To 
resolve overlapping spans, the greedy algorithm prioritises the longest 
and most conﬁdent spans by selecting those with the highest similarity 
scores while discarding overlapping candidates. This ensures that the 
model maintains the non-overlapping structure essential for NER tasks 
while accurately classifying entities in the input text.
3.5.  Label eﬃciency  evaluation
Once model is trained, we can evaluate model’s performance and 
cost trade-oﬀ, which was measured by the label-eﬃciency.  To system-
atically compare label eﬃciency  across diﬀerent models, we propose a 
model selection framework that helps decision-makers identify the most 
cost-eﬀective approach under resource constraints. This framework ad-
dresses two key questions:
• Which model provides the best trade-oﬀ between annotation cost 
and performance?
• How many labelled samples are required to achieve an optimal bal-
ance between cost and performance (e.g., F1-score)?
To quantify this trade-oﬀ, we draw upon the Law of Diminishing Re-
turns (Shephard & Färe, 1974), a principle from economics that describes 
performance saturation as additional resources are allocated. By incor-
porating this concept, we aim to provide actionable insights into the 
cost-eﬀectiveness of NER models for cyber security applications.
Cost Function. Let 𝑚 = |𝐷train| be the number of labelled data samples 
in the training set. The total annotation cost 𝐶(𝑚) is deﬁned as:
𝐶(𝑚) = 𝑎𝑚 + 𝑏 (8)
where 𝑎 represents the per-sample annotation cost (e.g., cost per sen-
tence), and 𝑏 accounts for ﬁxed overhead costs (e.g., infrastructure, data 
pre-processing).
Performance Function. Model performance 𝑃 (𝑚), measured using 
evaluation metrics such as F1-score, follows a logarithmic growth pat-
tern due to diminishing returns from additional labelled data. This rela-
tionship can be expressed as:
𝑃 (𝑚) = log 𝑁 (𝑚) + 𝑞 (9)
where 𝑁 controls the rate at which performance saturates and 𝑞 rep-
resents a bias term capturing baseline performance.
Point of Diminishing Returns (PoDR). To determine the PoDR, we use 
the maximum performance-to-cost gain ratio, a robust method since cost 
and performance exist on diﬀerent scales (e.g., annotation cost in thou-
sands vs. F1-score ranging from 0-100%). PoDR is identiﬁed as the point 
where the relative increase in performance per unit cost is maximised:
PoDR = arg max
𝑚
( 𝑑𝑃
𝑑𝑚
/ 𝑑𝐶
𝑑𝑚
)
(10)
where 𝑑𝑃 ∕𝑑𝑚 represents the marginal performance gain, and 𝑑𝐶 ∕𝑑𝑚
represents the marginal cost increase. This equation infers that PoDR 
can be found around the maximum gap between 𝑃 (𝑚) and 𝐶(𝑚). This 
approach provides two key insights for decision-making: (1) selecting 
the most cost-eﬀective model under a ﬁxed project budget and (2) 
determining the optimal number of annotations required for the best 
performance-cost trade-oﬀ. We will demonstrate this method of NER 
model selection using multiple models in a CTI NER task in Section 5.5.
4.  Experiments
Comprehensive experiments were conducted to evaluate the perfor-
mance of the proposed LETNER model. This section provides details 
of the experimental setup, starting with an introduction to the three 
datasets used, followed by descriptions of the baseline methods, evalu-
ation criteria, and model implementation details.
4.1.  Datasets
Unlike general domains, publicly available NER datasets in the CTI 
domain are scarce. To evaluate our model, LETNER, we utilise three 
existing CTI-focused datasets. Table 2 provides statistics for each entity 
class across these datasets.
• TwitterNER: Originally collected and labelled by Dionísio et al. 
(2020), this dataset contains 31,281 labelled tweets. We retrieved 
available tweets in 2021 using the tweet IDs provided by the au-
thors.4
• DNRTI (Wang et al., 2020): The ﬁrst open-source CIT NER dataset.
• APTNER (Wang et al., 2022): A large-scale CIT NER dataset derived 
from Advanced Persistent Threat (APT) reports.
4.2.  Baselines
To comprehensively evaluate model performance, we selected base-
line models from two perspectives: (1) Supervised ﬁne-tuning models 
that are similar to ours, ensuring fair comparison with traditional NER 
methods. (2)LLM inference-only models, where we assess open-source 
LLMs on a subset of sampled data for qualitative analysis.
4 https://github.com/ndionysus/multitask-cyberthreat-detection
Expert Systems With Applications 324 (2026) 132470 
7 

Y. Wang et al.
Table 2 
Dataset statistics.
 Dataset  TwitterNER (Dionísio et al., 2020)  DNRTI (Wang et al., 2020)  APTNER (Wang et al., 2022)
 # Entity Classes  6  14  22
 Label Scheme  BIO  BIOS  BIOES
 # Sentence  11068  4647  9743
 Sentence Length (Min-Mean-Max)  3-22.63-67  2-35.39-115  3-34.87-411
 Entity class distribution (Min-Max)  0.34%-51.22%  0.26%-77.88%  0.004%-82.94%
 Entity Labels
ID, ORG, PRO,
VER, VUL, O
Area, Exp, Features,
HackOrg, Idus, O,
OﬀAct, Org, Purp,
SamFile, SecTeam,
Time, Tool, Way
ACT, APT, DOM, EMAIL,
ENCR, FILE, IDTY, IP,
LOC, MAL, MD5, O, OS,
VULID, URL, SECTEAM,
SHA1, SHA2, TIME,
TOOL, VULNAME
1. Flair(BiLSTM-CRF) (Dionísio et al., 2019): This model employs pre-
trained word embeddings as input, which are processed through 
Bidirectional Long Short-Term Memory (BiLSTM) layers for feature 
learning. A Conditional Random Field (CRF) layer follows to enforce 
the positional prediction of BIO labels. We implemented this model 
using the Flair framework.5
2. BERT-base and XLNet-base: Prior research (Evangelatos et al., 
2021) has shown that these transformer-based models perform well 
for CTI NER tasks, treating them as token classiﬁcation problems.
3. CySecBERT (Bayer et al., 2024): A transformer-based BERT model 
pre-trained on CTI data, applied here for token-level classiﬁcation in 
CTI NER tasks.
4. RoBERTa-BiGRU-CRF (Ahmed et al., 2024): This model leverages 
RoBERTa for feature extraction, followed by a Bi-directional GRU 
layer to learn word-level representations and a CRF layer to compute 
the probability for each entity.
5. GLiNER (Zaratiana et al., 2024): A general open-domain NER model 
that employs a metric learning-based architecture with a span-based 
approach. GLiNER uses the DeBERTa encoder to learn prompts (NER 
labels) and spans in a shared space. It has been ﬁne-tuned on several 
general-domain NER datasets.
6. Llama-3-1B (Dubey et al., 2024): Part of the open-source Llama 
family of LLMs, Llama-3-1B is based on a decoder-only architec-
ture. We include this model to evaluate how a larger decoder-
only model architecture performs compared to traditional encoder-
based models for the NER task. However, ﬁnetuning LLMs for token 
classiﬁcation demands substantial computing resources. To adapt 
Llama-3-1B for this task eﬃciently,  we employ Low-Rank Adaptation 
(LoRA) (Hu et al., 2022), a parameter-eﬃcient  ﬁne-tuning method 
that reduces computational overhead while enabling eﬀective adap-
tation to domain-speciﬁc data.
7. Llama-3-8B (Dubey et al., 2024): A larger variant of Llama-3, fea-
turing an 8-billion-parameter architecture. Unlike Llama-3-1B, this 
model is not ﬁne-tuned but is instead used in a zero-shot inference 
setting to analyse its qualitative performance compared to LETNER.
8. DeepSeek-r1:14B: An open-source LLM optimised for natural 
language understanding and generation. Similar to Llama-3-8B, 
DeepSeek-r1 is evaluated solely in an inference-only setting, without 
ﬁne-tuning, to examine its ability to recognise cyber security-related 
entities for qualitative analysis.
4.3.  Evaluation
NER performance evaluation. In this work, we assess model per-
formance using micro-precision, micro-recall, and micro-F1 score, ex-
cluding the non-entity class (𝑂 class ). Unlike many prior studies that 
evaluate all classes, our approach is better suited to the CTI domain, 
5 https://github.com/ﬂairNLP/ﬂair
where accurately identifying entity spans is more crucial than handling 
non-entity tokens. Given the inherent class imbalance in three datasets, 
micro-averaging ensures that each entity instance contributes equally to 
the overall evaluation, preventing dominant classes from disproportion-
ately inﬂuencing the results.
Formally, let 𝑇 𝑃𝑐 , 𝐹 𝑃𝑐, and 𝐹 𝑁𝑐 denote the true positives, false pos-
itives, and false negatives for entity class 𝑐 ∈  . The micro-precision 
(Pmicro), micro-recall (Rmicro), and micro-F1 score are deﬁned as:
Pmicro =
∑
𝑐∈ 𝑇 𝑃𝑐
∑
𝑐∈ (𝑇 𝑃𝑐 + 𝐹 𝑃𝑐) (11)
Rmicro =
∑
𝑐∈ 𝑇 𝑃𝑐
∑
𝑐∈ (𝑇 𝑃𝑐 + 𝐹 𝑁𝑐 ) (12)
F1micro = 2 × Pmicro × Rmicro
Pmicro + Rmicro
(13)
By excluding the non-entity class, our evaluation focuses on the 
model’s ability to identify meaningful entity classes, aligning with real-
world CTI applications where detecting key entities such as malware, 
vulnerabilities, and threat actors is of primary importance.
Label eﬃciency  evaluation. To measure label eﬃciency,  data is 
split into training and test sets at varying ratios. Speciﬁcally, we incre-
mentally increase the proportion of labelled data used for training from 
10% to 80%, with the remainder used for testing. A minimum 10% la-
belled data is decided to ensure a full coverage of all entity classes in 
the training set due to the severe class imbalance in all datasets. This 
setup mimics real-world conditions where only a small fraction of the 
dataset is annotated, oﬀering valuable insights into each model’s ability 
to learn from limited supervision (i.e. label eﬃciency).  For each train-
ing scenario, we run experiments with three diﬀerent random seeds and 
report the averaged results to ensure robustness.
4.4.  Implementation
All models were implemented using PyTorch 3.11 and trained on 
an A100 GPU computing instance provided by the university’s High-
Performance Computing (HPC) facility. For our model, LETNER, we 
used Microsoft/deberta-v3-small6 as the token-level encoder and all-
MiniLM-L6-v27 as the sentence-level encoder due to its strong perfor-
mance and eﬃciency.
The number of training steps was adjusted based on the training data 
size, ranging from 2,000 to 12,000 steps. The hyperparameter 𝛽, which 
balances the impact of the two loss terms, was tuned within the range 
[0.5, 0.7] for each dataset to optimise performance. The Span-CNN-Gate 
6 https://huggingface.co/microsoft/deberta-v3-small
7 https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
Expert Systems With Applications 324 (2026) 132470 
8 

Y. Wang et al.
Table 3 
Micro-F1 score (averaged over three runs) on all entity classes reported on diﬀerent training and testing settings. The highest score is marked in bold and second 
highest score is underlined.
 Dataset  Train Size Flair BERT-base XLNet-base CySec-BERT BiGRU-CRF LLaMA-LoRA GLiNER-  LETNER
(Dionísio et al., 
2019)
(Evangelatos 
et al., 2021)
(Evangelatos 
et al., 2021)
(Bayer et al., 
2024)
(Ahmed et al., 
2024)
(Dubey et al., 
2024)
(Zaratiana et al., 
2024)
 APTNER (22 classes)
 10% 60.05 57.45 59.51 31.40 29.41 6.20 63.99  71.85
 50% 74.91 72.39 72.66 72.77 55.06 49.42 72.89  76.44
 80% 77.17 76.23 76.23 76.19 64.15 64.35 76.22  77.23
 DNRTI (14 classes)
 10% 58.12 45.51 43.97 26.87 37.36 4.16 65.06  69.48
 50% 76.93 72.94 69.67 71.14 65.81 53.00 70.51  78.85
 80% 80.97 78.38 77.07 76.65 77.11 68.00 78.48  81.18
 TwitterNER (6 classes)
 10% 92.57 89.98 90.17 91.33 76.37 72.32 93.07  95.20
 50% 96.47 96.00 95.74 95.60 89.47 94.06 96.02  97.08
 80% 96.57 96.53 96.29 96.35 92.22 96.51 94.43  97.85
window size 𝑗 was ﬁxed at 5 across all three datasets, guided by domain 
observations indicating that most multi-token CTI entities fall within 
this range. The hidden dimension of the metric space is deﬁned as 𝑑ℎ =
768. We used a batch size of 8 for training, with a learning rate of 1e-
5 for the dual encoders and 3e-5 for the rest of the network. During 
inference, a threshold 𝜏 = 0.5 was applied to determine whether a span 
belongs to an entity class.
5.  Results and discussions
This section discusses the experimental results from multiple per-
spectives. We begin by comparing the proposed LETNER model with 
state-of-the-art baseline methods in similar model scale across three dif-
ferent datasets to assess their comparative performance on the NER task. 
Next, we conduct a qualitative analysis, comparing LETNER with two 
LLMs (Llama3 and DeepSeek-r1) to assess how LETNER compared to 
state-of-the-art LLMs on the quality of NER results. After that, we analyse 
models performance under varying amounts of training data to assess 
label eﬃciency.  This is followed by an ablation study to investigate the 
contribution of each core component to LETNER’s performance. Finally, 
we analyse the label eﬃciency  by comparing LETNER with Flair (LSTM-
CRF), to provide insights for decision-makers on the performance-cost 
trade-oﬀ under diﬀerent resource settings.
5.1.  Performance comparison with state-of-the-art
Table 3 reports the Micro-F1 scores, a balanced metric that eval-
uates precision and recall, for all baseline models across three diﬀer-
ent datasets with varying training sizes. Among all baselines, LETNER 
demonstrates superior performance, label eﬃciency,  and robustness 
across diverse training scenarios in both complex CTI datasets (APT-
NER and DNRTI) and simpler ones (TwitterNER). It consistently outper-
forms other models across all datasets, achieving the highest F1 scores in 
both low-resource (10%) and high-resource (80%) training settings. No-
tably, in the APTNER dataset, LETNER surpasses the second-best model 
(GLiNER) by 7.86% and the third-best model (Flair, a BiLSTM-CRF) by 
11.8% when trained on just 10% of the data, highlighting its robustness 
in low-resource conditions.
GLiNER performs the second-best in low-resource settings (10% 
training data) across all three datasets, showcasing the label eﬃciency  
beneﬁts of its metric-learning-based architecture. However, despite its 
general-domain NER pretraining, it fails to match LETNER’s eﬃciency.  
Surprisingly, the traditional Flair model (BiLSTM-CRF) delivers com-
petitive results(second best), particularly in moderate- to high-resource 
scenarios, demonstrating strong feature extraction capabilities. Among 
transformer-based models, BERT, XLNet, CySecBERT, and BiGRU-CRF 
(based on RoBERTa) exhibit similar trends, gradually improving with 
more training data but consistently underperforming compared to LET-
NER, GLiNER, and Flair. In contrast, LLaMA3-1B ﬁne-tuned with LoRA 
lags behind most models across all settings, highlighting its unsuitabil-
Fig. 5. Prompt instructions for LLMs to identify CTI-related entities.
ity for token classiﬁcation tasks, possibly due to its decoder-only based 
architecture.
5.2.  Performance comparison with open-source LLMs
This subsection compares the proposed LETNER model with two 
open-source yet comparatively lightweight LLMs on 100 randomly sam-
pled unseen instances from the APTNER dataset. The experiment pro-
vides both quantitative and qualitative analyses to assess LETNER’s per-
formance relative to larger open-source LLMs operating without ﬁne-
tuning. Speciﬁcally, LETNER was trained using only 30% of the labelled 
data, while Llama3-8B (Dubey et al., 2024) and DeepSeek-R1:14B (Guo 
et al., 2025) were accessed via APIs using the Ollama client.8
The LLMs were instructed to act as security analysts and extract 
entities according to the semantic label deﬁnitions used for LETNER 
training. The prompt template is shown in Fig. 5. To facilitate post-
processing, the models were required to return outputs in structured 
JSON format. The extracted entities were parsed and mapped to span 
representations aligned with the ground-truth annotations. A predicted 
span was counted as correct only when both the span boundaries and 
entity type exactly matched the gold annotation. Gold spans without 
matching predictions were counted as false negatives, while predicted 
spans absent from the gold annotations were treated as false positives. 
Total span-level errors were computed as the sum of false positives and 
false negatives, and category proportions were derived from this total. 
The same evaluation protocol was applied to all three models to com-
pute micro-precision, micro-recall, and micro-F1 scores, as well as to 
conduct error analysis.
8 https://ollama.com/
Expert Systems With Applications 324 (2026) 132470 
9 

Y. Wang et al.
Table 4 
NER Performance comparison of LETNER with 
Llama3-8B and DeepSeek-r1:14B. All metrics are re-
ported in Micro.
 Model  Precision  Recall  F1
 Llama3-8B  26.1  23.6  24.8
 Llama3-8B (normalised)  26.1  23.6  24.8
 DeepSeek-14B  37.8  32.5  34.9
 DeepSeek-14B (normalised)  40.1  34.2  36.9
 LETNER  63.4  69.8  66.5
Quantitative analysis: Table 4 presents the quantitative compari-
son. LETNER substantially outperforms both LLM baselines, achieving 
improvements of approximately 29.6 F1 points over DeepSeek-14B and 
41.7 F1 points over Llama3-8B. This performance gap is primarily at-
tributed to LETNER’s improved span boundary detection and its abil-
ity to recognise ﬁne-grained CTI entities under limited supervision. In 
contrast, LLM performance is constrained by conservative extraction be-
haviour and diﬃculty  identifying multi-token entities, resulting in lower 
recall. Because LLM outputs may appear in diﬀerent formats and vary in 
punctuation spacing (e.g., Microsoft.NET vs Microsoft .NET), we manu-
ally corrected these inconsistencies to align predictions with the ground-
truth labels, producing normalised results. However, this normalisation 
produced only marginal improvements, indicating that most errors stem 
from entity recognition challenges rather than formatting mismatches.
Qualitative analysis: Table 5 presents entity predictions from all 
three models for qualitative analysis. Compared with ground truth la-
bels, we observe that LETNER successfully identiﬁed most entities. In 
contrast, DeepSeek missed some, and Llama3-8B missed a signiﬁcant 
number, leading to the lowest recall among three models. This obser-
vation is consistent with the quantitative results. For example, Llama3 
missed all location and time-related entities, such as “August 2013” in 
the third sentence, “July 2014” in the ﬁfth sentence and “Japanese” in 
the sixth sentence. It seems that Llama struggles to look through all 22 
entity classes and only focuses on the ﬁrst few security-related entity 
classes.
DeepSeek, leveraging its strong reasoning capabilities, achieved 
comparatively high coverage of entities but tends to misidentify 
security-related entities regarding their span boundaries and correct 
entity classes. For example, “FireEye”, a SECTEAM entity was incor-
rectly identiﬁed as IDTY (Identiﬁed entities) as in the third sentence. 
More critically, “admin@338” (an APT entity) was misclassiﬁed as an 
email address by both LLMs, highlighting their limited understanding of 
CTI-speciﬁc terminology. It is worth noting that to achieve this perfor-
mance, DeepSeek required signiﬁcant inference time due to its reliance 
on chain-of-thought reasoning, taking up to 525 s on average (across 10 
queries) to generate a response.
Moreover, we observed that LLM-based models occasionally failed to 
adhere to the required structured JSON output format, which is crucial 
for CTI applications where a standardised output is necessary for down-
stream processing. In contrast, LETNER, despite a few misclassiﬁed span 
boundaries, such as in the second and sixth sentences, achieved better 
performance than DeepSeek and Llama while maintaining a lightweight 
model architecture. Given its eﬃciency  and ability to learn from limited 
labelled training data, LETNER is better suited for CTI NER tasks.
Error analysis: To better understand the error patterns of LETNER, 
we summarise the false positives and false negatives in Table 6. LETNER 
produces slightly more mis-classiﬁcations than missed spans, which is 
consistent with its high recall performance. Upon closer examination, 
we observe that most errors occur in the following scenarios. First, rare 
CTI entities with limited training instances are occasionally missed; for 
example, 14 “FILE” and 13 “IDTY” entities are predicted as “O”. Addi-
tionally, a considerable number of mis-classiﬁcations occur between se-
mantically related CTI entity categories, particularly “ACT” and “APT”, 
as well as “FILE” and “MAL”. A manual review of the ground-truth an-
notations across the APTNER dataset reveals that some entities are in-
consistently labelled as “TOOL” or “MAL” in diﬀerent sentences. This 
reﬂects the dual-label nature of many cyber security terms and the over-
lap between certain entity types, where the same entity may assume 
diﬀerent roles depending on context. Such entity ambiguity highlights 
the potential need for models capable of operating under a multi-label 
classiﬁcation setting in future work.
5.3.  Impact of training size on model performance
Fig. 6 examines the eﬀect of increasing training data for diﬀerent 
models across all datasets. While all models beneﬁt from additional 
training data, the improvement rates vary. LETNER and GLiNER start 
with relatively high initial performance and exhibit steady, gradual im-
provements across training sizes, with LETNER consistently outperform-
ing others. In contrast, transformer-based models (BERT, XLNet, and 
CySecBERT) show rapid initial improvements as training data increases 
but plateau beyond a threshold of approximately 40-50% of the train-
ing set. BiGRU-CRF and LLaMA-LoRA, as observed in previous results, 
continue to lag behind other models across all datasets despite increases 
in training data. However, LLaMA-LoRA shows signs of catching up on 
the TwitterNER dataset when trained with 80% of the data, suggesting 
that larger language models require more labelled samples to achieve 
competitive performance.
Across all datasets, additional labelled data yields minimum perfor-
mance gain after a certain point, but the size threshold varies. On the 
more complex APTNER and DNRTI datasets, most models see steady per-
formance gains beyond approximately 50% annotation. In contrast, on 
the simpler TwitterNER dataset, most models show minimal improve-
ment beyond 30% annotation, reaching peak performance much earlier 
than on the other two datasets. This trend suggests that the amount 
of training data required for optimal learning depends on the dataset’s 
complexity.
In summary, while increased annotation improves all models’ perfor-
mance, LETNER demonstrates superior label eﬃciency,  requiring signif-
icantly fewer labelled data to achieve high NER performance compared 
to other baselines. Notably, with just 10% of the training data, LET-
NER surpasses the widely adopted Flair NER framework by 11.8% in the 
F1 score. This highlights its suitability for real-world CTI applications, 
where obtaining annotated data is often costly and resource-intensive.
5.4.  Ablation study
The ablation study analyses the contribution of two core components 
in LETNER: the Span-CNN-gate module and the orthogonal constraint. 
Three variations have been developed: (1) removing Span-CNN-gate 
(W/o Span-CNN-gate), (2) removing orthogonal constraint (W/o Or-
thogonal) and removing both of them (W/o both). For implementing the 
’W/o both’ variation, we use the concatenation of the starting and end-
ing tokens to learn a span representation as in GLiNER (Zaratiana et al., 
2024). In our earlier experiments, we observed that LETNER’s perfor-
mance gains plateau after utilising 50% of the training data. Therefore, 
we use 50% of the training set as a cut-oﬀ to systematically evaluate the 
eﬀect when removing each component.
Results in Table 7 demonstrate that the Span-CNN-Gate module and 
the orthogonal constraint contribute to LETNER’s overall performance. 
When both components are removed (W/o both), the model relies solely 
on simple token concatenation for span representation learning. This 
setting consistently performs poorly in Precision, Recall, and F1 scores 
across all datasets.
Introducing the Span-CNN-gate module (W/o Orthogonal) signiﬁ-
cantly improves F1 scores (+4.19% for APTNER, +8.78% for DNRTI, 
and +1.99% for TwitterNER), demonstrating its eﬀectiveness in extract-
ing local contextual features crucial for entity recognition, particularly 
in complex datasets like APTNER and DNRTI. Adding the orthogonal 
Expert Systems With Applications 324 (2026) 132470 
10 

Y. Wang et al.
Fig. 6. Model performance as Weighted-F1 on various datasets with diﬀerent training-testing ratios.
Expert Systems With Applications 324 (2026) 132470 
11 

Y. Wang et al.
Table 5 
Side by side entity predictions of LETNER, Llama3-8B and DeepSeek-r1:14B on the test set. Blue text marks the successfully identiﬁed entities and their 
classes, while the orange text marks the misidentiﬁed entities.
Table 6 
Error analysis for LETNER.
 Error Category  Count  Proportion
 False Positives  123  57.2%
 False Negatives  92  42.8%
Table 7 
Results for the ablation study. Averaged Micro-Precision, Micro-Recall 
and Micro-F1 (over three random runs) and their standard deviations 
are reported. All models are trained with 50% labelled dataset and 
tested on the rest 50% dataset.
 APTNER
 F1% ± std  Recall% ± std  Precision% ± std
 W/o both  70.02±0.27  73.46±0.65  66.88±0.39
 W/o Span-CNN-Gate  70.77±0.22  72.27±0.34  69.33±0.42
 W/o Orthogonal  74.21±0.44  73.37±0.69  75.07±0.49
 LETNER  76.44±0.51  77.7±0.66  75.21±0.52
 DNRTI
 W/o both  69.93±0.75  75.45±0.50  65.16±0.96
 W/o Span-CNN-Gate  72.21±0.54  75.20±0.72  69.45±0.57
 W/o Orthogonal  78.71±0.30  77.88±0.45  79.57±0.15
 LETNER  78.85±0.24  81.27±0.67  76.56±0.11
 TwitterNER
 W/o both  92.69±0.33  93.40±0.23  92.00±0.48
 W/o Span-CNN-Gate  93.70±0.12  93.88±0.25  93.53±0.12
 W/o Orthogonal  94.68±0.15  94.05±0.11  95.32±0.26
 LETNER  97.08±0.03  98.39±0.06  95.81±0.10
constraint (W/o Span-CNN-Gate), compared to W/o both, primarily ben-
eﬁts precision, suggesting that it helps disentangle entity representations 
and reﬁne boundary detection. The full LETNER model, which incor-
porates both enhancements, achieves the highest F1 scores across all 
datasets by balancing recall and precision.
For the DNRTI dataset, the LETNER variation only considering the 
Span-CNN-Gate and removing the orthogonality (i.e. W/o Orthogonal) 
results in higher precision (79.57%) compared to LETNER (76.56%), but 
at the cost of lower recall (77.88%) than LETNER (81.27%). This sug-
gests that while orthogonal regularisation encourages feature diversity, 
it may also restrict the model’s ability to recognise certain ambiguous en-
tities. Notably, in DNRTI, some entity annotations overlap; for example, 
APT28 malware is labelled as TOOL, while APT28 alone is labelled as 
HackOrg (hacking organisation). Such annotation inconsistencies may 
explain why orthogonality, which enforces feature separation, reduces 
precision by limiting the model’s ﬂexibility in handling overlapping en-
tities. These results indicate that while the orthogonal constraint reﬁnes 
precision, its impact depends on the dataset’s entity overlap character-
istics. The full LETNER model, incorporating both Span-CNN-Gate and 
orthogonality, achieves a balanced trade-oﬀ, yielding the highest F1-
score (78.85%). These ﬁndings highlight the importance of integrating 
both Span-CNN-Gate and orthogonal constraints, as they collectively op-
timise entity extraction by improving recall, precision, and overall F1.
5.5.  Trade-oﬀ between annotation cost and model performance
We conduct a case study to compare the label eﬃciency  of LETNER 
with Flair (LSTM-CRF), a widely used NER framework with a diﬀerent 
model architecture (Akbik et al., 2019). This analysis provides insights 
into their cost-performance trade-oﬀs. Using the APTNER dataset, which 
consists of 9,743 sentences with 22 ﬁne-grained entity classes, we esti-
Expert Systems With Applications 324 (2026) 132470 
12 

Y. Wang et al.
Fig. 7. Annotation cost and model performance trade-oﬀ based on the PoDR on the APTNER dataset. The X-axis represents annotation cost (AUD), increasing 
progressively from 10% to 80% of the annotated dataset. The left Y-axis denotes the Micro-F1 score on the testing set, while the right Y-axis represents the Marginal 
Gain, computed as the change in F1-score per unit increase in annotation cost.
mate annotation costs based on a research assistant’s labour rate of 60 
AUD per hour in Australia. Given the complexity of the task, we esti-
mate the per sentence cost is 0.40 AUD, and the annotating 10% of the 
dataset is estimated to cost approximately 390 AUD while increasing 
the annotation to 80% raises the price to 3118 AUD.
Fig. 7 presents the performance-cost trade-oﬀ for LETNER and Flair. 
LETNER exhibits a sharp increase in performance before reaching the 
Point of Diminishing Returns (PoDR) at approximately 1,500 AUD (40% 
annotated data), with an F1-score slightly above 76%. Beyond this point, 
the marginal gain in performance declines signiﬁcantly. Flair follows a 
diﬀerent trend. Initially, the marginal gain drops signiﬁcantly, followed 
by a slight increase, which occurs at 2,000 AUD cost with an F1-score 
of 75%. After this point, additional annotation provides minimal per-
formance improvements, suggesting the PoDR occurs at around 50% 
annotation data.
This experiment reveals that LETNER is signiﬁcantly more label-
eﬃcient  than Flair. The performance gap is especially pronounced at 
lower annotation percentages, indicating that LETNER learns more ef-
fectively from limited labelled data. On the other hand, Flair requires 
substantially more annotated data to achieve comparable performance, 
resulting in higher annotation costs for similar F1-score gains. For ex-
ample, at 50% annotation, LETNER achieves an F1-score of 76.44%, 
whereas Flair only reaches 74.91%. To attain a comparative F1 score(of 
76.39), Flair requires at least 60% annotation, incurring a 10% higher 
annotation cost than LETNER.
6.  Conclusion and future work
In this paper, we introduced LETNER, a label-eﬃcient  NER frame-
work designed for CTI. Addressing the challenges of high annotation 
costs and domain-speciﬁc adaptation, LETNER integrates the innova-
tive concepts of metric learning, span-based feature extraction, and 
a CNN-gating mechanism to improve entity recognition in CTI texts. 
We also proposed a method for evaluating label eﬃciency,  assisting 
decision-makers in selecting optimal trade-oﬀs between annotation ef-
fort and model performance. Experimental results on multiple CTI 
datasets demonstrate that LETNER signiﬁcantly outperforms state-of-
the-art NER frameworks at low resource setting. Our ablation study 
further highlights the importance of the Span-CNN-Gate module and 
orthogonality constraint, conﬁrming their contributions to improving 
span-based entity extraction. These ﬁndings suggest that LETNER pro-
vides a practical and eﬀective solution for CTI analysis, where rapid 
adaptation to evolving threats is crucial.
While LETNER demonstrates strong performance under limited an-
notation conditions, further research is needed to enhance its generali-
sation across diverse datasets. A promising direction is pretraining LET-
NER on heterogeneous cyber security corpora, such as threat reports, 
vulnerability disclosures, and social media discussions to improve few-
shot and zero-shot inference on diverse datasets.
Additionally, LETNER does not currently address the multi-label as-
signment problem, which is also critical in the CTI domain. In real-world 
CTI reports, certain entities may serve multiple functional roles and may 
be associated with diﬀerent entity classes. The current LETNER formu-
lates entity recognition as a single-labelling task, which is consistent 
with standard NER evaluation methods. Extending LETNER to support 
multi-label classiﬁcation represents an important future direction and 
would require modiﬁcations to the inference strategy, such as sigmoid-
based multi-label prediction and threshold-based decoding. Moreover, 
additional benchmark datasets designed to support multi-label entity 
annotation will be necessary to properly evaluate this capability.
Declaration of generative AI and AI-assisted technologies in the 
writing process
During the preparation of this work, authors used ChatGPT to proof-
read and polish the language. After using this service, authors carefully 
reviewed and edited the content as needed and take full responsibility 
for the content of the publication.
CRediT authorship contribution statement
Yue Wang: Conceptualization, Methodology, Writing – original 
draft, Software, Writing – review & editing; Duoyi Zhang: Conceptu-
alization, Methodology, Writing – original draft, Software, Writing – re-
view & editing; Md Abul Bashar: Conceptualization, Methodology, Soft-
ware, Supervision, Writing – review & editing, Resources; Mahinthan 
Chandramohan: Investigation, Funding acquisition, Supervision, Writ-
ing – review & editing, Resources; Richi Nayak: Conceptualization, 
Methodology, Investigation, Writing - review & editing, Resources.
Data availability
Data will be made available on request.
Declaration of competing interests
The authors declare the following ﬁnancial interests/personal rela-
tionships which may be considered as potential competing interests:
Yue Wang reports ﬁnancial support through scholarship donated by 
Oracle Labs Australia. The company had no role in study design, anal-
yses, decisions to publish, or manuscript preparation. If there are other 
Expert Systems With Applications 324 (2026) 132470 
13 

Y. Wang et al.
authors, they declare that they have no known competing ﬁnancial in-
terests or personal relationships that could have appeared to inﬂuence 
the work reported in this paper. 
Acknowledgment
The author would like to thank Oracle Labs Australia and the QUT 
Centre for Data Science for their scholarship support for her PhD stud-
ies. She also acknowledges the QUT eResearch team for providing High 
Performance Computing resources used in the experiments. 
References
Ahmed, K., Khurshid, S. K., & Hina, S. (2024). CyberEntRel: Joint extraction of cyber 
entities and relations using deep learning. Computers & Security, 136, 103579.
Akbik, A., Bergmann, T., Blythe, D., Rasul, K., Schweter, S., & Vollgraf, R. (2019). FLAIR: 
An easy-to-use framework for state-of-the-art NLP. In Proc. annu. conf. north am. chapter 
assoc. comput. linguist. (demonstrations) (pp. 54–59).
Bayer, M., Kuehn, P., Shanehsaz, R., & Reuter, C. (2024). CySecBERT: A domain-adapted 
language model for the cybersecurity domain. ACM Transactions on Privacy and Secu-
rity, 27(2), 1–20.
Chen, Y., Zheng, Y., & Yang, Z. (2023). Prompt-based metric learning for few-shot NER. 
In Findings of the association for computational linguistics: ACL 2023 (pp. 7199–7212).
Dionísio, N., Alves, F., Ferreira, P. M., & Bessani, A. (2019). Cyberthreat detection from 
twitter using deep neural networks. In 2019 int. jt. conf. neural netw. (IJCNN) (pp. 1–8). 
IEEE.
Dionísio, N., Alves, F., Ferreira, P. M., & Bessani, A. (2020). Towards end-to-end cy-
berthreat detection from twitter using multi-task learning. In 2020 int. jt. conf. neural 
netw. (IJCNN) (pp. 1–8). IEEE.
Dubey, A., Jauhri, A., Pandey, A., Kadian, A., Al-Dahle, A., Letman, A., Mathur, A., Schel-
ten, A., Yang, A., Fan, A. et al. (2024). The llama 3 herd of models. arXiv preprint 
arXiv:2407.21783, .
Evangelatos, P., Iliou, C., Mavropoulos, T., Apostolou, K., Tsikrika, T., Vrochidis, S., & 
Kompatsiaris, I. (2021). Named entity recognition in cyber threat intelligence us-
ing transformer-based models. In 2021 IEEE int. conf. cyber security resil. (CSR) (pp. 
348–353). IEEE.
Finkel, J. R., Grenager, T., & Manning, C. D. (2005). Incorporating non-local information 
into information extraction systems by gibbs sampling. In Proceedings of the 43rd annual 
meeting of the association for computational linguistics (ACL’05) (pp. 363–370).
Gautam, S., Boubekki, A., Hansen, S., Salahuddin, S., Jenssen, R., Höhne, M., 
& Kampﬀmeyer, M. (2022). ProtoVAE: A trustworthy self-explainable prototyp-
ical variational model. Advances in Neural Information Processing Systems, 35,
17940–17952.
Guo, D., Yang, D., Zhang, H., Song, J., Zhang, R., Xu, R., Zhu, Q., Ma, S., Wang, P., Bi, 
X. et al. (2025). DeepSeek-R1: Incentivizing reasoning capability in llms via reinforce-
ment learning. arXiv preprint arXiv:2501.12948, .
Honnibal, M., Montani, I., Van Landeghem, S., Boyd, A. (2020). SpaCy: Industrial-strength 
natural language processing in python, https://doi.org/10.5281/zenodo.1212303 .
Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W. et al. 
(2022). LoRA: Low-rank adaptation of large language models. ICLR, 1(2), 3.
Huang, Z., Xu, W., & Yu, K. (2015). Bidirectional LSTM-CRF models for sequence tagging. 
arXiv preprint arXiv:1508.01991, .
Kaya, M., & Bilge, H. ¸ S. (2019). Deep metric learning: A survey. Symmetry, 11(9), 1066.
Li, J., Sun, A., Han, J., & Li, C. (2020). A survey on deep learning for named entity recog-
nition. IEEE Trans. Knowl. Data Eng., 34(1), 50–70.
Luo, Z., Zou, Y., Hoﬀman, J., & Fei-Fei, L. F. (2017). Label eﬃcient  learning of transferable 
representations acrosss domains and tasks. In I. Guyon, U. V. Luxburg, S. Bengio,
H. Wallach, R. Fergus, S. Vishwanathan, & R. Garnett (Eds.), Advances in neural informa-
tion processing systems. Curran Associates, Inc. (vol. 30). https://proceedings.neurips.
cc/paper_ﬁles/paper/2017/ﬁle/a8baa56554f96369ab93e4f3bb068c22-Paper.pdf .
Luong, K., Nayak, R., Balasubramaniam, T., & Bashar, M. A. (2022). Multi-layer mani-
fold learning for deep non-negative matrix factorization-based multi-view clustering. 
Pattern Recognition, 131, 108815.
Mahboubi, A., Luong, K., Aboutorab, H., Bui, H. T., Jarrad, G., Bahutair, M., Camtepe, S., 
Pogrebna, G., Ahmed, E., Barry, B. et al. (2024). Evolving techniques in cyber threat 
hunting: A systematic review. Journal of Network and Computer Applications, 232, (p. 
104004).
Rahman, M. R., Mahdavi-Hezaveh, R., & Williams, L. (2020). A literature review on min-
ing cyberthreat intelligence from unstructured texts. In IEEE International conference 
on data mining workshops, icdmw (pp. 516–525). IEEE Computer Society (vol. 2020-
November). https://doi.org/10.1109/ICDMW51313.2020.00075
Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese 
BERT-networks. In Proc. 2019 conf. empirical methods nat. lang. process. (EMNLP-
IJCNLP) (pp. 3982–3992).
Shen, W., Peng, Z., Wang, X., Wang, H., Cen, J., Jiang, D., Xie, L., Yang, X., & Tian, Q. 
(2023). A survey on label-eﬃcient  deep image segmentation: Bridging the gap be-
tween weak supervision and dense prediction. IEEE Transactions on Pattern Analysis 
and Machine Intelligence, 45(8), 9284–9305.
Shephard, R. W., & Färe, R. (1974). The law of diminishing returns. In Production theory: 
Proceedings of an international seminar held at the university at karlsruhe may–july 1973 
(pp. 287–318). Springer.
Shin, H., Shim, W., Kim, S., Lee, S., Kang, Y. G., & Hwang, Y. H. (2021). Twiti: Social 
Listening for Threat Intelligence. In Proceedings of the web conference 2021 (p. 13). 
New York, NY, USA: ACM. https://doi.org/10.1145/3442381
Wang, X., He, S., Xiong, Z., Wei, X., Jiang, Z., Chen, S., & Jiang, J. (2022). APTNER: A 
speciﬁc dataset for ner missions in cyber threat intelligence ﬁeld. In 2022 IEEE 25th 
int. conf. comput. supported cooperative work des. (CSCWD) (pp. 1233–1238). IEEE.
Wang, X., Liu, X., Ao, S., Li, N., Jiang, Z., Xu, Z., Xiong, Z., Xiong, M., & Zhang, X. 
(2020). DNRTI: A large-scale dataset for named entity recognition in threat intelli-
gence. In 2020 IEEE 19th int. conf. trust, security privacy comput. commun. (trustcom) 
(pp. 1842–1848).
Wang, Y., Bashar, M. A., Chandramohan, M., & Nayak, R. (2023). Exploring topic models 
to discern cyber threats on twitter: A case study on log4shell. Intelligent Systems with 
Applications, 20, 200280.
Wang, Y., Nayak, R., Bashar, M. A., & Chandramohan, M. (2025). Latent space reﬁne-
ment for unsupervised cyber threat text classiﬁcation. Knowledge-Based Systems, 329, 
(p. 114399).
Wu, X., Tao, X., Wu, W., Zhang, J., Li, Y., & Li, L. (2025). Random forest of thoughts: 
Reasoning path fusion for LLM inference in computational social science. Information 
Fusion, 127, (p. 103791).
Yang, Y., & Katiyar, A. (2020). Simple and eﬀective few-shot named entity recognition 
with structured nearest neighbor learning. In Proc. 2020 conf. empir. methods nat. lang. 
process. (EMNLP) (pp. 6365–6375).
Zaratiana, U., Tomeh, N., Holat, P., & Charnois, T. (2022). Named entity recognition as 
structured span prediction. In Proceedings of the workshop on unimodal and multimodal 
induction of linguistic structures (UM-ios) (pp. 1–10).
Zaratiana, U., Tomeh, N., Holat, P., & Charnois, T. (2024). GLiNER: Generalist model for 
named entity recognition using bidirectional transformer. In Proc. 2024 conf. north 
amer. chap. assoc. comput. linguist.: Human lang. technol. (vol. 1: Long papers) (pp. 
5364–5376).
Zhang, D., Nayak, R., & Bashar, M. A. (2024). Pre-gating and contextual attention gate-a 
new fusion method for multi-modal data tasks. Neural Networks, 179, 106553.
Zhang, D., Wang, Y., Bashar, M. A., & Nayak, R. (2023). Enhanced topic modeling with 
multi-modal representation learning. In Proc. paciﬁc-asia conf. knowl. discov. data min-
ing (pp. 393–404). Springer.
Zhou, S., Long, Z., Tan, L., GuoH. (2018). Automatic identiﬁcation of indicators of com-
promise using neural-based sequence labelling. In Proc. 32nd pac. asia conf. lang., inf., 
comput.
Expert Systems With Applications 324 (2026) 132470 
14 