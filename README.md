# بھائی-lang

**A Karachi-native programming language with data lineage as a first-class primitive.**

Data privacy (GDPR / CPRA), ML feature provenance, and AI agent auditability are problems conventional languages punt to libraries. بھائی makes them intrinsic: every value carries its ancestry, consent revocation cascades automatically through every derived computation, and PII leaks are detectable with a single query.

The language is written in Urdu script because its semantics map to Karachi idioms about relationships (`رشتہ`), loss (`تپکا`, `شاپنگ`), and authenticity (`VIP`, `دو نمبری`).

---

## Status

Experimental (v0.2). Two interpreters live in this repo:

| File | Purpose |
|---|---|
| [`bhai.py`](bhai.py) | General-purpose tree-walking interpreter. Variables, functions, closures, control flow, lists, built-ins. |
| [`rishta.py`](rishta.py) | The رشتہ primitive runtime. Data lineage + consent + trust + PII-sensitivity as the execution model. |

`bhai.py` is a conventional language with Urdu keywords. The novelty lives in `rishta.py` — see [*The رشتہ primitive*](#the-رشتہ-primitive).

---

## Requirements

Python 3.8+. No dependencies.

## Install & run

```sh
git clone git@github.com:adiled/bhai-lang.git
cd bhai-lang

python3 bhai.py examples/factorial.bhai
python3 rishta.py examples/rishta_leak.bhai
python3 rishta.py examples/rishta_gdpr.bhai
```

---

## Hello, دنیا

```
# examples/hello.bhai  —  python3 bhai.py examples/hello.bhai
پھوٹ "ابے اوئے، سلام دنیا!"

سن شہر = "کراچی"
اگر شہر == "کراچی" {
    پھوٹ "بھائی، یہ تو اپنا شہر ہے"
}
```

---

## Language reference — `bhai.py`

### Keywords

| Keyword | Transliteration | Role | Karachi origin |
|---|---|---|---|
| `سن` | sun | variable declaration (let) | "listen up" |
| `کام` | kaam | function declaration | "work" |
| `کلٹی` | kalti | return | "flip back" (see glossary: escape/flee) |
| `اگر` / `ورنہ` | agar / warna | if / else | |
| `جبتک` | jabtak | while | "as long as" |
| `ہرایک` … `میں` | har-ek … mein | for-each … in | |
| `شاٹ` | shaaT | break | "short-circuit" (dimaagh shaat) |
| `کٹا` | kaTa | continue | "cut / skip past" |
| `پھوٹ` | phooT | print | "burst out / say it" |
| `پوچھ` | pooch | input() | "ask" |
| `جنین` / `کدو` / `نلا` | janeen / kaddu / nulla | true / false / null | genuine / pumpkin-dud / null |
| `اور` / `یا` / `نا` | aur / ya / naa | and / or / not | |

### Operators

Arithmetic `+ - * / %`, comparison `== != < > <= >=`, logical `&& || !`, assignment `=`, grouping `( ) { } [ ]`. Urdu punctuation: `،` as comma, `۔` as semicolon.

Numeric literals accept Urdu digits: `۵۰` = 50. Strings use `"..."` with standard escapes.

### Built-ins

| Function | Purpose |
|---|---|
| `لمبائی(x)` | length of string / list |
| `قسم(x)` | type name |
| `نمبر(x)` / `لفظ(x)` | cast to number / string |
| `ڈال(list, x)` / `نکال(list)` | push / pop |
| `ترتیب(n)` / `ترتیب(a, b)` / `ترتیب(a, b, step)` | range |

### Example — recursion + loops

```
کام فیکٹوریل(ن) {
    اگر ن <= 1 { کلٹی 1 }
    کلٹی ن * فیکٹوریل(ن - 1)
}

ہرایک ای میں ترتیب(1, 6) {
    پھوٹ ای, "! =", فیکٹوریل(ای)
}
```

### Example — closures

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

## The رشتہ primitive — `rishta.py`

The novel contribution. **Every value is a `کردار` (entity)** carrying its lineage. Operations automatically attach parentage edges; consent revocation cascades through them.

### The value model

Each کردار carries:

| Property | Values | Semantics |
|---|---|---|
| `value` | any | the underlying data |
| `parents` / `children` | `{rel → کردار}` | automatic lineage graph |
| `consent` | `VIP` · `دو نمبری` · `شاپنگ` | clean · tainted-via-ancestry · revoked |
| `trust` | `جانی` · `بھائی` · — | intimate · trusted · default |
| `sensitivity` | `حساس` · — | PII / sensitive · default |

**Propagation rules** (enforced at every operation):

- **Consent** — if any ancestor is revoked (`شاپنگ`), the descendant becomes `دو نمبری` (tainted) and its value is hidden on read.
- **Trust** — derived values inherit the **maximum** trust of their parents (`جانی` > `بھائی` > none).
- **Sensitivity** — derived values inherit `حساس` if **any** parent is `حساس`.

### Declaration

```
کردار <name> = <expr> [جانی|بھائی] [حساس]
```

Examples:
```
کردار عمر = 25
کردار ای_میل = "ali@karachi.pk" جانی
کردار سی_این_آئی_سی = 4210112345678 حساس جانی
```

### Automatic lineage

Every binary operation creates a new کردار whose parents are the operands. Left → `باپ`, right → `ماں`.

```
کردار ا = 10
کردار ب = 20
کردار ج = ا + ب     # ج.parents = {باپ: ا, ماں: ب}
شجرہ ج
```

### Primitives

| Statement | Effect |
|---|---|
| `تپکا <name>` | revoke consent; cascade — every descendant becomes `دو نمبری` |
| `شجرہ <name>` | print full lineage tree with consent/trust/sensitivity tags per node |
| `اولاد <name>` | list all descendants |
| `جد <name>` | list all ancestors |
| `رساؤ <name>` | **PII leak query** — every `حساس` ancestor of `<name>` |
| `رشتہ: <a> کا <rel> <b>` | explicitly assert a lineage edge |
| `رشتہ <a> سے <b>` | query the rishta path between two کردار |
| `پھوٹ <expr>` | print with consent / trust / sensitivity tags |

Relationship names accepted: `باپ`, `ماں`, `بیٹا`, `بیٹی`, `بہن`, `چچا`, `ماموں`, `دادا`, `نانا`, `والد`.

### Example — GDPR cascade

```
کردار صارف = "ali@karachi.pk" جانی
کردار پروفائل = صارف + " (کراچی)"
کردار رپورٹ = پروفائل + " — اپریل 2026"

تپکا صارف
# ⚠  صارف تپکا — 4 اولاد دو نمبری ہوئی

پھوٹ رپورٹ
# رپورٹ: (ہائیڈ) [دو نمبری] [جانی] — اجداد میں کوئی تپکا ہو چکا
```

### Example — PII leak detection

```
کردار سی_این_آئی_سی = 4210112345678 حساس
کردار عمر = 25
کردار ماڈل_فیچر = سی_این_آئی_سی + عمر       # auto-tagged حساس
کردار موسم_اسکور = عمر + 10                  # clean

رساؤ ماڈل_فیچر
# ⚠  ماڈل_فیچر میں حساس رساؤ — 2 حساس جد ملے:
#   ← خود: ماڈل_فیچر  = 4210112345703 [VIP] [حساس]
#   ← باپ: سی_این_آئی_سی = 4210112345678 [VIP] [حساس]

رساؤ موسم_اسکور
# ✓ موسم_اسکور: کوئی حساس رساؤ نہیں — صاف ہے
```

---

## Why this exists

Conventional languages treat these problems as library concerns. They are brittle, opt-in, and easy to forget:

- **GDPR / CPRA right-to-delete** — teams spend weeks hunting derived data after a deletion request
- **ML feature governance** — "did sensitive data influence this prediction?" is rarely answerable
- **AI agent auditability** — as agents call agents, output provenance disappears
- **Healthcare / finance audits** — lineage is reconstructed after the fact by expensive consultants

In بھائی these are runtime-intrinsic: the answer to every question is already in the graph.

---

## Roadmap

- **v0.3** — `سیٹ` (freeze), `سافٹویئر اپڈیٹ` (versioned mutation), `ڈنڈی ماری` (tamper marks), `اوقات دکھا` (assertions)
- **v0.4** — serialized `شجرہ`: save/load lineage across runs — the compliance audit kit
- **v0.5** — compile-to-Python: embed the رشتہ runtime in existing Python codebases
- **v1.0** — bytecode VM
- **v2.0** — Rust runtime + LLVM backend

---

## Contributing

Early-stage; breaking changes between every minor version until v1.0. Issues and PRs welcome — especially vocabulary suggestions rooted in Karachi Urdu idioms.

## License

TBD.
