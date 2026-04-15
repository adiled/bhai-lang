#!/usr/bin/env python3
# بھائی — رشتہ primitive, Karachi-native vocabulary
# states: VIP (clean) | دو نمبری (tainted via lineage) | شاپنگ (revoked)
# revoke verb: تپکا
# trust: جانی > بھائی > (default), propagates max along lineage

import os
import sys
import json
import hashlib
import datetime
import itertools
from dataclasses import dataclass
from typing import Any, List, Tuple, Optional
from collections import deque


# ═══════════════════════ ERRORS ═══════════════════════

class BhaiError(Exception):
    def __init__(self, msg, line=None):
        self.msg = msg; self.line = line
        super().__init__(f"[لائن {line}] {msg}" if line else msg)


# ═══════════════════════ KIRDAAR ═══════════════════════

_counter = itertools.count(1)
TRUST_RANK = {None: 0, "بھائی": 1, "جانی": 2}


def max_trust(a, b):
    return a if TRUST_RANK[a] >= TRUST_RANK[b] else b


class Kirdaar:
    __slots__ = ("id", "name", "value", "parents", "children", "consent", "trust", "sensitivity", "dushman", "origin", "line")

    def __init__(self, value, name=None, line=None, trust=None, sensitivity=None):
        self.id = next(_counter)
        self.name = name or f"_انونیم_{self.id}"
        self.value = value
        self.parents: List[Tuple[str, "Kirdaar"]] = []
        self.children: List[Tuple[str, "Kirdaar"]] = []
        self.consent = "VIP"              # VIP | دو نمبری | شاپنگ
        self.trust = trust                # None | بھائی | جانی
        self.sensitivity = sensitivity    # None | حساس
        self.dushman = False              # adversarial flag
        self.origin = None                # None | لے_پالک | رضاعی
        self.line = line

    def link(self, rel, parent):
        self.parents.append((rel, parent))
        parent.children.append((rel, self))

    def tapka_cascade(self):
        self.consent = "شاپنگ"
        q = deque(c for _, c in self.children)
        seen = {self.id}
        count = 0
        while q:
            k = q.popleft()
            if k.id in seen: continue
            seen.add(k.id)
            if k.consent == "VIP":
                k.consent = "دو نمبری"
                count += 1
            q.extend(c for _, c in k.children)
        return count


# ═══════════════════════ LEXER ═══════════════════════

KEYWORDS = {
    "کردار":  "KIRDAAR",
    "رشتہ":   "RISHTA",
    "کا":     "KA",
    "سے":     "SE",
    "باپ":    "REL", "ماں":  "REL", "بیٹا": "REL", "بیٹی": "REL",
    "بھائی":  "TRUST_BHAI",
    "جانی":   "TRUST_JANI",
    "بہن":    "REL", "چچا": "REL", "ماموں": "REL",
    "دادا":   "REL", "نانا": "REL", "والد": "REL",
    "اولاد":      "Q_AULAD",
    "جد":         "Q_JAD",
    "شجرہ":       "Q_SHAJARA",
    "رساؤ":        "Q_LEAK",
    "استاد_چین":  "Q_USTAAD_CHAIN",
    "تپکا":       "REVOKE",
    "حساس":       "SENSITIVITY",
    "سوتن":       "SAUTAN",
    "استاد":      "USTAAD",
    "گواہ":       "GAWAH",
    "جوڑ":        "JORH",
    "بنا":        "BANA",
    "سنبھال":     "SAVE",
    "اٹھا":       "LOAD",
    "منگوا":      "IMPORT",
    "دشمن":       "DUSHMAN",
    "لے_پالک":    "LEPALAK",
    "رضاعی":      "RAZAI",
    "سمدھی":      "Q_SAMDHI",
    "دشمن_رساؤ":  "Q_DUSHMAN_LEAK",
    "ثبوت":       "Q_SUBOOT",
    "پھوٹ":   "PRINT",
    "جنین":   "TRUE",
    "کدو":    "FALSE",
    "نلا":    "NULL",
}

URDU_DIGITS = {c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}
TWO_CHAR = {"==": "EQ", "!=": "NEQ", "<=": "LE", ">=": "GE"}
ONE_CHAR = {
    "(": "LPAREN", ")": "RPAREN",
    ",": "COMMA", "،": "COMMA",
    ";": "SEMI", "۔": "SEMI",
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
    "=": "ASSIGN", "<": "LT", ">": "GT", ":": "COLON",
}


@dataclass
class Token:
    kind: str
    value: Any
    line: int


class Lexer:
    def __init__(self, src):
        self.src = src; self.i = 0; self.line = 1; self.tokens = []

    def _peek(self, k=0):
        j = self.i + k
        return self.src[j] if j < len(self.src) else ""

    def _adv(self):
        c = self.src[self.i]; self.i += 1
        if c == "\n": self.line += 1
        return c

    def tokenize(self):
        while self.i < len(self.src):
            c = self._peek()
            if c in " \t\r\n":
                self._adv()
            elif c == "#":
                while self.i < len(self.src) and self._peek() != "\n":
                    self._adv()
            elif c == '"':
                self._string()
            elif c.isdigit() or c in URDU_DIGITS:
                self._number()
            elif c == "_" or c.isalpha():
                self._ident()
            else:
                self._symbol()
        self.tokens.append(Token("EOF", None, self.line))
        return self.tokens

    def _string(self):
        ln = self.line; self._adv()
        buf = []
        esc = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"'}
        while self.i < len(self.src) and self._peek() != '"':
            ch = self._adv()
            if ch == "\\":
                if self.i >= len(self.src):
                    raise BhaiError("اسٹرنگ ادھوری", ln)
                buf.append(esc.get(self._adv(), ch))
            else:
                buf.append(ch)
        if self.i >= len(self.src):
            raise BhaiError("اسٹرنگ بند نہیں ہوئی", ln)
        self._adv()
        self.tokens.append(Token("STRING", "".join(buf), ln))

    def _number(self):
        ln = self.line; buf = []
        while self.i < len(self.src):
            ch = self._peek()
            if ch.isdigit(): buf.append(self._adv())
            elif ch in URDU_DIGITS: buf.append(URDU_DIGITS[self._adv()])
            else: break
        is_float = False
        if self._peek() == "." and (self._peek(1).isdigit() or self._peek(1) in URDU_DIGITS):
            is_float = True; buf.append(self._adv())
            while self.i < len(self.src):
                ch = self._peek()
                if ch.isdigit(): buf.append(self._adv())
                elif ch in URDU_DIGITS: buf.append(URDU_DIGITS[self._adv()])
                else: break
        v = float("".join(buf)) if is_float else int("".join(buf))
        self.tokens.append(Token("NUMBER", v, ln))

    def _ident(self):
        ln = self.line; buf = []
        while self.i < len(self.src):
            ch = self._peek()
            if ch == "_" or ch.isalnum() or ch in URDU_DIGITS:
                buf.append(self._adv())
            else:
                break
        name = "".join(buf)
        kind = KEYWORDS.get(name, "IDENT")
        self.tokens.append(Token(kind, name, ln))

    def _symbol(self):
        ln = self.line; ch = self._adv()
        two = ch + self._peek()
        if two in TWO_CHAR:
            self._adv()
            self.tokens.append(Token(TWO_CHAR[two], two, ln))
        elif ch in ONE_CHAR:
            self.tokens.append(Token(ONE_CHAR[ch], ch, ln))
        else:
            raise BhaiError(f"یہ '{ch}' کیا ہے یہاں؟", ln)


# ═══════════════════════ AST ═══════════════════════

@dataclass
class Program:        stmts: list
@dataclass
class KirdaarDecl:    name: str; expr: Any; trust: Optional[str]; sensitivity: Optional[str]; line: int
@dataclass
class RishtaAssert:   child: str; rel: str; parent: str; line: int
@dataclass
class QueryRishta:    a: str; b: str; line: int
@dataclass
class Revoke:         name: str; line: int
@dataclass
class QueryShajara:   name: str; line: int
@dataclass
class QueryAulad:     name: str; line: int
@dataclass
class QueryJad:       name: str; line: int
@dataclass
class QueryLeak:      name: str; line: int
@dataclass
class QueryUstaadChain: name: str; line: int
@dataclass
class SautanDecl:     child: str; parent: str; line: int
@dataclass
class UstaadDecl:     child: str; parent: str; line: int
@dataclass
class GawahDecl:      name: str; source: str; line: int
@dataclass
class JorhStmt:       a: str; b: str; result: str; line: int
@dataclass
class SaveStmt:       path: str; line: int
@dataclass
class LoadStmt:       path: str; line: int
@dataclass
class ImportStmt:     path: str; line: int
@dataclass
class DushmanMark:    name: str; line: int
@dataclass
class LepalakDecl:    name: str; expr: Any; line: int
@dataclass
class RazaiDecl:      name: str; source: str; line: int
@dataclass
class QuerySamdhi:    name: str; line: int
@dataclass
class QueryDushmanLeak: name: str; line: int
@dataclass
class QuerySaboot:    name: str; line: int
@dataclass
class PrintStmt:      expr: Any; line: int
@dataclass
class Binary:         op: str; left: Any; right: Any; line: int
@dataclass
class Literal:        value: Any; line: int
@dataclass
class VarRef:         name: str; line: int


# ═══════════════════════ PARSER ═══════════════════════

class Parser:
    def __init__(self, tokens):
        self.t = tokens; self.i = 0

    def _peek(self, k=0):  return self.t[self.i + k]
    def _check(self, k):   return self._peek().kind == k
    def _adv(self):        tok = self.t[self.i]; self.i += 1; return tok
    def _match(self, *k):
        if self._peek().kind in k: return self._adv()
        return None
    def _expect(self, k, msg):
        if self._peek().kind == k: return self._adv()
        raise BhaiError(msg, self._peek().line)

    def parse(self):
        stmts = []
        while not self._check("EOF"):
            stmts.append(self._stmt())
        return Program(stmts)

    def _stmt(self):
        t = self._peek()
        if t.kind == "KIRDAAR":    return self._kirdaar_decl()
        if t.kind == "RISHTA":     return self._rishta_stmt()
        if t.kind == "REVOKE":     return self._revoke()
        if t.kind == "Q_SHAJARA":  return self._simple_q(QueryShajara, "کس کا شجرہ؟")
        if t.kind == "Q_AULAD":    return self._simple_q(QueryAulad,   "کس کی اولاد؟")
        if t.kind == "Q_JAD":      return self._simple_q(QueryJad,     "کس کے جد؟")
        if t.kind == "Q_LEAK":     return self._simple_q(QueryLeak,    "کس کا رساؤ؟")
        if t.kind == "Q_USTAAD_CHAIN": return self._simple_q(QueryUstaadChain, "کس کی استاد چین؟")
        if t.kind == "SAUTAN":     return self._typed_decl(SautanDecl)
        if t.kind == "USTAAD":     return self._typed_decl(UstaadDecl)
        if t.kind == "GAWAH":      return self._gawah()
        if t.kind == "JORH":       return self._jorh()
        if t.kind == "SAVE":       return self._save_load(SaveStmt)
        if t.kind == "LOAD":       return self._save_load(LoadStmt)
        if t.kind == "IMPORT":     return self._save_load(ImportStmt)
        if t.kind == "DUSHMAN":    return self._simple_q(DushmanMark, "کسے دشمن مارنا ہے؟")
        if t.kind == "Q_DUSHMAN_LEAK": return self._simple_q(QueryDushmanLeak, "کس کا دشمن رساؤ؟")
        if t.kind == "Q_SAMDHI":   return self._simple_q(QuerySamdhi, "کس کے سمدھی؟")
        if t.kind == "Q_SUBOOT":   return self._simple_q(QuerySaboot, "کس کا ثبوت؟")
        if t.kind == "LEPALAK":    return self._lepalak()
        if t.kind == "RAZAI":      return self._typed_decl(RazaiDecl)
        if t.kind == "PRINT":      return self._print()
        raise BhaiError(f"یہ '{t.value}' یہاں کیا کر رہا ہے؟", t.line)

    def _kirdaar_decl(self):
        t = self._adv()
        name = self._expect("IDENT", "کردار کا نام دے").value
        self._expect("ASSIGN", "= چاہیے")
        expr = self._expr()
        trust = None
        sensitivity = None
        while self._peek().kind in ("TRUST_JANI", "TRUST_BHAI", "SENSITIVITY"):
            tok = self._adv()
            if tok.kind == "SENSITIVITY":
                sensitivity = tok.value
            else:
                trust = tok.value
        self._match("SEMI")
        return KirdaarDecl(name, expr, trust, sensitivity, t.line)

    def _rishta_stmt(self):
        t = self._adv()
        if self._match("COLON"):
            child = self._expect("IDENT", "کردار کا نام").value
            self._expect("KA", "'کا' چاہیے")
            rel = self._expect("REL", "رشتہ کی قسم — باپ/ماں/بیٹا وغیرہ").value
            parent = self._expect("IDENT", "کردار کا نام").value
            self._match("SEMI")
            return RishtaAssert(child, rel, parent, t.line)
        a = self._expect("IDENT", "پہلا کردار؟").value
        self._expect("SE", "'سے' چاہیے")
        b = self._expect("IDENT", "دوسرا کردار؟").value
        self._match("SEMI")
        return QueryRishta(a, b, t.line)

    def _revoke(self):
        t = self._adv()
        name = self._expect("IDENT", "کسے تپکانا ہے؟").value
        self._match("SEMI")
        return Revoke(name, t.line)

    def _simple_q(self, cls, msg):
        t = self._adv()
        name = self._expect("IDENT", msg).value
        self._match("SEMI")
        return cls(name, t.line)

    def _typed_decl(self, cls):
        # syntax: <kwd> <child> = <parent>
        t = self._adv()
        child = self._expect("IDENT", "کردار کا نام").value
        self._expect("ASSIGN", "= چاہیے")
        parent = self._expect("IDENT", "کردار کا نام").value
        self._match("SEMI")
        return cls(child, parent, t.line)

    def _lepalak(self):
        # syntax: لے_پالک <name> = <expr>   (declares an externally-sourced kirdaar)
        t = self._adv()
        name = self._expect("IDENT", "کردار کا نام").value
        self._expect("ASSIGN", "= چاہیے")
        expr = self._expr()
        self._match("SEMI")
        return LepalakDecl(name, expr, t.line)

    def _gawah(self):
        # syntax: گواہ <name> = <source>
        t = self._adv()
        name = self._expect("IDENT", "گواہ کا نام").value
        self._expect("ASSIGN", "= چاہیے")
        source = self._expect("IDENT", "کس پہ گواہی؟").value
        self._match("SEMI")
        return GawahDecl(name, source, t.line)

    def _save_load(self, cls):
        t = self._adv()
        path = self._expect("STRING", "فائل کا نام چاہیے").value
        self._match("SEMI")
        return cls(path, t.line)

    def _jorh(self):
        # syntax: جوڑ <a> سے <b> بنا <result>
        t = self._adv()
        a = self._expect("IDENT", "پہلا کردار").value
        self._expect("SE", "'سے' چاہیے")
        b = self._expect("IDENT", "دوسرا کردار").value
        self._expect("BANA", "'بنا' چاہیے")
        result = self._expect("IDENT", "نتیجہ کا نام").value
        self._match("SEMI")
        return JorhStmt(a, b, result, t.line)

    def _print(self):
        t = self._adv()
        expr = self._expr()
        self._match("SEMI")
        return PrintStmt(expr, t.line)

    def _expr(self):   return self._term()

    def _term(self):
        left = self._factor()
        while self._peek().kind in ("PLUS", "MINUS"):
            op = self._adv()
            left = Binary(op.value, left, self._factor(), op.line)
        return left

    def _factor(self):
        left = self._primary()
        while self._peek().kind in ("STAR", "SLASH", "PERCENT"):
            op = self._adv()
            left = Binary(op.value, left, self._primary(), op.line)
        return left

    def _primary(self):
        t = self._peek()
        if t.kind == "NUMBER": self._adv(); return Literal(t.value, t.line)
        if t.kind == "STRING": self._adv(); return Literal(t.value, t.line)
        if t.kind == "TRUE":   self._adv(); return Literal(True, t.line)
        if t.kind == "FALSE":  self._adv(); return Literal(False, t.line)
        if t.kind == "NULL":   self._adv(); return Literal(None, t.line)
        if t.kind == "IDENT":  self._adv(); return VarRef(t.value, t.line)
        if t.kind == "LPAREN":
            self._adv(); e = self._expr()
            self._expect("RPAREN", ") چاہیے")
            return e
        raise BhaiError(f"'{t.value}' یہاں کیا کر رہا ہے؟", t.line)


# ═══════════════════════ INTERPRETER ═══════════════════════

ANSI = {
    "VIP":      "\033[32m",
    "شاپنگ":   "\033[31m\033[1m",
    "دو نمبری": "\033[33m",
    "جانی":    "\033[36m\033[1m",
    "بھائی":   "\033[36m",
    "حساس":    "\033[35m\033[1m",
    "دشمن":    "\033[31m\033[1m",
    "لے_پالک": "\033[34m",
    "رضاعی":   "\033[34m\033[2m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "reset":   "\033[0m",
}

def paint(s, key):
    if not sys.stdout.isatty(): return s
    return f"{ANSI.get(key, '')}{s}{ANSI['reset']}"


def _hash_kirdaar(k, cache):
    """Deterministic SHA-256 over (value + tags + sorted parent rishta-edges).
    Excludes the kirdaar's name — same content + lineage = same hash."""
    if k.id in cache:
        return cache[k.id]
    parent_proofs = sorted(
        (rel, _hash_kirdaar(p, cache)) for rel, p in k.parents
    )
    canonical = json.dumps(
        {
            "v": k.value,
            "c": k.consent,
            "t": k.trust,
            "s": k.sensitivity,
            "d": k.dushman,
            "o": k.origin,
            "p": parent_proofs,
        },
        sort_keys=True, ensure_ascii=False, default=str,
    )
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cache[k.id] = h
    return h


def _show(v):
    if v is None: return "نلا"
    if v is True: return "جنین"
    if v is False: return "کدو"
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    return str(v)


def _show_safe(k):
    if k.consent == "VIP": return _show(k.value)
    return paint("???", k.consent)


def _tags(k):
    parts = [paint(f"[{k.consent}]", k.consent)]
    if k.trust:
        parts.append(paint(f"[{k.trust}]", k.trust))
    if k.sensitivity:
        parts.append(paint(f"[{k.sensitivity}]", k.sensitivity))
    if k.dushman:
        parts.append(paint("[دشمن]", "دشمن"))
    if k.origin:
        parts.append(paint(f"[{k.origin}]", k.origin))
    return " ".join(parts)


class Interpreter:
    def __init__(self):
        self.globals: dict = {}
        self.imported: set = set()
        self.current_dir: str = os.getcwd()

    def run(self, prog):
        for s in prog.stmts:
            self._exec(s)

    def _exec(self, n):
        getattr(self, f"_x_{type(n).__name__}")(n)

    def _lookup(self, name, line):
        if name not in self.globals:
            raise BhaiError(f"ابے '{name}' کون ہے؟ کبھی declare ہی نہیں کیا", line)
        return self.globals[name]

    def _x_KirdaarDecl(self, n):
        k = self._eval(n.expr)
        k.name = n.name
        if n.trust is not None:
            k.trust = n.trust
        if n.sensitivity is not None:
            k.sensitivity = n.sensitivity
        self.globals[n.name] = k

    def _x_RishtaAssert(self, n):
        child = self._lookup(n.child, n.line)
        parent = self._lookup(n.parent, n.line)
        child.link(n.rel, parent)
        print(paint(f"✓ {n.child} کا {n.rel} = {n.parent}", "bold"))

    def _x_QueryRishta(self, n):
        a = self._lookup(n.a, n.line)
        b = self._lookup(n.b, n.line)
        path = self._find_path(a, b)
        if path is None:
            print(f"{n.a} اور {n.b} اجنبی ہیں — کوئی رشتہ نہیں")
            return
        chain = f"{n.a}"
        for rel, node in path:
            chain += f" → ({rel}) {node.name}"
        print(chain)

    def _x_Revoke(self, n):
        k = self._lookup(n.name, n.line)
        count = k.tapka_cascade()
        print(paint(f"⚠  {n.name} تپکا — {count} اولاد دو نمبری ہوئی", "شاپنگ"))

    def _x_QueryShajara(self, n):
        k = self._lookup(n.name, n.line)
        print(paint(f"شجرہ {n.name}:", "bold"))
        print(self._render_shajara(k))

    def _x_QueryAulad(self, n):
        k = self._lookup(n.name, n.line)
        ds = list(self._descendants(k))
        if not ds:
            print(f"{n.name} کی اولاد نہیں"); return
        print(paint(f"{n.name} کی اولاد:", "bold"))
        for rel, ch in ds:
            print(f"  → {rel}: {ch.name} = {_show_safe(ch)} {_tags(ch)}")

    def _x_QueryJad(self, n):
        k = self._lookup(n.name, n.line)
        ancs = list(self._ancestors(k))
        if not ancs:
            print(f"{n.name} یتیم ہے — کوئی جد نہیں"); return
        print(paint(f"{n.name} کے جد:", "bold"))
        for rel, a in ancs:
            print(f"  ← {rel}: {a.name} = {_show_safe(a)} {_tags(a)}")

    def _x_SautanDecl(self, n):
        child = self._lookup(n.child, n.line)
        parent = self._lookup(n.parent, n.line)
        child.link("سوتن", parent)
        # سوتن inherits sensitivity to child (alternative source could carry PII too)
        if parent.sensitivity:
            child.sensitivity = "حساس"
        print(paint(f"✓ {n.child} کی سوتن: {n.parent}", "bold"))

    def _x_UstaadDecl(self, n):
        # Y is استاد of X (Y trained X). X is implicitly شاگرد.
        shagird = self._lookup(n.child, n.line)
        ustaad = self._lookup(n.parent, n.line)
        shagird.link("استاد", ustaad)
        # training data sensitivity flows to the model
        if ustaad.sensitivity:
            shagird.sensitivity = "حساس"
        print(paint(f"✓ {n.parent} → استاد of {n.child}", "bold"))

    def _x_GawahDecl(self, n):
        src = self._lookup(n.source, n.line)
        # snapshot src's value at this moment; obs is a new kirdaar
        obs = Kirdaar(src.value, name=n.name, line=n.line)
        obs.link("گواہ", src)
        # witness inherits trust + sensitivity (it sees the same data)
        obs.trust = src.trust
        obs.sensitivity = src.sensitivity
        self.globals[n.name] = obs
        print(paint(f"✓ گواہ {n.name} → {n.source} پہ snapshot لیا", "bold"))

    def _x_JorhStmt(self, n):
        a = self._lookup(n.a, n.line)
        b = self._lookup(n.b, n.line)
        # joined value carries both sources' values
        joined = Kirdaar([a.value, b.value], name=n.result, line=n.line)
        joined.link("بیوی", a)
        joined.link("شوہر", b)
        # propagate trust + sensitivity from both sources
        joined.trust = max_trust(a.trust, b.trust)
        if a.sensitivity or b.sensitivity:
            joined.sensitivity = "حساس"
        # consent: if either source is compromised, joined is tainted
        if a.consent != "VIP" or b.consent != "VIP":
            joined.consent = "دو نمبری"
        self.globals[n.result] = joined
        print(paint(f"✓ جوڑ: {n.a} ⨝ {n.b} → {n.result} (سمدھی between {n.a} ↔ {n.b})", "bold"))

    def _x_SaveStmt(self, n):
        # collect every kirdaar reachable from any global (parents + children both directions)
        reachable = {}
        def visit(k):
            if k.id in reachable: return
            reachable[k.id] = k
            for _, p in k.parents: visit(p)
            for _, c in k.children: visit(c)
        for k in self.globals.values():
            visit(k)
        # compute hashes for every reachable kirdaar (cached)
        hash_cache = {}
        for k in reachable.values():
            _hash_kirdaar(k, hash_cache)
        data = {
            "version": "0.9",
            "saved_at": datetime.datetime.now().isoformat(),
            "kirdaars": [
                {
                    "id": k.id,
                    "name": k.name,
                    "value": k.value,
                    "consent": k.consent,
                    "trust": k.trust,
                    "sensitivity": k.sensitivity,
                    "dushman": k.dushman,
                    "origin": k.origin,
                    "parents": [{"rel": rel, "id": p.id} for rel, p in k.parents],
                    "گواہی": hash_cache[k.id],
                }
                for k in reachable.values()
            ],
            "globals": {name: k.id for name, k in self.globals.items()},
        }
        with open(n.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(paint(
            f"✓ سنبھال لیا → {n.path} ({len(reachable)} کردار, {len(self.globals)} global)",
            "bold",
        ))

    def _x_ImportStmt(self, n):
        path = os.path.abspath(os.path.join(self.current_dir, n.path))
        if path in self.imported:
            return
        if not os.path.exists(path):
            raise BhaiError(f"فائل نہیں ملی: {n.path}", n.line)
        self.imported.add(path)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        old_dir = self.current_dir
        self.current_dir = os.path.dirname(path)
        try:
            toks = Lexer(src).tokenize()
            prog = Parser(toks).parse()
            for stmt in prog.stmts:
                self._exec(stmt)
        finally:
            self.current_dir = old_dir
        print(paint(f"✓ منگوا: {n.path}", "bold"))

    def _x_LoadStmt(self, n):
        global _counter
        with open(n.path, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") not in ("0.4", "0.7", "0.9"):
            print(paint(f"⚠  پرانا فارمیٹ — version {data.get('version')}", "شاپنگ"))
        # phase 1: build kirdaars without edges
        by_id = {}
        for kd in data["kirdaars"]:
            k = object.__new__(Kirdaar)
            k.id = kd["id"]
            k.name = kd["name"]
            k.value = kd["value"]
            k.consent = kd["consent"]
            k.trust = kd["trust"]
            k.sensitivity = kd["sensitivity"]
            k.dushman = kd.get("dushman", False)
            k.origin = kd.get("origin", None)
            k.parents = []
            k.children = []
            k.line = None
            by_id[k.id] = k
        # phase 2: link edges
        for kd in data["kirdaars"]:
            child = by_id[kd["id"]]
            for edge in kd["parents"]:
                parent = by_id[edge["id"]]
                child.parents.append((edge["rel"], parent))
                parent.children.append((edge["rel"], child))
        # phase 3: verify گواہی (cryptographic testimony) for every kirdaar
        verified = 0
        if data.get("version") == "0.9":
            cache = {}
            for kd in data["kirdaars"]:
                if "گواہی" not in kd:
                    continue
                k = by_id[kd["id"]]
                expected = _hash_kirdaar(k, cache)
                if expected != kd["گواہی"]:
                    raise BhaiError(
                        f"⚠  گواہی نا کام: '{kd['name']}' میں چھیڑ چھاڑ ہوئی! "
                        f"expected {expected[:12]}…, file says {kd['گواہی'][:12]}…",
                        None,
                    )
                verified += 1
        # phase 4: restore globals + advance counter
        self.globals = {name: by_id[kid] for name, kid in data["globals"].items()}
        if by_id:
            _counter = itertools.count(max(by_id.keys()) + 1)
        saved_at = data.get("saved_at", "?")
        proof_msg = f", {verified} گواہی verified ✓" if verified else ""
        print(paint(
            f"✓ اٹھا لیا ← {n.path} ({len(by_id)} کردار, {len(self.globals)} global{proof_msg}) — saved {saved_at}",
            "bold",
        ))

    def _x_DushmanMark(self, n):
        k = self._lookup(n.name, n.line)
        k.dushman = True
        seen = {k.id}
        q = deque(c for _, c in k.children)
        count = 0
        while q:
            ch = q.popleft()
            if ch.id in seen: continue
            seen.add(ch.id)
            if not ch.dushman:
                ch.dushman = True
                count += 1
            q.extend(c for _, c in ch.children)
        print(paint(f"⚠  {n.name} اب دشمن — {count} اولاد بھی دشمن", "دشمن"))

    def _x_LepalakDecl(self, n):
        k = self._eval(n.expr)
        k.name = n.name
        k.parents = []          # adopted has no biological parents
        k.origin = "لے_پالک"
        self.globals[n.name] = k
        print(paint(f"✓ لے_پالک: {n.name} = {_show_safe(k)} — باہر سے آیا", "bold"))

    def _x_RazaiDecl(self, n):
        # syntax: رضاعی <new> = <source>  → new is a cached/mirrored copy
        src = self._lookup(n.source, n.line)
        cached = Kirdaar(src.value, name=n.name, line=n.line)
        cached.link("رضاعی", src)
        cached.trust = src.trust
        cached.sensitivity = src.sensitivity
        cached.dushman = src.dushman
        cached.origin = "رضاعی"
        self.globals[n.name] = cached
        print(paint(f"✓ رضاعی: {n.name} ← {n.source} (مرر/کیش)", "bold"))

    def _x_QuerySamdhi(self, n):
        k = self._lookup(n.name, n.line)
        # سمدھی = co-parents through shared children (other parents of my children)
        seen = {k.id}
        results = []
        for _, ch in k.children:
            for orel, op in ch.parents:
                if op.id != k.id and op.id not in seen:
                    seen.add(op.id)
                    results.append((ch, op))
        if not results:
            print(f"{n.name} کا کوئی سمدھی نہیں — کبھی جوڑ نہیں ہوا")
            return
        print(paint(f"{n.name} کے سمدھی:", "bold"))
        for via, other in results:
            print(f"  ↔ {other.name} = {_show_safe(other)} {_tags(other)} (via {via.name})")

    def _x_QuerySaboot(self, n):
        k = self._lookup(n.name, n.line)
        h = _hash_kirdaar(k, {})
        print(paint(f"ثبوت {n.name}: {h[:16]}…  (full SHA-256: {h})", "bold"))

    def _x_QueryDushmanLeak(self, n):
        k = self._lookup(n.name, n.line)
        leaks = []
        if k.dushman:
            leaks.append(("خود", k))
        leaks.extend((rel, a) for rel, a in self._ancestors(k) if a.dushman)
        if not leaks:
            print(paint(f"✓ {n.name}: کوئی دشمن رساؤ نہیں — صاف", "VIP"))
            return
        print(paint(f"⚠  {n.name} میں دشمن رساؤ — {len(leaks)} adversarial جد:", "دشمن"))
        for rel, a in leaks:
            print(f"  ← {rel}: {a.name} = {_show_safe(a)} {_tags(a)}")

    def _x_QueryUstaadChain(self, n):
        k = self._lookup(n.name, n.line)
        # walk parents only via استاد edges
        chain = []
        seen = {k.id}
        stack = [(rel, p) for rel, p in k.parents if rel == "استاد"]
        while stack:
            rel, p = stack.pop()
            if p.id in seen: continue
            seen.add(p.id)
            chain.append((rel, p))
            stack.extend((r, pp) for r, pp in p.parents if r == "استاد")
        if not chain:
            print(f"{n.name}: کوئی استاد نہیں ملا")
            return
        print(paint(f"{n.name} کی استاد چین:", "bold"))
        for rel, a in chain:
            print(f"  ← {rel}: {a.name} = {_show_safe(a)} {_tags(a)}")

    def _x_QueryLeak(self, n):
        k = self._lookup(n.name, n.line)
        leaks = []
        if k.sensitivity:
            leaks.append(("خود", k))
        leaks.extend((rel, a) for rel, a in self._ancestors(k) if a.sensitivity)
        if not leaks:
            print(paint(f"✓ {n.name}: کوئی حساس رساؤ نہیں — صاف ہے", "VIP"))
            return
        print(paint(f"⚠  {n.name} میں حساس رساؤ — {len(leaks)} حساس جد ملے:", "حساس"))
        for rel, a in leaks:
            print(f"  ← {rel}: {a.name} = {_show_safe(a)} {_tags(a)}")

    def _x_PrintStmt(self, n):
        v = self._eval(n.expr)
        self._print_kirdaar(v)

    # ── expression eval ──
    def _eval(self, n):
        return getattr(self, f"_e_{type(n).__name__}")(n)

    def _e_Literal(self, n):
        return Kirdaar(n.value, line=n.line)

    def _e_VarRef(self, n):
        return self._lookup(n.name, n.line)

    def _e_Binary(self, n):
        l = self._eval(n.left)
        r = self._eval(n.right)
        if l.consent == "شاپنگ" or r.consent == "شاپنگ":
            bad = l.name if l.consent == "شاپنگ" else r.name
            raise BhaiError(f"'{bad}' تپکا ہو چکا — اس پہ compute نہیں ہوگا", n.line)
        try:
            if n.op == "+":
                if isinstance(l.value, str) or isinstance(r.value, str):
                    v = _show(l.value) + _show(r.value)
                else:
                    v = l.value + r.value
            elif n.op == "-": v = l.value - r.value
            elif n.op == "*": v = l.value * r.value
            elif n.op == "/":
                if r.value == 0: raise BhaiError("زیرو سے تقسیم — دماغ چل گیا", n.line)
                v = l.value / r.value
            elif n.op == "%": v = l.value % r.value
            else: raise BhaiError(f"op {n.op}?", n.line)
        except TypeError:
            raise BhaiError(
                f"ٹائپ mix نہیں ہوئے: {type(l.value).__name__} اور {type(r.value).__name__} پہ '{n.op}'",
                n.line,
            )
        child = Kirdaar(v, line=n.line)
        child.link("باپ", l)
        child.link("ماں", r)
        if l.consent != "VIP" or r.consent != "VIP":
            child.consent = "دو نمبری"
        # trust propagation: max of both sides
        child.trust = max_trust(l.trust, r.trust)
        # sensitivity propagation: any حساس ancestor → child حساس
        if l.sensitivity or r.sensitivity:
            child.sensitivity = "حساس"
        # dushman propagation: any adversarial ancestor → child adversarial
        if l.dushman or r.dushman:
            child.dushman = True
        return child

    # ── lineage queries ──
    def _descendants(self, k):
        seen = {k.id}
        q = deque(list(k.children))
        while q:
            rel, ch = q.popleft()
            if ch.id in seen: continue
            seen.add(ch.id)
            yield rel, ch
            q.extend(ch.children)

    def _ancestors(self, k):
        seen = {k.id}
        q = deque(list(k.parents))
        while q:
            rel, p = q.popleft()
            if p.id in seen: continue
            seen.add(p.id)
            yield rel, p
            q.extend(p.parents)

    def _find_path(self, a, b):
        q = deque([(a, [])])
        seen = {a.id}
        while q:
            node, path = q.popleft()
            if node.id == b.id: return path
            for rel, ch in node.children:
                if ch.id in seen: continue
                seen.add(ch.id)
                q.append((ch, path + [(rel, ch)]))
        q = deque([(a, [])])
        seen = {a.id}
        while q:
            node, path = q.popleft()
            if node.id == b.id: return path
            for rel, p in node.parents:
                if p.id in seen: continue
                seen.add(p.id)
                q.append((p, path + [(rel, p)]))
        return None

    # ── rendering ──
    def _print_kirdaar(self, k):
        if k.consent == "شاپنگ":
            print(f"{k.name}: {paint('(تپکا ہو چکا)', 'شاپنگ')} {_tags(k)}")
            return
        if k.consent == "دو نمبری":
            reason = "اجداد میں کوئی تپکا ہو چکا"
            print(f"{k.name}: {paint('(ہائیڈ)', 'دو نمبری')} {_tags(k)} — {reason}")
            return
        lineage = ", ".join(f"{rel}: {p.name}" for rel, p in k.parents) if k.parents else paint("یتیم", "dim")
        print(f"{k.name}: {_show(k.value)} {_tags(k)} — {lineage}")

    def _render_shajara(self, root):
        lines = []
        def walk(node, prefix, is_last, rel_label, first=False):
            connector = "" if first else ("└─ " if is_last else "├─ ")
            label = f"{rel_label}: " if rel_label else ""
            lines.append(f"{prefix}{connector}{label}{node.name} = {_show_safe(node)} {_tags(node)}")
            ext = "    " if is_last else "│   "
            child_prefix = prefix if first else prefix + ext
            for i, (rel, p) in enumerate(node.parents):
                walk(p, child_prefix, i == len(node.parents) - 1, rel)
        walk(root, "", True, None, first=True)
        return "\n".join(lines)


# ═══════════════════════ ENTRY ═══════════════════════

def run_file(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    interp = Interpreter()
    interp.current_dir = os.path.dirname(os.path.abspath(path))
    interp.imported.add(os.path.abspath(path))
    try:
        toks = Lexer(src).tokenize()
        prog = Parser(toks).parse()
        interp.run(prog)
    except BhaiError as e:
        print(f"بکواس! [{path}:{e.line or '?'}] {e.msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("استعمال: rishta.py <file.bhai>", file=sys.stderr)
        sys.exit(2)
    run_file(sys.argv[1])
