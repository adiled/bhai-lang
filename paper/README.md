# Paper

`bhai.tex` — research paper formalizing the رشتہ semantics, kinship-typed lineage edges, and گواہی cryptographic protocol.

## Compile

Requires **XeLaTeX** (Urdu script needs proper RTL shaping; pdflatex won't work).

Install once on macOS:
```sh
brew install --cask mactex            # ~5GB; or install BasicTeX + missing packages on demand
```

Install the Urdu Nastaliq font (one-time):
```sh
# Noto Nastaliq Urdu — free, from Google Noto
open https://fonts.google.com/noto/specimen/Noto+Nastaliq+Urdu
# download the family, install Noto_Nastaliq_Urdu/static/NotoNastaliqUrdu-Regular.ttf
```

Build:
```sh
cd paper/
xelatex bhai.tex
biber bhai            # or: bibtex bhai
xelatex bhai.tex
xelatex bhai.tex      # twice more to resolve refs
```

Output: `bhai.pdf`.

## Target venues

In rough order of fit:
- **TaPP** (USENIX Theory and Practice of Provenance) — workshop, fastest path, ideal niche
- **PLDI** / **OOPSLA** — programming-language venues; the kinship-typed angle suits PL audience
- **SIGMOD** / **VLDB** — data-systems venues; the lineage angle suits DB audience
- **CCS** / **USENIX Security** — for the cryptographic-testimony angle

For first submission, recommend retargeting from PLDI to TaPP if reviewers push back on novelty-vs-pragmatism — TaPP is friendlier to implementation-driven contributions.

## Status

First-cut draft; needs:
- author affiliations and ORCID
- formal theorems for hash properties (currently informal)
- larger-scale evaluation (the case studies are 4–10 nodes; reviewers will want 10k–100k)
- proper related-work depth on PASS-line provenance literature
- copy-edit pass for academic register
