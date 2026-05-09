# رشتہ Rishta

A Karachi-native programming language with cryptographically verifiable data lineage as a first-class primitive.

Data privacy (GDPR, CPRA), ML feature provenance, and AI agent auditability are problems conventional languages punt to libraries. Rishta makes them intrinsic. Every value carries its ancestry. Consent revocation cascades automatically through every derived computation. PII leaks are detectable with a single query. Every lineage claim is cryptographically signed, auditable without trusting the vendor.

The kinship vocabulary is drawn specifically from Karachi Urdu, a port-city creole shaped by Mohajir, Sindhi, Punjabi, Memon, Gujarati, Marwari, Persian, and English contact. About 50 distinct lineage relationships have natural names in this register that English data-systems vocabulary lacks: `سوتن` (co-wife) for fallback parents, `سمدھی` (co-in-laws) for cross-table joins, `استاد` (teacher) for training-data edges, `گواہ` (witness) for audit observers, and so on.

> Not the same as [DulLabs/bhai-lang](https://github.com/DulLabs/bhai-lang) (Singh and Tripathi, 2021). That project is a Hindi-flavored interpreter in romanized Latin script, designed for entertainment. Rishta is its semantic opposite: Urdu-script, lineage-native, research-aimed. The projects share neither vocabulary nor goals.

---

## Status

Experimental. The repo ships two interpreters that share lexer architecture and import semantics:

| File | Purpose |
|---|---|
| [`bhai.py`](bhai.py) | General-purpose dialect. Variables, functions, closures, control flow, lists, 19-builtin standard library. |
| [`rishta.py`](rishta.py) | Lineage-native dialect. The `رشتہ` primitive runtime: lineage, consent, trust, sensitivity, cryptographic testimony. |

The novelty lives in `rishta.py`. See [The رشتہ primitive](#the-رشتہ-primitive).

---

## Requirements

Python 3.8+. No third-party dependencies.

## Install and run

```sh
git clone git@github.com:adiled/rishta-lang.git
cd rishta-lang

python3 bhai.py    examples/factorial.bhai
python3 rishta.py  examples/rishta_leak.bhai
python3 rishta.py  examples/rishta_gdpr.bhai
python3 rishta.py  examples/rishta_proof.bhai
```

---

## Hello, دنیا

```
# examples/hello.bhai
پھوٹ "ابے اوئے، سلام دنیا!"

سن شہر = "کراچی"
اگر شہر == "کراچی" {
    پھوٹ "بھائی، یہ تو اپنا شہر ہے"
}
```

Run with `python3 bhai.py examples/hello.bhai`.

---

## Language reference, `bhai.py`

### Keywords

| Keyword | Transliteration | Role | Karachi origin |
|---|---|---|---|
| `سن` | sun | variable declaration (let) | "listen up" |
| `کام` | kaam | function declaration | "work" |
| `کلٹی` | kalti | return | "flip back" (also: escape, flee) |
| `اگر` / `ورنہ` | agar / warna | if / else | |
| `جبتک` | jabtak | while | "as long as" |
| `ہرایک` ... `میں` | har-ek ... mein | for-each ... in | |
| `شاٹ` | shaaT | break | "short-circuit" (`dimaagh shaat`) |
| `کٹا` | kaTa | continue | "cut, skip past" |
| `پھوٹ` | phooT | print | "burst out, say it" |
| `پوچھ` | pooch | input() | "ask" |
| `جنین` / `کدو` / `نلا` | janeen / kaddu / nulla | true / false / null | genuine / pumpkin-dud / null |
| `اور` / `یا` / `نا` | aur / ya / naa | and / or / not | |
| `منگوا` | mangwa | import | "summon, bring" |

### Operators

Arithmetic `+ - * / %`, comparison `== != < > <= >=`, logical `&& || !`, assignment `=`, grouping `( ) { } [ ]`. Urdu punctuation: `،` as comma, `۔` as semicolon. Numeric literals accept Urdu digits (`۵۰` is 50). Strings use `"..."` with standard escapes.

### Built-ins

Core list and type ops:

| Function | Purpose |
|---|---|
| `لمبائی(x)` | length of string or list |
| `قسم(x)` | type name |
| `نمبر(x)` / `لفظ(x)` | cast to number, cast to string |
| `ڈال(list, x)` / `نکال(list)` | push, pop |
| `ترتیب(n)` / `ترتیب(a, b)` / `ترتیب(a, b, step)` | range |

`فائل` (file IO):

| Function | Purpose |
|---|---|
| `فائل_پڑھ(path)` | read text |
| `فائل_لکھ(path, text)` | write (overwrite) |
| `فائل_ضمیمہ(path, text)` | append |
| `فائل_موجود(path)` | exists |
| `فائل_حذف(path)` | delete (idempotent) |

`وقت` (time):

| Function | Purpose |
|---|---|
| `وقت_ابھی()` | current Unix timestamp |
| `وقت_فارمیٹ(ts)` | ISO 8601 string |

`حساب` (math):

| Function | Purpose |
|---|---|
| `حساب_جذر(x)` / `حساب_طاقت(b, e)` | sqrt, pow |
| `حساب_مطلق(x)` / `حساب_فرش(x)` / `حساب_چھت(x)` | abs, floor, ceil |
| `حساب_بے_ترتیب()` | random float in [0, 1) |
| `حساب_پائی()` / `حساب_ای()` | π, e |

`جال` (regex):

| Function | Purpose |
|---|---|
| `جال_میچ(pat, text)` | full match, returns bool |
| `جال_ڈھونڈ(pat, text)` | first match or null |
| `جال_تمام(pat, text)` | list of all matches |
| `جال_بدل(pat, repl, text)` | substitute |

See [`examples/stdlib_demo.bhai`](examples/stdlib_demo.bhai) for a real log-analyzer program using all four modules.

### Example, recursion + loops

```
کام فیکٹوریل(ن) {
    اگر ن <= 1 { کلٹی 1 }
    کلٹی ن * فیکٹوریل(ن - 1)
}

ہرایک ای میں ترتیب(1, 6) {
    پھوٹ ای, "! =", فیکٹوریل(ای)
}
```

### Example, closures

```
کام بنانے_والا(شروع) {
    سن گنتی = شروع
    کام اگلا() {
        گنتی = گنتی + 1
        کلٹی گنتی
    }
    کلٹی اگلا
}

سن کاؤنٹر = بنانے_والا(10)
پھوٹ کاؤنٹر()   # 11
پھوٹ کاؤنٹر()   # 12
```

---

## The رشتہ primitive

The novel contribution. Every value is a `کردار` (entity) carrying its lineage. Operations attach parent edges. Consent revocation cascades.

### The value model

Each `کردار` carries:

| Property | Values | Semantics |
|---|---|---|
| `value` | any | the underlying datum |
| `parents` / `children` | `{rel → کردار}` | automatic lineage graph |
| `consent` | `VIP`, `دو نمبری`, `شاپنگ` | clean, tainted-via-ancestry, revoked |
| `trust` | `جانی`, `بھائی`, none | intimate, trusted, default |
| `sensitivity` | `حساس`, none | PII / sensitive |
| `dushman` | flag | adversarial mark |
| `origin` | `لے_پالک`, `رضاعی`, none | externally imported, cached/mirrored |

Propagation rules, enforced at every operation:

- Consent. If any ancestor is revoked (`شاپنگ`), the descendant becomes `دو نمبری` (tainted) and its value is hidden on read.
- Trust. Derived values inherit the maximum trust of their parents (`جانی` > `بھائی` > none).
- Sensitivity. Derived values inherit `حساس` if any parent is `حساس`.
- Adversarial. Same OR-propagation as sensitivity.

### Declaration

```
کردار <name> = <expr> [جانی|بھائی] [حساس]
```

```
کردار عمر = 25
کردار ای_میل = "ali@karachi.pk" جانی
کردار سی_این_آئی_سی = 4250112345678 حساس جانی
```

### Automatic lineage

Every binary operation creates a new `کردار` whose parents are the operands. Left becomes `باپ`, right becomes `ماں`.

```
کردار ا = 10
کردار ب = 20
کردار ج = ا + ب     # ج.parents = {باپ: ا, ماں: ب}
شجرہ ج
```

### Primitives

| Statement | Effect |
|---|---|
| `تپکا <name>` | revoke consent, cascade. Every descendant becomes `دو نمبری`. |
| `شجرہ <name>` | print full lineage tree with consent, trust, sensitivity tags |
| `اولاد <name>` | list all descendants |
| `جد <name>` | list all ancestors |
| `رساؤ <name>` | PII leak query, lists every `حساس` ancestor |
| `رشتہ: <a> کا <rel> <b>` | explicitly assert a lineage edge |
| `رشتہ <a> سے <b>` | query the rishta path between two `کردار` |
| `پھوٹ <expr>` | print with consent, trust, sensitivity tags |

### Modules (v0.5)

```
منگوا "<path/to/file.bhai>"
```

Imports another `.bhai` file into the current namespace. Path is resolved relative to the importing file. Cycles are skipped (each absolute path loads at most once). Imported `کردار` keep their consent, trust, sensitivity, lineage intact. They are indistinguishable from locally-declared ones. Works in both `bhai.py` and `rishta.py`. See [`examples/rishta_modules.bhai`](examples/rishta_modules.bhai).

### Cryptographic testimony (v0.9)

Every `کردار` has a content-addressable proof: a SHA-256 hash computed deterministically from its value, tags, and the sorted hashes of its parents (a Merkle chain over the شجرہ).

| Statement | Effect |
|---|---|
| `ثبوت <name>` | print the SHA-256 hash of `<name>`'s lineage |
| `سنبھال "..."` | save the entire reachable شجرہ as JSON. Each کردار carries its `گواہی` field. |
| `اٹھا "..."` | load. Verifies every `گواہی`. Mismatch aborts with the offending name. |

The audit JSON is plain text. A recipient can verify the chain without trusting the producer. Tamper a single value and every descendant's proof fails. See [`examples/rishta_proof.bhai`](examples/rishta_proof.bhai).

### Typed-edge primitives (v0.3)

Five Karachi kinship vocabulary edges that conventional lineage tools have no word for:

| Statement | Edge created | Computational meaning |
|---|---|---|
| `استاد <model> = <data>` | `استاد` (teacher) | training-data to model lineage. The most-asked edge in ML auditing. |
| `استاد_چین <name>` | (query) | walk the `استاد` chain. List every training source up the lineage. |
| `سوتن <child> = <fallback>` | `سوتن` (co-wife) | fallback parent, `COALESCE`, A/B alternative source |
| `گواہ <name> = <source>` | `گواہ` (witness) | read-only audit snapshot of source's value at this moment |
| `جوڑ <a> سے <b> بنا <c>` | `بیوی` + `شوہر` | JOIN. `c` is a marriage of `a` and `b`. Sources are implicitly `سمدھی` (co-in-laws). |

### Adversarial / external / cached (v0.7)

| Statement | Effect |
|---|---|
| `دشمن <name>` | mark `کردار` as adversarial (poisoned, attacker-controlled). Cascades to descendants. Any binary op involving an adversarial `کردار` produces an adversarial child. |
| `دشمن_رساؤ <name>` | list every adversarial ancestor. Security audit. |
| `لے_پالک <name> = <expr>` | declare `کردار` as externally imported (third-party API, file blob). No native lineage. Tagged `[لے_پالک]`. |
| `رضاعی <name> = <source>` | `کردار` is a cached or mirrored copy of `<source>`. Trust, sensitivity, dushman inherited. Edge type `رضاعی`. |
| `سمدھی <name>` | list co-join partners. Every `کردار` that has been `جوڑ`'d with `<name>`. |

### Example, GDPR cascade

```
کردار صارف = "ali@karachi.pk" حساس جانی
کردار پروفائل = صارف + " (کراچی)"
کردار رپورٹ = پروفائل + ", اپریل 2026"

تپکا صارف
# ⚠ صارف تپکا, 4 اولاد دو نمبری ہوئی

پھوٹ رپورٹ
# رپورٹ: (ہائیڈ) [دو نمبری] [جانی] [حساس]
```

### Example, PII leak detection

```
کردار سی_این_آئی_سی = 4250112345678 حساس
کردار عمر = 25
کردار ماڈل_فیچر = سی_این_آئی_سی + عمر       # auto-tagged حساس
کردار موسم_اسکور = عمر + 10                  # clean

رساؤ ماڈل_فیچر
# ⚠ ماڈل_فیچر میں حساس رساؤ, 2 حساس جد ملے:
#   ← خود: ماڈل_فیچر  = 4250112345703 [VIP] [حساس]
#   ← باپ: سی_این_آئی_سی = 4250112345678 [VIP] [حساس]

رساؤ موسم_اسکور
# ✓ موسم_اسکور: کوئی حساس رساؤ نہیں, صاف ہے
```

---

## Why this exists

Conventional languages treat lineage, GDPR delete cascades, and ML feature provenance as library concerns. They are brittle, opt-in, easy to forget.

- GDPR / CPRA right-to-delete. Teams spend weeks hunting derived data after a deletion request.
- ML feature governance. "Did sensitive data influence this prediction?" is rarely answerable.
- AI agent auditability. As agents call agents, output provenance disappears.
- Healthcare and finance audits. Lineage is reconstructed after the fact by expensive consultants.

In Rishta these are runtime-intrinsic. The answer to every question is already in the graph.

---

## Roadmap

- v0.3, typed rishta edges (استاد, سوتن, گواہ, جوڑ). Done.
- v0.4, serialized شجرہ (سنبھال, اٹھا). Done.
- v0.5, modules (منگوا). Done.
- v0.7, more typed edges (دشمن, لے_پالک, رضاعی, سمدھی query, دشمن_رساؤ query). Done.
- v0.8, stdlib (فائل, وقت, حساب, جال). 19 builtins. Done.
- v0.9, گواہی (cryptographic testimony, Merkle chain over the شجرہ). Done.
- v0.6 (deferred), REPL for `rishta.py`, polish (literal-print, source-context errors).
- v1.0, bytecode VM.
- v2.0, Rust runtime + LLVM backend.

---

## Paper

A research paper formalizing the رشتہ semantics, kinship-typed lineage edges, and گواہی cryptographic protocol lives in [`paper/`](paper/). Built artifact: [`paper/rishta.pdf`](paper/rishta.pdf).

## Contributing

Early-stage. Breaking changes between every minor version until v1.0. Issues and PRs welcome, especially vocabulary suggestions rooted in Karachi Urdu idioms.

## License

TBD.
