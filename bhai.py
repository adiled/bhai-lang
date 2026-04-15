#!/usr/bin/env python3
# بھائی — کراچی کی سب سے بدتمیز پروگرامنگ زبان
# v0.1 — tree-walking interpreter. Next: bytecode VM, then Rust port.

import sys
from dataclasses import dataclass
from typing import Any


# ═══════════════════════════ ERRORS ═══════════════════════════

class BhaiError(Exception):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line
        super().__init__(self._format())
    def _format(self):
        return f"[لائن {self.line}] {self.msg}" if self.line else self.msg


# ═══════════════════════════ LEXER ═══════════════════════════

KEYWORDS = {
    "سن":     "VAR",       # listen up — variable declaration
    "بول":    "PRINT",     # speak
    "اگر":    "IF",
    "ورنہ":   "ELSE",
    "جبتک":   "WHILE",
    "ہرایک":  "FOREACH",
    "میں":    "IN",
    "کام":    "FUNC",      # work/job — function
    "واپس":   "RETURN",
    "سچ":     "TRUE",
    "جھوٹ":   "FALSE",
    "خالی":   "NULL",
    "اور":    "AND",
    "یا":     "OR",
    "نہیں":   "NOT",
    "توڑ":    "BREAK",
    "اگلا":   "CONTINUE",
    "پوچھ":   "INPUT",
}

URDU_DIGITS = {c: str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}

TWO_CHAR = {"==": "EQ", "!=": "NEQ", "<=": "LE", ">=": "GE", "&&": "AND", "||": "OR"}
ONE_CHAR = {
    "(": "LPAREN", ")": "RPAREN", "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACK", "]": "RBRACK", ",": "COMMA", "،": "COMMA",
    ";": "SEMI", "۔": "SEMI",
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
    "=": "ASSIGN", "<": "LT", ">": "GT", "!": "BANG", ":": "COLON",
}


@dataclass
class Token:
    kind: str
    value: Any
    line: int


class Lexer:
    def __init__(self, src):
        self.src = src
        self.i = 0
        self.line = 1
        self.tokens = []

    def _peek(self, k=0):
        j = self.i + k
        return self.src[j] if j < len(self.src) else ""

    def _advance(self):
        c = self.src[self.i]
        self.i += 1
        if c == "\n":
            self.line += 1
        return c

    def tokenize(self):
        while self.i < len(self.src):
            c = self._peek()
            if c in " \t\r\n":
                self._advance()
            elif c == "#":
                while self.i < len(self.src) and self._peek() != "\n":
                    self._advance()
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
        line = self.line
        self._advance()  # opening "
        buf = []
        escapes = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "0": "\0"}
        while self.i < len(self.src) and self._peek() != '"':
            c = self._advance()
            if c == "\\":
                if self.i >= len(self.src):
                    raise BhaiError("اسٹرنگ میں adhoora escape", line)
                nxt = self._advance()
                buf.append(escapes.get(nxt, nxt))
            else:
                buf.append(c)
        if self.i >= len(self.src):
            raise BhaiError("ابے اسٹرنگ بند کرنا بھول گیا", line)
        self._advance()  # closing "
        self.tokens.append(Token("STRING", "".join(buf), line))

    def _number(self):
        line = self.line
        buf = []
        while self.i < len(self.src):
            c = self._peek()
            if c.isdigit():
                buf.append(self._advance())
            elif c in URDU_DIGITS:
                buf.append(URDU_DIGITS[self._advance()])
            else:
                break
        is_float = False
        if self._peek() == "." and (self._peek(1).isdigit() or self._peek(1) in URDU_DIGITS):
            is_float = True
            buf.append(self._advance())
            while self.i < len(self.src):
                c = self._peek()
                if c.isdigit():
                    buf.append(self._advance())
                elif c in URDU_DIGITS:
                    buf.append(URDU_DIGITS[self._advance()])
                else:
                    break
        val = float("".join(buf)) if is_float else int("".join(buf))
        self.tokens.append(Token("NUMBER", val, line))

    def _ident(self):
        line = self.line
        buf = []
        while self.i < len(self.src):
            c = self._peek()
            if c == "_" or c.isalnum() or c in URDU_DIGITS:
                buf.append(self._advance())
            else:
                break
        name = "".join(buf)
        kind = KEYWORDS.get(name, "IDENT")
        self.tokens.append(Token(kind, name, line))

    def _symbol(self):
        line = self.line
        c = self._advance()
        two = c + self._peek()
        if two in TWO_CHAR:
            self._advance()
            self.tokens.append(Token(TWO_CHAR[two], two, line))
        elif c in ONE_CHAR:
            self.tokens.append(Token(ONE_CHAR[c], c, line))
        else:
            raise BhaiError(f"یہ '{c}' کیا بلا ہے یہاں؟", line)


# ═══════════════════════════ AST ═══════════════════════════

@dataclass
class Program: stmts: list
@dataclass
class VarDecl: name: str; expr: Any; line: int
@dataclass
class Assign: target: Any; expr: Any; line: int
@dataclass
class PrintStmt: exprs: list; line: int
@dataclass
class IfStmt: cond: Any; then: Any; else_: Any; line: int
@dataclass
class WhileStmt: cond: Any; body: Any; line: int
@dataclass
class ForEach: var: str; iterable: Any; body: Any; line: int
@dataclass
class FuncDecl: name: str; params: list; body: Any; line: int
@dataclass
class ReturnStmt: expr: Any; line: int
@dataclass
class BreakStmt: line: int
@dataclass
class ContinueStmt: line: int
@dataclass
class Block: stmts: list
@dataclass
class ExprStmt: expr: Any
@dataclass
class Binary: op: str; left: Any; right: Any; line: int
@dataclass
class Unary: op: str; operand: Any; line: int
@dataclass
class Literal: value: Any; line: int
@dataclass
class Variable: name: str; line: int
@dataclass
class Call: callee: Any; args: list; line: int
@dataclass
class Index: obj: Any; idx: Any; line: int
@dataclass
class ListLit: items: list; line: int
@dataclass
class InputExpr: prompt: Any; line: int


# ═══════════════════════════ PARSER ═══════════════════════════

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def _peek(self, k=0): return self.tokens[self.i + k]
    def _check(self, kind): return self._peek().kind == kind

    def _advance(self):
        t = self.tokens[self.i]
        self.i += 1
        return t

    def _match(self, *kinds):
        if self._peek().kind in kinds:
            return self._advance()
        return None

    def _expect(self, kind, msg):
        if self._peek().kind == kind:
            return self._advance()
        raise BhaiError(msg, self._peek().line)

    def parse(self):
        stmts = []
        while not self._check("EOF"):
            stmts.append(self._statement())
        return Program(stmts)

    def _statement(self):
        t = self._peek()
        if t.kind == "VAR":      return self._var_decl()
        if t.kind == "PRINT":    return self._print_stmt()
        if t.kind == "IF":       return self._if_stmt()
        if t.kind == "WHILE":    return self._while_stmt()
        if t.kind == "FOREACH":  return self._foreach_stmt()
        if t.kind == "FUNC":     return self._func_decl()
        if t.kind == "RETURN":   return self._return_stmt()
        if t.kind == "BREAK":
            self._advance(); self._match("SEMI")
            return BreakStmt(t.line)
        if t.kind == "CONTINUE":
            self._advance(); self._match("SEMI")
            return ContinueStmt(t.line)
        if t.kind == "LBRACE":
            return self._block()
        return self._expr_stmt()

    def _var_decl(self):
        t = self._advance()
        name = self._expect("IDENT", "ابے نام تو دے متغیر کا").value
        self._expect("ASSIGN", "= چاہیے بھائی")
        expr = self._expression()
        self._match("SEMI")
        return VarDecl(name, expr, t.line)

    def _print_stmt(self):
        t = self._advance()
        exprs = [self._expression()]
        while self._match("COMMA"):
            exprs.append(self._expression())
        self._match("SEMI")
        return PrintStmt(exprs, t.line)

    def _if_stmt(self):
        t = self._advance()
        cond = self._expression()
        then = self._block()
        else_ = None
        if self._match("ELSE"):
            else_ = self._if_stmt() if self._check("IF") else self._block()
        return IfStmt(cond, then, else_, t.line)

    def _while_stmt(self):
        t = self._advance()
        cond = self._expression()
        body = self._block()
        return WhileStmt(cond, body, t.line)

    def _foreach_stmt(self):
        t = self._advance()
        name = self._expect("IDENT", "ہرایک کے بعد نام دے").value
        self._expect("IN", "'میں' چاہیے")
        iterable = self._expression()
        body = self._block()
        return ForEach(name, iterable, body, t.line)

    def _func_decl(self):
        t = self._advance()
        name = self._expect("IDENT", "کام کا نام دے بھائی").value
        self._expect("LPAREN", "( چاہیے")
        params = []
        if not self._check("RPAREN"):
            params.append(self._expect("IDENT", "پیرامیٹر کا نام").value)
            while self._match("COMMA"):
                params.append(self._expect("IDENT", "پیرامیٹر کا نام").value)
        self._expect("RPAREN", ") چاہیے")
        body = self._block()
        return FuncDecl(name, params, body, t.line)

    def _return_stmt(self):
        t = self._advance()
        expr = None
        if not self._check("SEMI") and not self._check("RBRACE") and not self._check("EOF"):
            expr = self._expression()
        self._match("SEMI")
        return ReturnStmt(expr, t.line)

    def _block(self):
        self._expect("LBRACE", "{ چاہیے")
        stmts = []
        while not self._check("RBRACE") and not self._check("EOF"):
            stmts.append(self._statement())
        self._expect("RBRACE", "} چاہیے")
        return Block(stmts)

    def _expr_stmt(self):
        expr = self._expression()
        if self._match("ASSIGN"):
            value = self._expression()
            self._match("SEMI")
            if isinstance(expr, (Variable, Index)):
                return Assign(expr, value, getattr(expr, "line", 0))
            raise BhaiError("یہ کس کو assign کر رہا ہے؟", getattr(expr, "line", 0))
        self._match("SEMI")
        return ExprStmt(expr)

    # expression precedence (low → high): or, and, eq, cmp, term, factor, unary, call, primary
    def _expression(self):    return self._or_expr()

    def _or_expr(self):
        left = self._and_expr()
        while self._check("OR"):
            t = self._advance()
            left = Binary("||", left, self._and_expr(), t.line)
        return left

    def _and_expr(self):
        left = self._eq_expr()
        while self._check("AND"):
            t = self._advance()
            left = Binary("&&", left, self._eq_expr(), t.line)
        return left

    def _eq_expr(self):
        left = self._cmp_expr()
        while self._peek().kind in ("EQ", "NEQ"):
            t = self._advance()
            left = Binary(t.value, left, self._cmp_expr(), t.line)
        return left

    def _cmp_expr(self):
        left = self._term()
        while self._peek().kind in ("LT", "GT", "LE", "GE"):
            t = self._advance()
            left = Binary(t.value, left, self._term(), t.line)
        return left

    def _term(self):
        left = self._factor()
        while self._peek().kind in ("PLUS", "MINUS"):
            t = self._advance()
            left = Binary(t.value, left, self._factor(), t.line)
        return left

    def _factor(self):
        left = self._unary()
        while self._peek().kind in ("STAR", "SLASH", "PERCENT"):
            t = self._advance()
            left = Binary(t.value, left, self._unary(), t.line)
        return left

    def _unary(self):
        if self._peek().kind in ("BANG", "NOT", "MINUS"):
            t = self._advance()
            return Unary(t.value, self._unary(), t.line)
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._match("LPAREN"):
                args = []
                line = self._peek().line
                if not self._check("RPAREN"):
                    args.append(self._expression())
                    while self._match("COMMA"):
                        args.append(self._expression())
                self._expect("RPAREN", ") چاہیے")
                expr = Call(expr, args, line)
            elif self._match("LBRACK"):
                line = self._peek().line
                idx = self._expression()
                self._expect("RBRACK", "] چاہیے")
                expr = Index(expr, idx, line)
            else:
                break
        return expr

    def _primary(self):
        t = self._peek()
        if t.kind == "NUMBER":
            self._advance(); return Literal(t.value, t.line)
        if t.kind == "STRING":
            self._advance(); return Literal(t.value, t.line)
        if t.kind == "TRUE":
            self._advance(); return Literal(True, t.line)
        if t.kind == "FALSE":
            self._advance(); return Literal(False, t.line)
        if t.kind == "NULL":
            self._advance(); return Literal(None, t.line)
        if t.kind == "IDENT":
            self._advance(); return Variable(t.value, t.line)
        if t.kind == "LPAREN":
            self._advance()
            e = self._expression()
            self._expect("RPAREN", ") چاہیے")
            return e
        if t.kind == "LBRACK":
            self._advance()
            items = []
            if not self._check("RBRACK"):
                items.append(self._expression())
                while self._match("COMMA"):
                    items.append(self._expression())
            self._expect("RBRACK", "] چاہیے")
            return ListLit(items, t.line)
        if t.kind == "INPUT":
            self._advance()
            self._expect("LPAREN", "( چاہیے")
            prompt = None
            if not self._check("RPAREN"):
                prompt = self._expression()
            self._expect("RPAREN", ") چاہیے")
            return InputExpr(prompt, t.line)
        raise BhaiError(f"یہ '{t.value}' یہاں کیا کر رہا ہے؟", t.line)


# ═══════════════════════════ INTERPRETER ═══════════════════════════

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name, line=0):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise BhaiError(f"ابے '{name}' کیا چیز ہے؟ کبھی سنا نہیں اس کا", line)

    def set(self, name, value):
        self.vars[name] = value

    def assign(self, name, value, line=0):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value, line)
            return
        raise BhaiError(f"'{name}' declare ہی نہیں ہوا ابھی تک", line)


class BreakSignal(Exception): pass
class ContinueSignal(Exception): pass
class ReturnSignal(Exception):
    def __init__(self, value): self.value = value


class Function:
    def __init__(self, decl, closure):
        self.decl = decl
        self.closure = closure

    def call(self, interp, args, line):
        if len(args) != len(self.decl.params):
            raise BhaiError(
                f"'{self.decl.name}' کو {len(self.decl.params)} دلیلیں چاہیے، تو نے {len(args)} دیں",
                line,
            )
        env = Environment(self.closure)
        for p, a in zip(self.decl.params, args):
            env.set(p, a)
        try:
            for stmt in self.decl.body.stmts:
                interp._exec(stmt, env)
        except ReturnSignal as r:
            return r.value
        return None


@dataclass
class Builtin:
    name: str
    fn: Any


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self._install_builtins()

    def _install_builtins(self):
        g = self.globals
        g.set("لمبائی", Builtin("لمبائی", _b_len))
        g.set("قسم",    Builtin("قسم",    _b_type))
        g.set("نمبر",   Builtin("نمبر",   _b_num))
        g.set("لفظ",    Builtin("لفظ",    _b_str))
        g.set("شامل",   Builtin("شامل",   _b_push))   # append
        g.set("نکال",   Builtin("نکال",   _b_pop))    # pop
        g.set("ترتیب",  Builtin("ترتیب",  _b_range))  # range

    def run(self, program):
        for stmt in program.stmts:
            self._exec(stmt, self.globals)

    def _exec(self, node, env):
        m = getattr(self, f"_exec_{type(node).__name__}", None)
        if m is None:
            return self._eval(node, env)
        return m(node, env)

    def _exec_VarDecl(self, n, env):
        env.set(n.name, self._eval(n.expr, env))

    def _exec_Assign(self, n, env):
        value = self._eval(n.expr, env)
        tgt = n.target
        if isinstance(tgt, Variable):
            env.assign(tgt.name, value, n.line)
        elif isinstance(tgt, Index):
            obj = self._eval(tgt.obj, env)
            idx = self._eval(tgt.idx, env)
            try:
                obj[idx] = value
            except Exception as e:
                raise BhaiError(f"index پہ assign نہیں ہوا: {e}", n.line)

    def _exec_PrintStmt(self, n, env):
        parts = [_stringify(self._eval(e, env)) for e in n.exprs]
        print(" ".join(parts))

    def _exec_IfStmt(self, n, env):
        if _truthy(self._eval(n.cond, env)):
            self._exec(n.then, env)
        elif n.else_ is not None:
            self._exec(n.else_, env)

    def _exec_WhileStmt(self, n, env):
        while _truthy(self._eval(n.cond, env)):
            try:
                self._exec(n.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_ForEach(self, n, env):
        iterable = self._eval(n.iterable, env)
        if isinstance(iterable, str):
            items = list(iterable)
        elif isinstance(iterable, (list, tuple)):
            items = iterable
        elif isinstance(iterable, dict):
            items = list(iterable.keys())
        else:
            raise BhaiError("اس چیز پہ loop نہیں چلے گی بھائی", n.line)
        for v in items:
            loop_env = Environment(env)
            loop_env.set(n.var, v)
            try:
                for stmt in n.body.stmts:
                    self._exec(stmt, loop_env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_FuncDecl(self, n, env):
        env.set(n.name, Function(n, env))

    def _exec_ReturnStmt(self, n, env):
        v = self._eval(n.expr, env) if n.expr is not None else None
        raise ReturnSignal(v)

    def _exec_BreakStmt(self, n, env): raise BreakSignal()
    def _exec_ContinueStmt(self, n, env): raise ContinueSignal()

    def _exec_Block(self, n, env):
        block_env = Environment(env)
        for stmt in n.stmts:
            self._exec(stmt, block_env)

    def _exec_ExprStmt(self, n, env):
        self._eval(n.expr, env)

    def _eval(self, node, env):
        m = getattr(self, f"_eval_{type(node).__name__}", None)
        if m is None:
            raise BhaiError(f"internal: {type(node).__name__} kaise evaluate karun")
        return m(node, env)

    def _eval_Literal(self, n, env):  return n.value
    def _eval_Variable(self, n, env): return env.get(n.name, n.line)
    def _eval_ListLit(self, n, env):  return [self._eval(e, env) for e in n.items]

    def _eval_Binary(self, n, env):
        if n.op == "&&":
            l = self._eval(n.left, env)
            return l if not _truthy(l) else self._eval(n.right, env)
        if n.op == "||":
            l = self._eval(n.left, env)
            return l if _truthy(l) else self._eval(n.right, env)
        l = self._eval(n.left, env)
        r = self._eval(n.right, env)
        try:
            if n.op == "+":
                if isinstance(l, str) or isinstance(r, str):
                    return _stringify(l) + _stringify(r)
                if isinstance(l, list) and isinstance(r, list):
                    return l + r
                return l + r
            if n.op == "-": return l - r
            if n.op == "*":
                if isinstance(l, str) and isinstance(r, int): return l * r
                if isinstance(r, str) and isinstance(l, int): return r * l
                return l * r
            if n.op == "/":
                if r == 0: raise BhaiError("زیرو سے تقسیم؟ دماغ چل گیا کیا", n.line)
                return l / r
            if n.op == "%":
                if r == 0: raise BhaiError("زیرو سے modulo؟ سنجیدہ ہو بھائی", n.line)
                return l % r
            if n.op == "==": return l == r
            if n.op == "!=": return l != r
            if n.op == "<":  return l < r
            if n.op == ">":  return l > r
            if n.op == "<=": return l <= r
            if n.op == ">=": return l >= r
        except BhaiError:
            raise
        except TypeError:
            raise BhaiError(
                f"یہ کیا mix کر رہا ہے: {_type_name(l)} اور {_type_name(r)} پہ '{n.op}'",
                n.line,
            )
        raise BhaiError(f"unknown op {n.op}", n.line)

    def _eval_Unary(self, n, env):
        v = self._eval(n.operand, env)
        if n.op in ("!", "نہیں"): return not _truthy(v)
        if n.op == "-":
            try: return -v
            except TypeError:
                raise BhaiError(f"{_type_name(v)} کا negative؟", n.line)
        raise BhaiError(f"unknown unary {n.op}", n.line)

    def _eval_Call(self, n, env):
        callee = self._eval(n.callee, env)
        args = [self._eval(a, env) for a in n.args]
        if isinstance(callee, Function):
            return callee.call(self, args, n.line)
        if isinstance(callee, Builtin):
            return callee.fn(args, n.line)
        raise BhaiError("یہ call-able نہیں ہے بھائی", n.line)

    def _eval_Index(self, n, env):
        obj = self._eval(n.obj, env)
        idx = self._eval(n.idx, env)
        try:
            return obj[idx]
        except Exception as e:
            raise BhaiError(f"index نہیں ملا: {e}", n.line)

    def _eval_InputExpr(self, n, env):
        prompt = _stringify(self._eval(n.prompt, env)) if n.prompt else ""
        try:
            return input(prompt)
        except EOFError:
            return ""


# ═══════════════════════════ HELPERS ═══════════════════════════

def _truthy(v):
    if v is None: return False
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return v != 0
    if isinstance(v, str): return len(v) > 0
    if isinstance(v, (list, dict, tuple)): return len(v) > 0
    return True


def _stringify(v):
    if v is None: return "خالی"
    if v is True: return "سچ"
    if v is False: return "جھوٹ"
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    if isinstance(v, list): return "[" + ", ".join(_stringify(x) for x in v) + "]"
    return str(v)


def _type_name(v):
    if v is None: return "خالی"
    if isinstance(v, bool): return "بولین"
    if isinstance(v, int): return "نمبر"
    if isinstance(v, float): return "اعشاریہ"
    if isinstance(v, str): return "لفظ"
    if isinstance(v, list): return "فہرست"
    if isinstance(v, dict): return "نقشہ"
    if isinstance(v, (Function, Builtin)): return "کام"
    return "پتا_نہیں"


def _b_len(args, line):
    if len(args) != 1: raise BhaiError("لمبائی کو ایک argument چاہیے", line)
    v = args[0]
    if isinstance(v, (str, list, dict, tuple)): return len(v)
    raise BhaiError(f"{_type_name(v)} کی لمبائی نہیں نکلتی", line)


def _b_type(args, line):
    if len(args) != 1: raise BhaiError("قسم کو ایک argument چاہیے", line)
    return _type_name(args[0])


def _b_num(args, line):
    if len(args) != 1: raise BhaiError("نمبر کو ایک argument چاہیے", line)
    s = args[0]
    if isinstance(s, (int, float)): return s
    if isinstance(s, bool): return 1 if s else 0
    try:
        s = str(s)
        return int(s) if "." not in s else float(s)
    except Exception:
        raise BhaiError(f"'{args[0]}' کو نمبر نہیں بنا سکتا", line)


def _b_str(args, line):
    if len(args) != 1: raise BhaiError("لفظ کو ایک argument چاہیے", line)
    return _stringify(args[0])


def _b_push(args, line):
    if len(args) != 2 or not isinstance(args[0], list):
        raise BhaiError("شامل(فہرست, چیز) چاہیے", line)
    args[0].append(args[1])
    return args[0]


def _b_pop(args, line):
    if len(args) != 1 or not isinstance(args[0], list):
        raise BhaiError("نکال(فہرست) چاہیے", line)
    if not args[0]:
        raise BhaiError("خالی فہرست سے کیا نکالوں؟", line)
    return args[0].pop()


def _b_range(args, line):
    if len(args) == 1: return list(range(int(args[0])))
    if len(args) == 2: return list(range(int(args[0]), int(args[1])))
    if len(args) == 3: return list(range(int(args[0]), int(args[1]), int(args[2])))
    raise BhaiError("ترتیب(end) یا ترتیب(start, end) یا ترتیب(start, end, step)", line)


# ═══════════════════════════ ENTRY ═══════════════════════════

def run_source(src, interp=None):
    interp = interp or Interpreter()
    tokens = Lexer(src).tokenize()
    program = Parser(tokens).parse()
    interp.run(program)
    return interp


def run_file(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    try:
        run_source(src)
    except BhaiError as e:
        print(f"بکواس! {e}", file=sys.stderr)
        sys.exit(1)


def repl():
    print("بھائی REPL v0.1 — نکلنے کے لیے Ctrl+D")
    interp = Interpreter()
    while True:
        try:
            line = input("بھائی> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        try:
            run_source(line, interp)
        except BhaiError as e:
            print(f"بکواس! {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        repl()
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        print("استعمال: bhai [فائل.bhai]", file=sys.stderr)
        sys.exit(2)
