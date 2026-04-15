#!/usr/bin/env python3
# بھائی — رشتہ primitive, Karachi-native vocabulary
# states: VIP (clean) | دو نمبری (tainted via lineage) | شاپنگ (revoked)
# revoke verb: تپکا
# trust: جانی > بھائی > (default), propagates max along lineage

import sys
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
    __slots__ = ("id", "name", "value", "parents", "children", "consent", "trust", "sensitivity", "line")

    def __init__(self, value, name=None, line=None, trust=None, sensitivity=None):
        self.id = next(_counter)
        self.name = name or f"_انونیم_{self.id}"
        self.value = value
        self.parents: List[Tuple[str, "Kirdaar"]] = []
        self.children: List[Tuple[str, "Kirdaar"]] = []
        self.consent = "VIP"              # VIP | دو نمبری | شاپنگ
        self.trust = trust                # None | بھائی | جانی
        self.sensitivity = sensitivity    # None | حساس
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
    "اولاد":   "Q_AULAD",
    "جد":     "Q_JAD",
    "شجرہ":   "Q_SHAJARA",
    "رساؤ":    "Q_LEAK",
    "تپکا":   "REVOKE",
    "حساس":   "SENSITIVITY",
    "بول":    "PRINT",
    "سچ":     "TRUE",
    "جھوٹ":   "FALSE",
    "خالی":   "NULL",
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
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "reset":   "\033[0m",
}

def paint(s, key):
    if not sys.stdout.isatty(): return s
    return f"{ANSI.get(key, '')}{s}{ANSI['reset']}"


def _show(v):
    if v is None: return "خالی"
    if v is True: return "سچ"
    if v is False: return "جھوٹ"
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
    return " ".join(parts)


class Interpreter:
    def __init__(self):
        self.globals: dict = {}

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
    try:
        toks = Lexer(src).tokenize()
        prog = Parser(toks).parse()
        Interpreter().run(prog)
    except BhaiError as e:
        print(f"بکواس! {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("استعمال: rishta.py <file.bhai>", file=sys.stderr)
        sys.exit(2)
    run_file(sys.argv[1])
