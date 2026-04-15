# Paper

Research paper formalizing the رشتہ semantics, kinship-typed lineage edges, and گواہی cryptographic protocol.

Two source variants are kept in sync:
- `bhai.typ` — **Typst** source (recommended; clean RTL handling, single-binary compiler)
- `bhai.tex` — **LaTeX** source (XeLaTeX); kept for venue submission compatibility

## Compile (recommended: Typst)

```sh
brew install typst       # ~50MB single binary
cd paper/
typst compile bhai.typ   # → bhai.pdf
```

Requires **Noto Nastaliq Urdu** font. macOS ships it by default. Linux: `apt install fonts-noto-nastaliq` or download from Google Noto.

## Compile (LaTeX)

Requires **XeLaTeX** (Urdu script needs proper RTL shaping; pdflatex won't work). Note: tectonic 0.16+ segfaults on Nastaliq shaping on macOS Tahoe — use full TeX Live / MacTeX instead.

```sh
brew install --cask mactex   # ~5GB
cd paper/
xelatex bhai.tex && bibtex bhai && xelatex bhai.tex && xelatex bhai.tex
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
