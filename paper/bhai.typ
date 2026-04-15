// بھائی-lang — research paper (Typst version)
// Compile with: typst compile bhai.typ
// Requires: Noto Nastaliq Urdu font installed (macOS ships with it).

#set document(title: "Bhai-lang: Kinship-Typed Lineage", author: "Adil")
#set page(paper: "us-letter", margin: 0.85in)
#set text(font: "New Computer Modern", size: 10pt, lang: "en")
#set par(justify: true, leading: 0.55em)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => [
  #v(10pt)
  #set text(size: 12pt, weight: "bold")
  #it
  #v(4pt)
]

#show heading.where(level: 2): it => [
  #v(6pt)
  #set text(size: 10.5pt, weight: "bold", style: "italic")
  #it
  #v(2pt)
]

// Helper: Urdu text in Nastaliq
#let ur(body) = text(font: "Noto Nastaliq Urdu", size: 1.1em)[#body]

// Helper: code block
#show raw.where(block: true): block.with(
  fill: rgb("#f6f6f4"),
  inset: 8pt,
  radius: 3pt,
  width: 100%,
)

// ─── Title ───────────────────────────────────────────────
#align(center)[
  #v(20pt)
  #text(size: 17pt, weight: "bold")[
    #ur[بھائی]-lang: A Kinship-Typed Programming Language \
    for Cryptographically Verifiable Data Lineage
  ]
  #v(10pt)
  #text(size: 11pt)[Adil] \
  #text(size: 9pt, style: "italic")[Karachi]
  #v(15pt)
]

// ─── Abstract ────────────────────────────────────────────
#block(width: 100%, inset: (left: 24pt, right: 24pt))[
  #text(size: 9.5pt)[
    *Abstract.* Conventional data-lineage tools (OpenLineage, DataHub,
    Marquez) treat provenance as an annotation layer over heterogeneous
    systems and recognise at most three coarse edge types:
    #smallcaps[derived_from], #smallcaps[depends_on], and
    #smallcaps[contains]. We argue this vocabulary is structurally
    insufficient for the lineage questions modern compliance, ML
    governance, and AI auditability actually demand.

    We present #ur[بھائی]-lang, a programming language in which data
    lineage is the runtime substrate rather than a post-hoc instrumentation
    layer. Every value is a #emph[#ur[کردار]] (#emph[kirdaar] — character)
    carrying its ancestry; every primitive operation extends a typed
    kinship graph in which $tilde$50 distinct edges encode relationships
    such as #ur[سوتن] (#emph[sautan]: fallback parent), #ur[سمدھی]
    (#emph[samdhi]: cross-table-join co-source), #ur[استاد]
    (#emph[ustaad]: training-data → model), and #ur[گواہ] (#emph[gawah]:
    audit observer). The vocabulary is drawn directly from Urdu kinship
    terms, for which English-derived data-systems language has no
    equivalents.

    Every #ur[کردار] is content-addressable via a Merkle-chained SHA-256
    we call #ur[گواہی] (#emph[gawahi] — testimony). The cryptographic
    structure makes lineage #emph[verifiable] rather than vendor-asserted:
    a recipient of a serialised lineage graph can confirm, without
    trusting the producer, that no value or edge has been altered.

    We describe the language design, type system, cryptographic protocol,
    and a $tilde$1,500-line reference implementation. We illustrate the
    approach on four case studies: GDPR delete cascade, ML feature PII
    leak detection, JOIN provenance via a kinship-typed merge, and
    tamper detection. We argue that lineage-native runtime semantics are
    technically necessary, vocabulary-rich kinship typing is conceptually
    overdue, and Merkle-chained provenance is procurable.
  ]
]

#v(15pt)

// ─── Body in two columns ─────────────────────────────────
#show: rest => columns(2, gutter: 14pt, rest)

= Introduction

Data-lineage failures are expensive. The European Union has issued more
than €4.5 billion in GDPR penalties since 2018, a substantial fraction
tied to inadequate ability to identify and delete derived data on
request @gdpr-fines. ML governance teams cannot reliably answer "did
sensitive feature $X$ contribute to this prediction?"
@mlflow-lineage @featurestore. AI agents call other agents in
nondeterministic chains whose provenance disappears within hours
@ai-agent-provenance.

The dominant industry response is bolt-on instrumentation. Tools such
as OpenLineage @openlineage, DataHub @datahub, and Marquez @marquez
expose APIs that data-producing systems may call to record lineage
events. They are voluntary, eventually consistent, and — critically —
operate over a vocabulary of three relationships: #smallcaps[derived_from],
#smallcaps[depends_on], and #smallcaps[contains]. This impoverished
type system cannot distinguish

- a value derived from training data versus one derived from inference
  inputs;
- a join between two source tables versus an inheritance from a single
  one;
- a fallback computation that consulted a backup source versus a
  primary path;
- an externally imported value versus a locally derived one;
- a tampered ancestor versus a legitimate one.

Yet these are exactly the distinctions that compliance, ML, and
security teams are paid to enforce. The vocabulary gap is not a
missing feature; it is structural.

== Insight

Human kinship languages have $tilde$50 distinct relationship terms
because we needed them. Cousin-via-paternal-uncle (#ur[چچازاد]) is
computationally distinct from cousin-via-maternal-aunt
(#ur[خالہ‌زاد]); co-wife (#ur[سوتن]) is computationally distinct
from sister (#ur[بہن]); witness (#ur[گواہ]) is computationally
distinct from guarantor (#ur[ضامن]). Karachi Urdu, as a melting-pot
dialect, encodes one of the world's richest kinship vocabularies.
Mapping this vocabulary onto data lineage yields exactly the
relationship distinctions data systems have always lacked names for.

== Contributions

+ A programming-language design (#ur[بھائی]-lang) in which lineage is
  the runtime substrate rather than an annotation layer (§3).

+ A kinship-typed lineage edge ontology of $tilde$50 distinct
  relationships, with formal computational semantics for the core
  subset (§4).

+ A cryptographic testimony protocol (#ur[گواہی]) that makes lineage
  Merkle-chain verifiable, with $O(N)$ verification cost (§5).

+ A reference implementation in $tilde$1,500 lines of Python and four
  case studies (§6, §7).

= Background and the Vocabulary Gap

== The PROV-DM lineage

The W3C PROV data model @prov-dm formalises provenance as a tripartite
graph of #emph[Entities], #emph[Activities], and #emph[Agents],
connected by edges including `wasGeneratedBy`, `wasDerivedFrom`,
`wasAssociatedWith`, and `actedOnBehalfOf`. PROV-DM is influential and
well-specified, but its edge alphabet is small and operates at the
granularity of Activities (jobs, runs) rather than individual values.
Implementations such as OpenLineage @openlineage preserve the PROV-DM
granularity but reduce the edge vocabulary further, typically to a
single #smallcaps[output_of] relation.

== Capability and information-flow languages

Capability-secure languages (E @e-language, Pony @pony, Monte @monte)
carry authority alongside values, ensuring that holding a reference
confers the right to use it. Information-flow type systems
(FlowCaml @flowcaml, Jif @jif, LIO @lio) propagate confidentiality
labels through computation. Both bodies of work bear on lineage but
treat it as a property of #emph[access] or #emph[label], not of
derivation #emph[relationship]. They give us secrecy bits, not kinship
structure.

== ML lineage tools

Feast @feast, Tecton @tecton, MLflow @mlflow, and Weights & Biases
@wandb record feature and experiment lineage. Their semantics are
nominal — every artefact has a name and a parent set — but the edges
are typed only as #smallcaps[produced] or #smallcaps[used]. "Did this
feature derive from sensitive data?" is, in 2025, still answered by
manual code audit at every team we have spoken to.

== Verifiable provenance

Git @git pioneered the use of a Merkle DAG to make commit history
tamper-evident. Certificate Transparency @ct-rfc extends the idea to
TLS certificate logs. Datalog-with-provenance research
@provenance-semirings expresses lineage as a semiring annotation on
relational query results. None of this work has, to our knowledge, been
carried into a runtime where individual program values are themselves
Merkle-chained.

== The vocabulary gap, quantified

#figure(
  table(
    columns: 2,
    align: (left, right),
    stroke: 0.4pt,
    [*System*], [*Distinct edge types*],
    [OpenLineage @openlineage], [3],
    [DataHub @datahub], [4],
    [Marquez @marquez], [3],
    [PROV-DM @prov-dm], [13],
    [Atlan @atlan], [5],
    [*#ur[بھائی]-lang* (this work)], [*$tilde$50*],
  ),
  caption: [Edge-type expressivity across data-lineage systems.
    PROV-DM is the formal academic baseline; commercial tools have
    collapsed it further. #ur[بھائی]-lang ships with $tilde$50 typed
    edges drawn from Urdu kinship vocabulary.],
)

= Design: Lineage as Runtime Substrate

== The #ur[کردار] value model

Every value in #ur[بھائی] is a #ur[کردار] (kirdaar) — a record
carrying:

- a primitive value (number, string, boolean, list, null);
- a set of typed parent edges ${(r_i, k_i)}$, each $r_i$ a relation
  label drawn from the rishta vocabulary, $k_i$ another #ur[کردار];
- a consent state ${$#smallcaps[vip], #smallcaps[do-numri],
  #smallcaps[shopping]$}$;
- an optional trust label ${$#ur[جانی], #ur[بھائی], #sym.bot$}$;
- an optional sensitivity label ${$#ur[حساس], #sym.bot$}$;
- an adversarial bit #ur[دشمن];
- an origin marker ${$#ur[لے_پالک], #ur[رضاعی], #sym.bot$}$.

== Operations and edge construction

Every primitive operation #emph[constructs] edges. Binary arithmetic
`c = a + b` yields a fresh #ur[کردار] $c$ with
#h(0pt) parents$(c) = {(#ur[باپ], a), (#ur[ماں], b)}$ — left operand
as paternal lineage, right operand as maternal. Higher-arity operations
(joins, training declarations) construct correspondingly typed edges.

There is no opt-in. Lineage is created #emph[by construction] as a
side effect of computation; it cannot be omitted, forgotten, or buggy.

== Propagation rules

The runtime enforces three propagation laws on every operation,
illustrated for the binary case:

#align(center)[
  trust$(c)$ = max(trust$(a)$, trust$(b)$) \
  sens$(c)$ = sens$(a)$ #sym.or sens$(b)$ \
  dushman$(c)$ = dushman$(a)$ #sym.or dushman$(b)$
]

Trust is monotone under join, sensitivity and adversarial flags
propagate as taint, and consent demotes upon any compromised ancestor.

= The #ur[رشتہ] Type System

== Edge vocabulary

The full ontology contains $tilde$50 entries derived from the kinship
structure of Urdu, including paternal-versus-maternal nephew
(#ur[بھتیجا] vs #ur[بھانجا]), co-brothers-in-law via married sisters
(#ur[ہم‌زلف]), milk-kin (#ur[رضاعی]), and adopted (#ur[لے‌پالک]) —
each with a distinct semantic. Selected core edges:

#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    stroke: 0.4pt,
    inset: 5pt,
    [*Edge*], [*Literal Urdu*], [*Computational semantic*],

    [#ur[باپ]], [father], [primary derivation (left operand)],
    [#ur[ماں]], [mother], [primary derivation (right operand)],
    [#ur[استاد]], [teacher], [training-data → model edge],
    [#ur[شاگرد]], [apprentice], [inverse of #ur[استاد]],
    [#ur[سوتن]], [co-wife], [fallback parent / `COALESCE`],
    [#ur[گواہ]], [witness], [read-only audit snapshot],
    [#ur[بیوی] / #ur[شوہر]], [wife / husband], [JOIN — merged value],
    [#ur[سمدھی]], [co-in-laws], [JOIN-induced cross-source rel.],
    [#ur[ہم‌زلف]], [co-brothers-in-law], [parallel pipelines, common JOIN],
    [#ur[بھتیجا]], [paternal nephew], [paternal-side sibling pipeline],
    [#ur[بھانجا]], [maternal nephew], [maternal-side sibling pipeline],
    [#ur[چچازاد]], [paternal cousin], [shares paternal grandparent],
    [#ur[رضاعی]], [milk-kin], [cached / mirrored copy],
    [#ur[لے‌پالک]], [adopted], [externally imported],
    [#ur[دشمن]], [enemy], [adversarial mark; do not derive from],
  ),
  caption: [Core typed lineage edges and their computational semantics.
    Each edge is a Karachi-Urdu kinship term whose social meaning maps
    directly onto a data-systems relationship that conventional vocabulary
    cannot name.],
)

== Why vocabulary matters

Three edges in particular have no name in any data-systems tool we
surveyed:

*#ur[سوتن] (co-wife) as fallback parent.* A common pattern in
resilient computation is: derive a value from a primary source, but
fall through to an alternative if the primary is unavailable. SQL
implements this as `COALESCE`; ML pipelines implement it as model
ensembles or A/B tests. In each case, the #emph[relationship] between
the two parents and the child is absent from the lineage graph.
#ur[بھائی] encodes it as a #ur[سوتن] edge — declaratively, an
alternative parent of equal lineage standing.

*#ur[سمدھی] (co-in-laws) as JOIN-induced relation.* When tables `users`
and `orders` are joined, the rows of the result are children of both.
The relationship between `users` and `orders` themselves — they have
shared descendants — is what kinship terms #emph[co-in-laws]. Every
JOIN in a data warehouse creates a #ur[سمدھی] relationship; no lineage
tool surfaces it. #ur[بھائی] does so by construction.

*#ur[استاد] (teacher) as training edge.* The training-data-to-model
edge is the most-asked-about relationship in AI governance and the
least-typed in lineage tools. #ur[بھائی] represents it directly: a
model is a #ur[شاگرد] of its training data; the
`#ur[استاد_چین] <model>` query walks only #ur[استاد] edges, yielding
the complete training provenance.

= Cryptographic Testimony (#ur[گواہی])

== Threat model

We assume:
- the producer of a serialised lineage graph may be adversarial;
- the recipient (auditor, regulator, downstream consumer) wishes to
  verify the lineage without trusting the producer;
- the recipient has the public hash function but no shared secret;
- integrity, not confidentiality, is the property of interest.

This is the standard threat model for tamper-evident logs.

== Hash construction

For every #ur[کردار] $k$ we define:

#align(center)[
  gawahi$(k)$ = $H$(enc($k.v, k.tau, P_k$))
]

where $H$ is SHA-256, $k.v$ is the primitive value, $k.tau$ is the
tuple of consent / trust / sensitivity / adversarial / origin tags, and

#align(center)[
  $P_k$ = sort(${(r_i, $ gawahi$(k_i)) : (r_i, k_i) in$ parents$(k)}$)
]

The encoding `enc` is canonical JSON. Because gawahi is defined
recursively over parent hashes, the resulting structure is a Merkle DAG
isomorphic to the lineage graph itself.

== Properties

*Determinism.* Two #ur[کردار] with identical values, tags, and parent
hashes have identical #ur[گواہی], regardless of name, allocation order,
or session.

*Tamper-evidence.* Modifying any field of any #ur[کردار] alters its
hash and, by recursion, the hash of every descendant. A single-bit
change in a root #ur[کردار] invalidates every #ur[گواہی] below it.

*Verification cost.* Linear in the number of #ur[کردار]: each is hashed
once, each parent edge contributes a constant-size string. For the
audit graphs we construct in §7 (10–100 nodes), verification completes
in milliseconds.

*What it does not catch.* A producer can elide #ur[کردار] entirely
from the serialised graph — the hash of the omitted node is simply
absent. #ur[بھائی] addresses elision orthogonally via globals tracking,
but a determined producer with no external commitment can still omit.
We discuss external anchoring in §8.

== Round-trip verification

The `#ur[سنبھال]` primitive emits, alongside each #ur[کردار], its
#ur[گواہی]. The `#ur[اٹھا]` primitive recomputes hashes after
reconstructing the graph and aborts with the offending name on
mismatch. We have validated this end-to-end on a graph of 5
#ur[کردار], including a manual single-byte tamper test.

= Implementation

The reference implementation is two tree-walking interpreters in
$tilde$1,500 lines of Python:

- `bhai.py` — a general-purpose language with closures, control flow,
  lists, and a 19-builtin standard library (file IO, time, math,
  regex). Useful for writing real programs that interact with the
  operating system.
- `rishta.py` — the lineage-native DSL described in this paper. No
  control flow; programs are sequences of declarations and queries
  against the lineage graph.

Both interpreters share the same lexer architecture (Urdu identifier
handling, Urdu digit literals #ur[۰]–#ur[۹], Urdu punctuation #ur[،] /
#ur[۔]). They support modules via `#ur[منگوا]` (cycle-detected
import). The runtime is a graph of #ur[کردار] objects with
cached-on-demand hash computation. Persistence emits canonical JSON;
load verifies hashes before exposing globals.

The implementation is open-source @bhai-repo and runs on Python 3.8+
with no third-party dependencies.

= Case Studies

== GDPR delete cascade

```
کردار صارف = "ali@karachi.pk" حساس جانی
کردار پروفائل = صارف + " (کراچی)"
کردار رپورٹ = پروفائل + " — اپریل 2026"

تپکا صارف
# ⚠ صارف تپکا — 4 اولاد دو نمبری ہوئی
پھوٹ رپورٹ
# رپورٹ: (ہائیڈ) [دو نمبری] [جانی] [حساس]
```

A single #ur[تپکا] (revoke) call cascades through every value derived
from #ur[صارف], marking each #ur[دو نمبری] (tainted). Reads of tainted
#ur[کردار] return a hidden sentinel rather than the underlying value.
The compliance team's three-week audit becomes a four-token statement.

== ML feature PII leak detection

```
کردار سی_این_آئی_سی = 4210112345678 حساس
کردار عمر = 25
کردار ماڈل_فیچر = سی_این_آئی_سی + عمر
رساؤ ماڈل_فیچر
# ⚠ حساس رساؤ — 2 حساس جد ملے:
#   ← خود: ماڈل_فیچر  [VIP] [حساس]
#   ← باپ: سی_این_آئی_سی [VIP] [حساس]
```

The #ur[رساؤ] (leak) query walks ancestors filtered by sensitivity.
Any feature whose lineage includes a #ur[حساس] #ur[کردار] is flagged.
This addresses the canonical question of ML governance — #emph[did
sensitive data influence this prediction?] — by lineage walk rather
than code review.

== JOIN provenance via #ur[سمدھی]

```
کردار صارفین = 100 حساس
کردار آرڈرز = 50
جوڑ صارفین سے آرڈرز بنا فل_ٹیبل

سمدھی صارفین
#   ↔ آرڈرز = 50 [VIP] (via فل_ٹیبل)
```

The #ur[جوڑ] (join) primitive constructs #ur[بیوی] / #ur[شوہر] edges
from the result to each source. The induced #ur[سمدھی] relationship
between sources is queryable on demand. This is the cross-table "what
touches what" question every BI team computes ad hoc; here it is
graph-intrinsic.

== Tamper detection

We construct a 5-node graph, save it via #ur[سنبھال], and externally
modify the value of one #ur[کردار] in the resulting JSON. The
subsequent #ur[اٹھا] aborts with: \
`⚠ گواہی نا کام: 'صارف' میں چھیڑ چھاڑ ہوئی!` \
expected `a6b3b9ea073d…`, file says `e169a0b214be…`

The hash chain immediately localises tampering to the responsible
#ur[کردار].

= Discussion

== What this buys

The combination of (a) lineage-by-construction, (b) kinship-typed
edges, and (c) cryptographic testimony eliminates three classes of bug
at once: lineage absence, lineage misclassification, and lineage
tampering. Compliance audits that today require multi-person
quarter-long efforts collapse to graph queries that complete in
milliseconds and produce machine-verifiable artefacts.

== Limitations

*Performance.* The reference interpreter is tree-walking. Realistic
workloads will require a bytecode VM and incremental hash maintenance.

*Mutation.* The current language is value-immutable. A
versioned-mutation primitive (#ur[سافٹویئر اپڈیٹ]) is on the roadmap.

*Elision.* Cryptographic testimony catches modification but not
omission. External anchoring (commitment to a public log such as
Certificate Transparency or a blockchain) closes this gap; the
integration is straightforward but unimplemented.

*Adoption.* The Urdu-script keyword choice is a cultural commitment.
We expect a productionised English-keyword variant will be required for
enterprise adoption; the underlying semantics transfer unchanged.

== Cultural framing

The decision to express the type system in Urdu kinship terms is
deliberate and not decorative. Karachi Urdu's vocabulary is the most
relationship-rich substrate we found; the language design is downstream
of the vocabulary, not upstream of it. We conjecture that other
natural-language kinship systems (Tamil, Mandarin, Yoruba) would yield
comparable insight, and that programming-language design has
historically been impoverished by drawing only from English-derived
ontologies.

== Future work

Four directions are immediate: (i) external anchoring of #ur[گواہی]
to public logs; (ii) inter-organisation lineage-passport format for
verifiable hand-off between data producers and consumers; (iii)
compile-to-Python embedding so existing codebases can opt in
incrementally; (iv) more typed edges from the kinship vocabulary not
yet exposed.

= Related Work

Beyond the work surveyed in §2: PASS @pass pioneered OS-level
provenance capture; Burrito @burrito captured scientific-workflow
provenance; Carmine @carmine explored provenance for distributed
dataflow. None typed provenance edges beyond a small fixed alphabet,
and none made provenance cryptographically verifiable at the value
level.

In the cryptographic-log space, Trillian @trillian is the production
substrate behind Certificate Transparency and presents a general
append-only Merkle log. Our #ur[گواہی] differs in being structured
over the lineage DAG itself, not over an opaque event sequence.

In programming-language design, work on effect systems @koka @frank
and capability languages most closely parallels ours in treating a
meta-property of values (effects, authority) as part of the type
system. #ur[بھائی] extends this tradition to lineage, with the
distinguishing feature that the relationship — not just the property —
is typed.

= Conclusion

We have argued that data-lineage tools have been built on an
impoverished vocabulary of three to thirteen edge types, and that this
vocabulary gap is responsible for a wide class of unanswerable
compliance, ML, and AI auditability questions. We presented
#ur[بھائی]-lang, a programming language in which lineage is the runtime
substrate, edges are typed from a $tilde$50-term Karachi-Urdu kinship
vocabulary, and every value is content-addressable through a
Merkle-chained SHA-256 we call #ur[گواہی]. The reference implementation
is small ($tilde$1,500 lines of Python), demonstrates the approach
end-to-end, and is freely available.

The contribution of this paper is not the implementation but the
conceptual move: #emph[lineage is not an annotation problem; it is a
vocabulary problem solved by making derivation relationships
first-class]. We invite the data-systems and programming-language
communities to consider what other relationship vocabularies — drawn
from the world's languages, not from English alone — might similarly
enrich our tools.

#bibliography("refs.bib", style: "ieee")
