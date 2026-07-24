PAPER = capstone
SURVEY = survey
LATEX = pdflatex -interaction=nonstopmode -halt-on-error

.PHONY: all pdf survey clean

all: pdf survey

pdf: $(PAPER).pdf

survey: $(SURVEY).pdf

$(PAPER).pdf: $(PAPER).tex $(PAPER).bib
	$(LATEX) $(PAPER).tex
	bibtex $(PAPER)
	$(LATEX) $(PAPER).tex
	$(LATEX) $(PAPER).tex

# The survey has no BibTeX citations yet (inline arXiv IDs), so two passes.
$(SURVEY).pdf: $(SURVEY).tex
	$(LATEX) $(SURVEY).tex
	$(LATEX) $(SURVEY).tex

# Regenerate survey.tex from survey.md (md2tex_survey.py)
survey-tex: survey.md md2tex_survey.py
	python3 md2tex_survey.py

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out \
	      $(SURVEY).aux $(SURVEY).log $(SURVEY).out
