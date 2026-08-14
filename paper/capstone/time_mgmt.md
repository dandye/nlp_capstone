Given today's Monday and the paper's due Friday, here's a schedule that fits around your day job — front-loading the parts that don't need your active attention and reserving evenings for review/decisions:

**Mon (tonight):** Kick off the GLiNER retrain overnight as planned. While that runs, the paper rewrite for everything *not* blocked on it can proceed in parallel — Data/Method section describing the new LLM-gold pipeline, the RoBERTa-base/large + SecureBERT results tables and citations (all the numbers for these three are already sitting in `data/gold_v2/results/`, so no blocking there). You can review a draft whenever you get a spare few minutes, even at a glance.

**Tue evening:** GLiNER v2 numbers should be back from the overnight run. Slot them into the architecture-comparison table, finalize the Results section and the RQ2 discussion (this is the one section that was genuinely blocked on the retrain). Also make a quick call on RQ4 (frontier-LLM comparison) — there's no rerun of that against the new gold yet, so it's either a fast LLM-API rerun (cheap, could fit in one evening) or gets marked pending like GLiNER was.

**Wed evening:** Full consistency pass — abstract, intro RQs, related work, conclusion all need to agree with the new pipeline and numbers. Compile the LaTeX end-to-end (pdflatex + bibtex) and fix any reference/citation breakage. Decide on `gold_audit.md` — it's still an empty judgment sheet; realistically it's a "leave it pending" item unless you find an hour to hand-judge the 300 spans, which I wouldn't plan for given the timeline.

**Thu evening:** Buffer day. Proofread, tighten prose, confirm every `\pending{}` marker left in the paper is an intentional, honest limitation rather than a leftover TODO, final PDF build.

**Fri:** Submit, ideally with a final skim before your day job starts in case anything needs a last fix.

The only real risk to this schedule is if the GLiNER retrain fails or needs a second overnight run — worth checking on it first thing Tuesday morning rather than waiting for evening, so there's still a day of slack if it needs to rerun.

