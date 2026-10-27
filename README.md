# Changing Work

An exploratory dashboard of AI-related activities in job advertisements across UX research, product design, product management, marketing strategy/customer experience, and software engineering.

**Live site:** https://klukoff.github.io/changing-work/

The October 27, 2026 exploratory release covers 2,846 occupation-ad observations and 99 operational competencies. The software-engineering hierarchy follows [Andrew Ng's AI Engineering Skills Map](https://www.linkedin.com/pulse/ai-engineering-skills-map-andrew-ng-m479c/). Study definitions, samples and numerical results are independent of his project.

## Visual encoding

All occupation maps use the same percentage cards, recorded counts and evidence-status labels. Fixed-height bars share a 0–100% scale. Percentages divide the recorded count by the entire occupational sample, never by the candidate-selected subset of reviewed ads. Unfilled portions include ads without recorded support, unreviewed text and inconclusive evidence; they do not establish absence. These shares are descriptive results of the current coding, not validated prevalence or statistical lower bounds. The homepage dot plot uses the same automated screen across all five cohorts on a fixed 0–100% scale, with stable occupation order and direct counts. It does not mix the occupation-specific reviewed skill counts.

## What the numbers mean

- UXR, design and PM maps display contextually supported detections from AI review of retrieved passages. Their percentages show the share of all sampled ads with support recorded so far. Unmatched text has not received exhaustive review, and subsequent coding can change these shares.
- Marketing retains an earlier AI-assisted full-ad interpretation of 500 ads.
- Engineering shows automated candidate capabilities. Ordinary engineering fundamentals are not automatically AI use.
- The comparison table uses the same automated AI-text screen for all five occupations. It includes false positives and has unmeasured recall. It is not a ranking of workplace adoption.
- No independent human validation has been completed. Job ads report advertised expectations, not observed use, productivity or displacement.

Read [the full methods and decision history](downloads/methods.html), [monitoring protocol](downloads/monitoring-protocol.html) and [quality report](downloads/quality-report.json).

## Run the website

This is a buildless static site. Serve the repository root, for example:

```sh
python3 -m http.server 8781
```

GitHub Pages serves the `main` branch root. Relative paths support the project subdirectory. No analytics, login, API keys or backend are needed. Review notes stay in the visitor's browser unless exported. They are not sent to the project.

## Public artifacts

- `data/study.json`: view data, operational rules, measurement status and selected evidence.
- `downloads/codebook.json`: all 99 definitions and coding boundaries.
- `downloads/skill-counts.csv`: clearly labeled count types and denominators.
- `downloads/cohort-metadata.json`: sampled source identifiers, dates, URLs and hashes.
- `downloads/review-examples.json`: paraphrased contextual review examples.
- `downloads/quality-report.json`: geography, dates, source state, employer and exact-text sensitivity checks.
- `downloads/prospective-capture.json`: a separate October 26 capture, not a second analyzed cohort.

Raw provider payloads, complete descriptions, private calibration feedback and working drafts are excluded. Third-party descriptions and Ng's framework retain their original rights and attribution.

## Rebuild the published data

```sh
python3 scripts/build_public.py --project-root /path/to/retained-research-workspace
python3 scripts/build_quality.py --project-root /path/to/retained-research-workspace
python3 scripts/validate_release.py
```

The release builder expects the retained workspace's `collection/openjobdata_pilot_500_2026-10-16/{uxr,design,pm}/pilot_sample.json`, `collection/marketing_pilot_500_2026-10-17/sample.json`, `collection/software_engineering_2026-10-26/sample.json`, the operational artifacts under `outputs/frontier_review_v3_2026-10-17`, and the reviewed outputs under `outputs/expanded_coding_2026-10-26` and `analysis/software_engineering_2026-10-26`. These raw inputs are not included here. The public repository alone cannot reproduce every source recovery or contextual judgment. The builder uses an explicit public-field allowlist.

`common_detector.py` and `screen_common.py` reproduce the comparison screen on recovered descriptions. Source offsets are retained by the private output. This screening output must not be mistaken for semantic validation.

## Collect a prospective batch

Install the pinned dependency in an isolated environment using `scripts/requirements.txt`, then choose an output directory **outside this repository**:

```sh
python3 scripts/capture_source.py --output /path/to/private-captures --capture
```

The collector pins the source revision, verifies publisher hashes/bytes, keeps dates separate, and records event-count discrepancies. It does not perform eligibility screening or publish estimates. The first test found 7,697 unscreened title-candidate versions. Its source manifest reported closure events absent from the listed full-change files; this discrepancy is retained. No trend should be inferred from the capture.

Monthly automatic publication is not enabled. A complete monitoring release needs source reconciliation, eligibility, deduplication, independent validation and versioned taxonomy decisions. See the protocol for stable measures, a discovery layer, expert-panel input and bridge coding.
