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

$(SURVEY).pdf: $(SURVEY).tex $(SURVEY).bib
	$(LATEX) $(SURVEY).tex
	bibtex $(SURVEY)
	$(LATEX) $(SURVEY).tex
	$(LATEX) $(SURVEY).tex

# NOTE: survey.tex is now hand-edited (survey.md is deprecated).
# The old md->tex regeneration target was removed so it cannot clobber edits.

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out \
	      $(SURVEY).aux $(SURVEY).log $(SURVEY).out
