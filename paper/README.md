# Paper

Research paper formalizing the رشتہ semantics, kinship-typed lineage edges, and گواہی cryptographic protocol.

Two source variants are kept in sync:
- `rishta.typ`, Typst source (recommended; clean RTL handling, single-binary compiler).
- `rishta.tex`, LaTeX source (XeLaTeX); retained for venue submission compatibility.

## Compile (recommended: Typst)

```sh
brew install typst       # ~50MB single binary
cd paper/
typst compile rishta.typ   # → rishta.pdf
```

Requires Noto Nastaliq Urdu font. macOS ships it by default. On Linux: `apt install fonts-noto-nastaliq` or download from Google Noto.

## Compile (LaTeX)

Requires XeLaTeX (Urdu script needs proper RTL shaping; pdflatex won't work). Note: tectonic 0.16+ segfaults on Nastaliq shaping on macOS Tahoe; use full TeX Live or MacTeX instead.

```sh
brew install --cask mactex   # ~5GB
cd paper/
xelatex rishta.tex && bibtex rishta && xelatex rishta.tex && xelatex rishta.tex
```

Output: `rishta.pdf`.

## Target venues

In rough order of fit:
- TaPP (USENIX Theory and Practice of Provenance). Workshop, fastest path, ideal niche.
- PLDI, OOPSLA. Programming-language venues. The kinship-typed angle suits PL audiences.
- SIGMOD, VLDB. Data-systems venues. The lineage angle suits DB audiences.
- CCS, USENIX Security. For the cryptographic-testimony angle.

For first submission, retarget from PLDI to TaPP if reviewers push back on novelty-vs-pragmatism. TaPP is friendlier to implementation-driven contributions.

## Status

First-cut draft. Open work:
- Author ORCID.
- Formal theorems for hash properties (currently informal).
- Larger-scale evaluation. The case studies are 4 to 10 nodes; reviewers will want 10k to 100k.
- Deeper related-work coverage on PASS-line provenance literature.
- Copy-edit pass for academic register.
