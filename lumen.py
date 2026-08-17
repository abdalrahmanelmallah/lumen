#!/usr/bin/env python3
"""
Lumen — a tiny programming language, implemented in a single Python file.

Usage:
    python3 lumen.py yourprogram.lu
    python3 lumen.py                 # starts an interactive REPL
    python3 lumen.py repl            # same as above

Language features:
    let x = 5
    run(x + 1)
    if x > 3 { run("big") } elif x > 0 { run("small positive") } else { run("small") }
    while x > 0 { run(x); x = x - 1 }
    for let i = 0; i < 5; i = i + 1 { run(i) }
    for item in [1, 2, 3] { run(item) }
    fn add(a, b) { return a + b }
    run(add(2, 3))
    let d = {"name": "Sam", "age": 30}       # dictionaries
    run(d["name"])
    class Point {
        fn init(self, x, y) { self.x = x; self.y = y }
        fn dist(self) { return sqrt(self.x * self.x + self.y * self.y) }
    }
    let p = new Point(3, 4)
    run(p.dist())
    try {
        risky()
    } catch err {
        run("caught: " + err)
    }
    run(f"x is {x} and x^2 is {x ** 2}")     # string interpolation
    import "mathlib"                          # loads libs/mathlib.lu
    import "sys"                              # loads a native (Python-backed) library
    import "mathlib" as m; run(m.square(4))   # namespaced import

See README.md for how to write your own libraries.
"""

import sys
import os
import re

# ----------------------------------------------------------------------
# 0. PACKAGE CONFIG — where `lumen get <lib>` downloads libraries from.
# ----------------------------------------------------------------------
GITHUB_REPO = "abdalrahmanelmallah/lumen"
GITHUB_BRANCH = "main"


def library_url(name):
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/lumen/libs/{name}.lu"


def get_base_dir():
    """Directory to look for a bundled libs/ folder in. Works whether
    lumen.py is run directly with Python, or bundled into a standalone
    executable (e.g. via PyInstaller), where __file__ doesn't point at a
    useful location on disk."""
    if getattr(sys, "frozen", False):
        # PyInstaller: onefile builds unpack bundled data to sys._MEIPASS;
        # onedir builds sit next to sys.executable.
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------
# 1. LEXER — turns source text into a flat list of tokens
# ----------------------------------------------------------------------

KEYWORDS = {
    "let", "if", "elif", "else", "while", "for", "in", "fn", "return",
    "true", "false", "import", "as", "break", "continue", "try", "catch",
    "class", "new",
}

TOKEN_SPEC = [
    ("NUMBER",       r"\d+(\.\d+)?"),
    ("BLOCKCOMMENT", r"(?s:/\*.*?\*/)"),
    ("FSTRING",      r'f"([^"\\]|\\.)*"'),
    ("STRING",       r'"([^"\\]|\\.)*"'),
    ("ID",           r"[A-Za-z_][A-Za-z0-9_]*"),
    # longest/most-specific operators first so e.g. ** beats *, && beats &
    ("OP",           r"\*\*|==|!=|<=|>=|&&|\|\||<<|>>|[+\-*/%=<>(){}\[\],;!&|^:.]"),
    ("NEWLINE",      r"\n"),
    ("SKIP",         r"[ \t]+"),
    ("COMMENT",      r"#[^\n]*"),
]

MASTER_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


_STRING_ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'",
    "0": "\0", "b": "\b", "f": "\f",
}


def unescape_string(s):
    """Resolves backslash escapes (\\n, \\t, \\", \\\\, ...) in a string
    literal's raw text. Any other character — including non-ASCII text
    like accented letters or emoji — passes through unchanged.

    This intentionally does NOT use Python's `str.encode().decode(
    "unicode_escape")` shortcut: that codec treats its input as Latin-1
    bytes, so any non-ASCII character gets silently corrupted (each
    UTF-8 byte reinterpreted as its own separate character). Walking
    the string ourselves keeps every Unicode character intact.
    """
    if "\\" not in s:
        return s
    result = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt in _STRING_ESCAPES:
                result.append(_STRING_ESCAPES[nxt])
            else:
                # Unrecognized escape (e.g. \d, \w in a regex pattern) —
                # keep both characters literally rather than swallowing
                # the backslash, so patterns meant for the `re` library
                # survive a Lumen string literal intact.
                result.append(ch)
                result.append(nxt)
            i += 2
            continue
        result.append(ch)
        i += 1
    return "".join(result)


class Token:
    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r})"


def tokenize(source):
    tokens = []
    line = 1
    pos = 0
    while pos < len(source):
        m = MASTER_RE.match(source, pos)
        if not m:
            raise SyntaxError(f"Unexpected character {source[pos]!r} on line {line}")
        kind = m.lastgroup
        value = m.group()
        if kind == "NEWLINE":
            line += 1
        elif kind in ("SKIP", "COMMENT"):
            pass
        elif kind == "BLOCKCOMMENT":
            line += value.count("\n")
        elif kind == "NUMBER":
            value = float(value) if "." in value else int(value)
            tokens.append(Token("NUMBER", value, line))
        elif kind == "STRING":
            tokens.append(Token("STRING", unescape_string(value[1:-1]), line))
        elif kind == "FSTRING":
            # keep the raw (undecoded) inner text; interpolation splitting
            # happens at parse time so `{` / `}` aren't touched by escaping.
            tokens.append(Token("FSTRING", value[2:-1], line))
        elif kind == "ID":
            tokens.append(Token(value if value in KEYWORDS else "ID", value, line))
        else:
            tokens.append(Token(value, value, line))
        pos = m.end()
    tokens.append(Token("EOF", None, line))
    return tokens


# ----------------------------------------------------------------------
# 2. PARSER — turns tokens into an Abstract Syntax Tree (nested tuples)
# ----------------------------------------------------------------------
# Each AST node is a tuple: (node_type, ...fields)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def peek_next(self):
        return self.tokens[self.i + 1] if self.i + 1 < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def expect(self, kind):
        tok = self.peek()
        if tok.kind != kind:
            raise SyntaxError(f"Line {tok.line}: expected {kind}, got {tok.kind} ({tok.value!r})")
        return self.advance()

    def check(self, kind):
        return self.peek().kind == kind

    def parse_program(self):
        stmts = []
        while not self.check("EOF"):
            stmts.append(self.parse_statement())
        return ("block", stmts)

    def parse_expression_only(self):
        expr = self.parse_expression()
        self.expect("EOF")
        return expr

    def parse_block(self):
        self.expect("{")
        stmts = []
        while not self.check("}"):
            stmts.append(self.parse_statement())
        self.expect("}")
        return ("block", stmts)

    def parse_statement(self):
        tok = self.peek()
        if tok.kind == "let":
            self.advance()
            name = self.expect("ID").value
            self.expect("=")
            expr = self.parse_expression()
            self.skip_semi()
            return ("let", name, expr)
        if tok.kind == "if":
            self.advance()
            cond = self.parse_expression()
            then_block = self.parse_block()
            else_block = self.parse_else_tail()
            return ("if", cond, then_block, else_block)
        if tok.kind == "while":
            self.advance()
            cond = self.parse_expression()
            body = self.parse_block()
            return ("while", cond, body)
        if tok.kind == "for":
            self.advance()
            if self.check("ID") and self.peek_next().kind == "in":
                varname = self.advance().value
                self.advance()  # consume 'in'
                iterable = self.parse_expression()
                body = self.parse_block()
                return ("forin", varname, iterable, body)
            init = self.parse_statement()
            cond = self.parse_expression()
            self.expect(";")
            update = self.parse_statement()
            body = self.parse_block()
            return ("for", init, cond, update, body)
        if tok.kind == "fn":
            self.advance()
            name = self.expect("ID").value
            self.expect("(")
            params = []
            if not self.check(")"):
                params.append(self.expect("ID").value)
                while self.check(","):
                    self.advance()
                    params.append(self.expect("ID").value)
            self.expect(")")
            body = self.parse_block()
            return ("fndef", name, params, body)
        if tok.kind == "return":
            self.advance()
            expr = None
            if not self.check(";") and not self.check("}"):
                expr = self.parse_expression()
            self.skip_semi()
            return ("return", expr)
        if tok.kind == "break":
            self.advance()
            self.skip_semi()
            return ("break",)
        if tok.kind == "continue":
            self.advance()
            self.skip_semi()
            return ("continue",)
        if tok.kind == "try":
            self.advance()
            try_block = self.parse_block()
            self.expect("catch")
            err_name = self.expect("ID").value
            catch_block = self.parse_block()
            return ("try", try_block, err_name, catch_block)
        if tok.kind == "class":
            self.advance()
            name = self.expect("ID").value
            body = self.parse_block()
            return ("classdef", name, body)
        if tok.kind == "import":
            self.advance()
            name = self.expect("STRING").value
            alias = None
            if self.check("as"):
                self.advance()
                alias = self.expect("ID").value
            self.skip_semi()
            return ("import", name, alias)
        # expression statement (e.g. run(x) or assignment)
        expr = self.parse_expression()
        self.skip_semi()
        return ("exprstmt", expr)

    def parse_else_tail(self):
        """Handles the elif/else chain following an `if`'s then-block."""
        if self.check("elif"):
            self.advance()
            cond = self.parse_expression()
            then_block = self.parse_block()
            else_block = self.parse_else_tail()
            return ("block", [("if", cond, then_block, else_block)])
        if self.check("else"):
            self.advance()
            return self.parse_block() if self.check("{") else ("block", [self.parse_statement()])
        return None

    def skip_semi(self):
        if self.check(";"):
            self.advance()

    # --- expression parsing (precedence climbing) ---
    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_or()
        if self.check("=") and left[0] == "var":
            self.advance()
            value = self.parse_assignment()
            return ("assign", left[1], value)
        if self.check("=") and left[0] == "index":
            self.advance()
            value = self.parse_assignment()
            return ("indexassign", left[1], left[2], value)
        if self.check("=") and left[0] == "getattr":
            self.advance()
            value = self.parse_assignment()
            return ("attrassign", left[1], left[2], value)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.check("||"):
            self.advance()
            left = ("binop", "||", left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check("&&"):
            self.advance()
            left = ("binop", "&&", left, self.parse_equality())
        return left

    def parse_equality(self):
        left = self.parse_bitor()
        while self.peek().kind in ("==", "!="):
            op = self.advance().kind
            left = ("binop", op, left, self.parse_bitor())
        return left

    def parse_bitor(self):
        left = self.parse_bitxor()
        while self.check("|"):
            self.advance()
            left = ("binop", "|", left, self.parse_bitxor())
        return left

    def parse_bitxor(self):
        left = self.parse_bitand()
        while self.check("^"):
            self.advance()
            left = ("binop", "^", left, self.parse_bitand())
        return left

    def parse_bitand(self):
        left = self.parse_shift()
        while self.check("&"):
            self.advance()
            left = ("binop", "&", left, self.parse_shift())
        return left

    def parse_shift(self):
        left = self.parse_comparison()
        while self.peek().kind in ("<<", ">>"):
            op = self.advance().kind
            left = ("binop", op, left, self.parse_comparison())
        return left

    def parse_comparison(self):
        left = self.parse_term()
        while self.peek().kind in ("<", ">", "<=", ">="):
            op = self.advance().kind
            left = ("binop", op, left, self.parse_term())
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().kind in ("+", "-"):
            op = self.advance().kind
            left = ("binop", op, left, self.parse_factor())
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek().kind in ("*", "/", "%"):
            op = self.advance().kind
            left = ("binop", op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.peek().kind in ("-", "!"):
            op = self.advance().kind
            return ("unop", op, self.parse_unary())
        return self.parse_power()

    def parse_power(self):
        left = self.parse_call()
        if self.check("**"):
            self.advance()
            right = self.parse_unary()  # right-associative
            return ("binop", "**", left, right)
        return left

    def parse_call(self):
        expr = self.parse_primary()
        while True:
            if self.check("("):
                self.advance()
                args = []
                if not self.check(")"):
                    args.append(self.parse_expression())
                    while self.check(","):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(")")
                expr = ("call", expr, args)
            elif self.check("["):
                self.advance()
                index = self.parse_expression()
                self.expect("]")
                expr = ("index", expr, index)
            elif self.check("."):
                self.advance()
                member = self.expect("ID").value
                expr = ("getattr", expr, member)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.advance()
            return ("num", tok.value)
        if tok.kind == "STRING":
            self.advance()
            return ("str", tok.value)
        if tok.kind == "FSTRING":
            self.advance()
            return ("fstring", parse_fstring_parts(tok.value))
        if tok.kind == "true":
            self.advance()
            return ("bool", True)
        if tok.kind == "false":
            self.advance()
            return ("bool", False)
        if tok.kind == "new":
            self.advance()
            name = self.expect("ID").value
            self.expect("(")
            args = []
            if not self.check(")"):
                args.append(self.parse_expression())
                while self.check(","):
                    self.advance()
                    args.append(self.parse_expression())
            self.expect(")")
            return ("new", name, args)
        if tok.kind == "ID":
            self.advance()
            return ("var", tok.value)
        if tok.kind == "(":
            self.advance()
            expr = self.parse_expression()
            self.expect(")")
            return expr
        if tok.kind == "[":
            self.advance()
            elements = []
            if not self.check("]"):
                elements.append(self.parse_expression())
                while self.check(","):
                    self.advance()
                    elements.append(self.parse_expression())
            self.expect("]")
            return ("list", elements)
        if tok.kind == "{":
            self.advance()
            pairs = []
            if not self.check("}"):
                pairs.append(self.parse_dict_pair())
                while self.check(","):
                    self.advance()
                    pairs.append(self.parse_dict_pair())
            self.expect("}")
            return ("dict", pairs)
        raise SyntaxError(f"Line {tok.line}: unexpected token {tok.kind} ({tok.value!r})")

    def parse_dict_pair(self):
        key = self.parse_expression()
        self.expect(":")
        value = self.parse_expression()
        return (key, value)


def parse_fstring_parts(raw):
    """Splits an f-string's raw inner text into literal / {expr} parts."""
    parts = []
    buf = ""
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "{":
            if buf:
                parts.append(("lit", unescape_string(buf)))
                buf = ""
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if raw[j] == "{":
                    depth += 1
                elif raw[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth != 0:
                raise SyntaxError("Unclosed '{' in f-string")
            expr_src = raw[i + 1:j]
            expr_ast = Parser(tokenize(expr_src)).parse_expression_only()
            parts.append(("expr", expr_ast))
            i = j + 1
        else:
            buf += ch
            i += 1
    if buf:
        parts.append(("lit", unescape_string(buf)))
    return parts


def parse(source):
    return Parser(tokenize(source)).parse_program()


# ----------------------------------------------------------------------
# 3. INTERPRETER — walks the AST and executes it
# ----------------------------------------------------------------------

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined variable '{name}'")

    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        self.vars[name] = value

    def define(self, name, value):
        self.vars[name] = value


class Function:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def call(self, interp, args):
        env = Environment(self.closure)
        for p, a in zip(self.params, args):
            env.define(p, a)
        try:
            interp.exec_block(self.body, env)
        except ReturnSignal as r:
            return r.value
        return None


class ClassDef:
    """A Lumen `class` — just a name plus a dict of methods (Functions)."""

    def __init__(self, name, methods):
        self.name = name
        self.methods = methods

    def find_method(self, name):
        return self.methods.get(name)


class Instance:
    """A runtime object created by `new ClassName(...)`."""

    def __init__(self, classdef):
        self.classdef = classdef
        self.fields = {}


class Interpreter:
    def __init__(self, search_paths=None):
        self.globals = Environment()
        self.search_paths = search_paths or []
        self.loaded_modules = set()

        # Directory containing the currently running .lu script.
        # The REPL defaults to the current working directory.
        self.script_filename = None
        self.script_dir = os.getcwd()

        install_builtins(self.globals, self)
        install_native_libs(self)

    def run(self, source, filename="<program>"):
        self.script_filename = filename

        if filename != "<program>":
            self.script_dir = os.path.dirname(os.path.abspath(filename))
        else:
            self.script_dir = os.getcwd()

        ast = parse(source)
        self.exec_block(ast, self.globals)

    def exec_block(self, block, env):
        for stmt in block[1]:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        kind = stmt[0]
        if kind == "let":
            _, name, expr = stmt
            env.define(name, self.eval(expr, env))
        elif kind == "exprstmt":
            self.eval(stmt[1], env)
        elif kind == "if":
            _, cond, then_b, else_b = stmt
            if self.eval(cond, env):
                self.exec_block(then_b, Environment(env))
            elif else_b:
                self.exec_block(else_b, Environment(env))
        elif kind == "while":
            _, cond, body = stmt
            while self.eval(cond, env):
                try:
                    self.exec_block(body, Environment(env))
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif kind == "for":
            _, init, cond, update, body = stmt
            loop_env = Environment(env)
            self.exec_stmt(init, loop_env)
            while self.eval(cond, loop_env):
                try:
                    self.exec_block(body, Environment(loop_env))
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                self.exec_stmt(update, loop_env)
        elif kind == "forin":
            _, varname, iterable_expr, body = stmt
            iterable = self.eval(iterable_expr, env)
            for item in iterable:
                loop_env = Environment(env)
                loop_env.define(varname, item)
                try:
                    self.exec_block(body, loop_env)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif kind == "break":
            raise BreakSignal()
        elif kind == "continue":
            raise ContinueSignal()
        elif kind == "try":
            _, try_block, err_name, catch_block = stmt
            try:
                self.exec_block(try_block, Environment(env))
            except (ReturnSignal, BreakSignal, ContinueSignal):
                raise
            except Exception as e:
                catch_env = Environment(env)
                catch_env.define(err_name, str(e))
                self.exec_block(catch_block, catch_env)
        elif kind == "fndef":
            _, name, params, body = stmt
            env.define(name, Function(name, params, body, env))
        elif kind == "classdef":
            _, name, body = stmt
            methods = {}
            for m in body[1]:
                if m[0] != "fndef":
                    raise SyntaxError(
                        f"class '{name}' bodies may only contain function definitions"
                    )
                _, mname, params, mbody = m
                methods[mname] = Function(mname, params, mbody, env)
            env.define(name, ClassDef(name, methods))
        elif kind == "return":
            _, expr = stmt
            value = self.eval(expr, env) if expr else None
            raise ReturnSignal(value)
        elif kind == "import":
            _, name, alias = stmt
            self.do_import(name, env, alias)
        else:
            raise RuntimeError(f"Unknown statement {kind}")

    def do_import(self, name, env, alias=None):
        if alias:
            # namespaced import: load into an isolated scope, expose that
            # scope's bindings as a dict so `alias.thing` works via getattr.
            temp_env = Environment()
            if name in NATIVE_LIBS:
                NATIVE_LIBS[name](self, temp_env)
                self._load_sub_companion(name, temp_env, required=False)
            else:
                self._load_sub_companion(name, temp_env, required=True)
            env.define(alias, temp_env.vars)
            return
        if name in self.loaded_modules:
            return
        self.loaded_modules.add(name)
        if name in NATIVE_LIBS:
            NATIVE_LIBS[name](self, env)
            self._load_sub_companion(name, env)
            return
        self._load_sub_companion(name, env, required=True)

    def _load_sub_companion(self, name, env, required=False):
        for base in self.search_paths + [os.path.join(get_base_dir(), "libs")]:
            path = os.path.join(base, name + ".lu")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    src = f.read()
                self.exec_block(parse(src), env)
                return
        if required:
            raise ImportError(f"Could not find library '{name}' (looked for native lib or {name}.lu)")

    def eval(self, node, env):
        kind = node[0]
        if kind == "num":
            return node[1]
        if kind == "str":
            return node[1]
        if kind == "bool":
            return node[1]
        if kind == "fstring":
            result = ""
            for part in node[1]:
                if part[0] == "lit":
                    result += part[1]
                else:
                    val = self.eval(part[1], env)
                    result += str(to_display(val))
            return result
        if kind == "var":
            return env.get(node[1])
        if kind == "assign":
            value = self.eval(node[2], env)
            env.set(node[1], value)
            return value
        if kind == "list":
            return [self.eval(e, env) for e in node[1]]
        if kind == "dict":
            d = {}
            for k_node, v_node in node[1]:
                d[self.eval(k_node, env)] = self.eval(v_node, env)
            return d
        if kind == "getattr":
            obj = self.eval(node[1], env)
            member = node[2]
            return self._getattr(obj, member)
        if kind == "attrassign":
            obj = self.eval(node[1], env)
            member = node[2]
            value = self.eval(node[3], env)
            if isinstance(obj, Instance):
                obj.fields[member] = value
                return value
            if isinstance(obj, dict):
                obj[member] = value
                return value
            raise TypeError(f"cannot set attribute '.{member}' on a value of type {type(obj).__name__}")
        if kind == "new":
            _, classname, arg_nodes = node
            classdef = env.get(classname)
            if not isinstance(classdef, ClassDef):
                raise TypeError(f"'{classname}' is not a class")
            args = [self.eval(a, env) for a in arg_nodes]
            instance = Instance(classdef)
            init_method = classdef.find_method("init")
            if init_method is not None:
                init_method.call(self, [instance] + args)
            return instance
        if kind == "index":
            target = self.eval(node[1], env)
            idx = self.eval(node[2], env)
            if isinstance(target, dict):
                try:
                    return target[idx]
                except KeyError:
                    raise KeyError(f"key {idx!r} not found") from None
            try:
                return target[int(idx)]
            except IndexError:
                raise IndexError(
                    f"Index {int(idx)} out of range for a value of length {len(target)}"
                ) from None
            except TypeError:
                raise TypeError(f"Cannot index into a value of type {type(target).__name__}")
        if kind == "indexassign":
            target = self.eval(node[1], env)
            idx = self.eval(node[2], env)
            value = self.eval(node[3], env)
            if isinstance(target, dict):
                target[idx] = value
                return value
            if not isinstance(target, list):
                raise TypeError("Only lists and dicts support index assignment (e.g. list[0] = value)")
            try:
                target[int(idx)] = value
            except IndexError:
                raise IndexError(
                    f"Index {int(idx)} out of range for a list of length {len(target)}"
                ) from None
            return value
        if kind == "unop":
            op, operand = node[1], self.eval(node[2], env)
            if op == "-":
                return -operand
            if op == "!":
                return not operand
        if kind == "binop":
            op = node[1]
            left = self.eval(node[2], env)
            right = self.eval(node[3], env)
            return apply_binop(op, left, right)
        if kind == "call":
            fn = self.eval(node[1], env)
            args = [self.eval(a, env) for a in node[2]]
            if isinstance(fn, Function):
                return fn.call(self, args)
            if callable(fn):
                return fn(*args)
            raise TypeError(f"value is not callable")
        raise RuntimeError(f"Unknown expression {kind}")

    def _getattr(self, obj, member):
        if isinstance(obj, Instance):
            if member in obj.fields:
                return obj.fields[member]
            method = obj.classdef.find_method(member)
            if method is not None:
                def bound(*args, _method=method, _obj=obj):
                    return _method.call(self, [_obj] + list(args))
                return bound
            raise AttributeError(f"'{obj.classdef.name}' has no attribute '{member}'")
        if isinstance(obj, dict):
            if member in obj:
                val = obj[member]
                if isinstance(val, Function):
                    def wrapped(*args, _val=val):
                        return _val.call(self, list(args))
                    return wrapped
                return val
            raise AttributeError(f"no '{member}' found")
        raise AttributeError(f"cannot access '.{member}' on a value of type {type(obj).__name__}")


def apply_binop(op, left, right):
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        return left / right
    if op == "%":
        return left % right
    if op == "**":
        return left ** right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right
    if op == "<":
        return left < right
    if op == ">":
        return left > right
    if op == "<=":
        return left <= right
    if op == ">=":
        return left >= right
    if op == "&&":
        return bool(left) and bool(right)
    if op == "||":
        return bool(left) or bool(right)
    if op == "&":
        return int(left) & int(right)
    if op == "|":
        return int(left) | int(right)
    if op == "^":
        return int(left) ^ int(right)
    if op == "<<":
        return int(left) << int(right)
    if op == ">>":
        return int(left) >> int(right)
    raise RuntimeError(f"Unknown operator {op}")


# ----------------------------------------------------------------------
# 4. BUILTINS — functions available without any import
# ----------------------------------------------------------------------

def lumen_print(*args):
    print(*[to_display(a) for a in args])
    return None


def to_display(v):
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, list):
        return format_list(v)
    if isinstance(v, dict):
        return format_dict(v)
    if isinstance(v, Instance):
        return f"<{v.classdef.name} instance>"
    return v


def format_value(v):
    """Like to_display, but strings stay quoted — used for nested values."""
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, list):
        return format_list(v)
    if isinstance(v, dict):
        return format_dict(v)
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "null"
    if isinstance(v, Instance):
        return f"<{v.classdef.name} instance>"
    return str(v)


def format_list(lst):
    return "[" + ", ".join(format_value(e) for e in lst) + "]"


def format_dict(d):
    parts = []
    for k, v in d.items():
        key_repr = format_value(k) if isinstance(k, str) else str(to_display(k))
        parts.append(f"{key_repr}: {format_value(v)}")
    return "{" + ", ".join(parts) + "}"


def install_builtins(global_env, interp=None):
    global_env.define("run", lumen_print)
    global_env.define("len", lambda x: len(x))
    global_env.define("str", lambda x: str(to_display(x)))
    global_env.define("num", lambda x: float(x) if "." in str(x) else int(x))
    global_env.define("ord", lambda ch: ord(str(ch)[0]))
    global_env.define("chr", lambda n: chr(int(n)))
    global_env.define("input", lambda prompt="": input(str(prompt)))
    global_env.define("typeOf", lambda x: lumen_type_name(x))

    # Directory containing the currently running .lu script.
    # This is useful for scripts that need to find files beside themselves.
    if interp is not None:
        global_env.define("scriptDir", lambda: interp.script_dir)
        global_env.define("scriptPath", lambda: interp.script_filename)

    # dict helpers (bracket indexing/assignment already works on dicts;
    # these cover the operations indexing alone can't express)
    global_env.define("keys", lambda d: list(d.keys()))
    global_env.define("values", lambda d: list(d.values()))
    global_env.define("hasKey", lambda d, k: k in d)
    global_env.define("removeKey", lambda d, k: (d.pop(k, None), d)[1])


def lumen_type_name(x):
    if x is True or x is False:
        return "bool"
    if x is None:
        return "null"
    if isinstance(x, (int, float)):
        return "number"
    if isinstance(x, str):
        return "string"
    if isinstance(x, list):
        return "list"
    if isinstance(x, dict):
        return "dict"
    if isinstance(x, Instance):
        return x.classdef.name
    if isinstance(x, (Function, ClassDef)) or callable(x):
        return "function"
    return "unknown"


# ----------------------------------------------------------------------
# 5. NATIVE LIBRARIES — the plugin registry for Python-backed libraries
# ----------------------------------------------------------------------

NATIVE_LIBS = {}


def register_native_lib(name):
    def decorator(fn):
        NATIVE_LIBS[name] = fn
        return fn
    return decorator


@register_native_lib("sys")
def _lib_sys(interp, env):
    import time
    env.define("clock", lambda: time.time())
    env.define("sleep", lambda s: time.sleep(s))


@register_native_lib("random")
def _lib_random(interp, env):
    import random
    env.define("rand", lambda: random.random())
    env.define("randint", lambda a, b: random.randint(int(a), int(b)))


@register_native_lib("mathx")
def _lib_mathx(interp, env):
    import math
    env.define("sqrt", lambda x: math.sqrt(x))
    env.define("floor", lambda x: math.floor(x))
    env.define("ceil", lambda x: math.ceil(x))
    env.define("round", lambda x: round(x))
    env.define("log", lambda x: math.log(x))
    env.define("log10", lambda x: math.log10(x))
    env.define("sin", lambda x: math.sin(x))
    env.define("cos", lambda x: math.cos(x))
    env.define("tan", lambda x: math.tan(x))
    env.define("PI", math.pi)
    env.define("E", math.e)


@register_native_lib("strings")
def _lib_strings(interp, env):
    """String manipulation, backed by Python's str methods."""

    def split(s, sep=" "):
        return list(str(s).split(str(sep)))

    def join(lst, sep=""):
        return str(sep).join(str(to_display(x)) if not isinstance(x, str) else x for x in lst)

    def replace(s, old, new):
        return str(s).replace(str(old), str(new))

    def substring(s, start, end=None):
        s = str(s)
        start = int(start)
        if end is None:
            return s[start:]
        return s[start:int(end)]

    env.define("upper", lambda s: str(s).upper())
    env.define("lower", lambda s: str(s).lower())
    env.define("trim", lambda s: str(s).strip())
    env.define("split", split)
    env.define("join", join)
    env.define("contains", lambda s, sub: str(sub) in str(s))
    env.define("replace", replace)
    env.define("indexOf", lambda s, sub: str(s).find(str(sub)))
    env.define("startsWith", lambda s, prefix: str(s).startswith(str(prefix)))
    env.define("endsWith", lambda s, suffix: str(s).endswith(str(suffix)))
    env.define("charAt", lambda s, i: str(s)[int(i)])
    env.define("substring", substring)
    env.define("repeat", lambda s, n: str(s) * int(n))
    env.define("isEmpty", lambda s: len(str(s)) == 0)


@register_native_lib("lists")
def _lib_lists(interp, env):
    """List/array operations. List literals ([1, 2, 3]) and indexing
    (list[0], list[0] = x) work everywhere without importing anything —
    this library adds the higher-level operations on top of them."""

    def call_fn(fn, args):
        if isinstance(fn, Function):
            return fn.call(interp, args)
        if callable(fn):
            return fn(*args)
        raise TypeError("expected a function")

    def push(lst, value):
        lst.append(value)
        return lst

    def pop(lst):
        if not lst:
            raise IndexError("pop() called on an empty list")
        return lst.pop()

    def insert(lst, index, value):
        lst.insert(int(index), value)
        return lst

    def remove_at(lst, index):
        return lst.pop(int(index))

    def index_of(lst, value):
        try:
            return lst.index(value)
        except ValueError:
            return -1

    def slice_(lst, start, end=None):
        if end is None:
            return lst[int(start):]
        return lst[int(start):int(end)]

    def sort_(lst):
        return sorted(lst)

    def map_(lst, fn):
        return [call_fn(fn, [x]) for x in lst]

    def filter_(lst, fn):
        return [x for x in lst if call_fn(fn, [x])]

    def for_each(lst, fn):
        for x in lst:
            call_fn(fn, [x])
        return None

    def reduce_(lst, fn, initial):
        acc = initial
        for x in lst:
            acc = call_fn(fn, [acc, x])
        return acc

    env.define("push", push)
    env.define("pop", pop)
    env.define("insert", insert)
    env.define("removeAt", remove_at)
    env.define("indexOf", index_of)
    env.define("contains", lambda lst, value: value in lst)
    env.define("reverse", lambda lst: list(reversed(lst)))
    env.define("slice", slice_)
    env.define("sort", sort_)
    env.define("copy", lambda lst: list(lst))
    env.define("isEmpty", lambda lst: len(lst) == 0)
    env.define("first", lambda lst: lst[0])
    env.define("last", lambda lst: lst[-1])
    env.define("map", map_)
    env.define("filter", filter_)
    env.define("forEach", for_each)
    env.define("reduce", reduce_)


@register_native_lib("os")
def _lib_os(interp, env):
    """Machine & process info: env vars, platform detection, cwd, shell
    commands. See docs/os-library.md for the full contract — libs/os.lu
    layers a few pure-Lumen helpers (isMac/isWindows/isLinux, etc.) on
    top of the primitives defined here.
    """
    import platform as _platform
    import subprocess
    import socket
    import tempfile

    def get_env(name, default=""):
        return os.environ.get(str(name), default)

    def set_env(name, value):
        os.environ[str(name)] = str(value)
        return True

    def has_env(name):
        return str(name) in os.environ

    def env_vars():
        return dict(os.environ)

    def current_platform():
        system = _platform.system()
        if system == "Darwin":
            return "mac"
        if system == "Windows":
            return "windows"
        if system == "Linux":
            return "linux"
        return system.lower()

    def get_hostname():
        return socket.gethostname()

    def get_cwd():
        return os.getcwd()

    def change_dir(path):
        os.chdir(str(path))
        return True

    def home_dir():
        return os.path.expanduser("~")

    def temp_dir():
        return tempfile.gettempdir()

    def run_command(cmd):
        result = subprocess.run(
            str(cmd), shell=True, capture_output=True, text=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "code": result.returncode,
        }

    def do_exit(code=0):
        sys.exit(int(code))

    env.define("getEnv", get_env)
    env.define("setEnv", set_env)
    env.define("hasEnv", has_env)
    env.define("envVars", env_vars)

    env.define("platform", current_platform)
    env.define("hostname", get_hostname)
    env.define("cwd", get_cwd)
    env.define("changeDir", change_dir)
    env.define("homeDir", home_dir)
    env.define("tempDir", temp_dir)
    env.define("pathSep", os.sep)
    env.define("exit", do_exit)

    env.define("runCommand", run_command)


@register_native_lib("system")
def _lib_system(interp, env):
    """Desktop & system-control library.

    Lets a Lumen program interact with the host machine: change the
    desktop wallpaper, post native notifications, show dialog boxes,
    open URLs/files in the default app, open tabs in the default browser,
    speak text aloud, get/set the clipboard, and adjust system volume.

    Functions:
        setWallpaper(imagePath)
        notify(title, message, subtitle=None, sound=False)
        alert(message, title="")
        confirm(message, title="")          -> bool
        prompt(question, default="", title="") -> str | ""
        openUrl(url)
        openFile(path)
        openBrowserTab(url)
        say(text, voice=None)
        clipboardGet()                       -> str
        clipboardSet(text)                   -> bool
        setVolume(level)                     # 0..100 (macOS only)
        getVolume()                          -> int (0..100, macOS only)
        beep()
        systemInfo()                         -> dict

    Anything macOS-only (volume, default wallpaper set) silently no-ops
    on other platforms; functions that aren't meaningful (e.g. setVolume
    on Linux) return False instead of crashing.
    """
    import platform as _platform
    import subprocess
    import shutil
    import json
    import webbrowser

    _system = _platform.system()  # "Darwin" | "Windows" | "Linux"

    # --- Wallpaper ----------------------------------------------------

    def set_wallpaper(image_path):
        """Set the desktop wallpaper to the image at `image_path`.

        macOS uses AppleScript against System Events; Windows uses the
        SystemParametersInfo SPI_SETDESKWALLPAPER call via PowerShell;
        Linux is best-effort via `gsettings` (GNOME) and falls back to
        `feh` if available. Returns True on success.
        """
        path = str(image_path)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if not os.path.exists(path):
            return False

        try:
            if _system == "Darwin":
                script = (
                    'tell application "System Events" to set picture of '
                    f'desktop 1 to POSIX file "{path}"'
                )
                subprocess.run(["osascript", "-e", script], check=True)
                return True
            elif _system == "Windows":
                # PowerShell call to the Win32 API.
                ps = (
                    "Add-Type -TypeDefinition "
                    "\"using System.Runtime.InteropServices; "
                    "public class W {[DllImport(\\\"user32.dll\\\",CharSet=CharSet.Auto)] "
                    "public static extern int SystemParametersInfo(int a,int b,string c,int d;)}\";"
                    "[W]::SystemParametersInfo(0x0014, 0, "
                    f"'{path}', 0x00000001)"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    check=True,
                )
                return True
            elif _system == "Linux":
                uri = "file://" + path
                # GNOME
                r = subprocess.run(
                    [
                        "gsettings",
                        "set",
                        "org.gnome.desktop.background",
                        "picture-uri",
                        uri,
                    ],
                    capture_output=True,
                )
                if r.returncode == 0:
                    # Also set the "picture-uri-dark" key on newer GNOME.
                    subprocess.run(
                        [
                            "gsettings",
                            "set",
                            "org.gnome.desktop.background",
                            "picture-uri-dark",
                            uri,
                        ],
                        capture_output=True,
                    )
                    return True
                # Fallback: feh (writes ~/.fehbg)
                if shutil.which("feh"):
                    subprocess.run(["feh", "--bg-fill", path], check=True)
                    return True
                return False
            return False
        except Exception:
            return False

    # --- Notifications ------------------------------------------------

    def notify(title, message, subtitle=None, sound=False):
        """Post a native OS notification. Returns True if dispatched."""
        try:
            if _system == "Darwin":
                safe = lambda s: str(s).replace("\\", "\\\\").replace('"', '\\"')
                sub = f' subtitle "{safe(subtitle)}"' if subtitle else ""
                snd = " sound name \"Glass\"" if sound else ""
                script = (
                    f'display notification "{safe(message)}" '
                    f'with title "{safe(title)}"{sub}{snd}'
                )
                subprocess.run(["osascript", "-e", script], check=True)
                return True
            elif _system == "Linux":
                if shutil.which("notify-send"):
                    args = ["notify-send"]
                    if sound:
                        # urgency=critical makes some desktops play a sound
                        args += ["-u", "critical"]
                    args += [str(title), str(message)]
                    subprocess.run(args, check=True)
                    return True
                return False
            elif _system == "Windows":
                # BurntToast if available, else fall back to a MessageBox
                # via PowerShell (which is a blocking modal — last resort).
                ps = (
                    f"New-BurntToastNotification -Text '{title}', '{message}'"
                )
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True,
                )
                if r.returncode == 0:
                    return True
                return False
            return False
        except Exception:
            return False

    # --- Dialogs (blocking modals on macOS/Windows) -------------------

    def alert(message, title=""):
        """Show a blocking OK dialog. Returns None."""
        try:
            if _system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display alert "{title}" message "{message}" as informational',
                    ],
                    check=True,
                )
                return True
            elif _system == "Windows":
                ps = (
                    f"[System.Windows.MessageBox]::Show('{message}', '{title}', "
                    "'OK', 'Information')"
                )
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Add-Type -AssemblyName PresentationFramework; {ps}",
                    ],
                    check=True,
                )
                return True
            elif _system == "Linux":
                if shutil.which("zenity"):
                    subprocess.run(
                        [
                            "zenity",
                            "--info",
                            "--title",
                            str(title) or "Alert",
                            "--text",
                            str(message),
                        ],
                        check=True,
                    )
                    return True
                if shutil.which("notify-send"):
                    subprocess.run(
                        ["notify-send", str(title) or "Alert", str(message)],
                        check=True,
                    )
                    return True
                return False
            return False
        except Exception:
            return False

    def confirm(message, title=""):
        """Blocking Yes/No dialog. Returns True/False."""
        try:
            if _system == "Darwin":
                r = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display alert "{title}" message "{message}" as informational',
                    ],
                    capture_output=True,
                    text=True,
                )
                # osascript returns "button returned:OK" or "Cancel" etc.
                out = (r.stdout or "") + (r.stderr or "")
                return "OK" in out
            elif _system == "Windows":
                ps = (
                    "[System.Windows.MessageBox]::Show('"
                    + str(message).replace("'", "''")
                    + "','"
                    + str(title).replace("'", "''")
                    + "', 'YesNo', 'Question') -eq 'Yes'"
                )
                r = subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f"Add-Type -AssemblyName PresentationFramework; {ps}",
                    ],
                    capture_output=True,
                    text=True,
                )
                return "True" in (r.stdout or "")
            elif _system == "Linux":
                if shutil.which("zenity"):
                    r = subprocess.run(
                        [
                            "zenity",
                            "--question",
                            "--title",
                            str(title) or "Confirm",
                            "--text",
                            str(message),
                        ],
                    )
                    return r.returncode == 0
                return False
            return False
        except Exception:
            return False

    def prompt(question, default="", title=""):
        """Blocking text-input dialog. Returns the entered string,
        or "" if cancelled / unsupported."""
        try:
            if _system == "Darwin":
                default_safe = str(default).replace("\\", "\\\\").replace('"', '\\"')
                q_safe = str(question).replace("\\", "\\\\").replace('"', '\\"')
                script = (
                    f'set theAnswer to text returned of (display dialog '
                    f'"{q_safe}" default answer "{default_safe}" '
                    f'with title "{title}")\n'
                    'return theAnswer'
                )
                r = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                )
                return (r.stdout or "").strip() if r.returncode == 0 else ""
            elif _system == "Linux":
                if shutil.which("zenity"):
                    r = subprocess.run(
                        [
                            "zenity",
                            "--entry",
                            "--title",
                            str(title) or "Input",
                            "--text",
                            str(question),
                            "--entry-text",
                            str(default),
                        ],
                        capture_output=True,
                        text=True,
                    )
                    return (r.stdout or "").strip() if r.returncode == 0 else ""
                return ""
            return ""
        except Exception:
            return ""

    # --- Openers (URL / file / browser tab) ---------------------------

    def open_url(url):
        """Open a URL in the OS default handler (browser for http(s),
        Spotify for spotify:, etc.)."""
        try:
            if _system == "Darwin":
                subprocess.run(["open", str(url)], check=True)
                return True
            elif _system == "Windows":
                os.startfile(str(url))  # type: ignore[attr-defined]
                return True
            elif _system == "Linux":
                subprocess.run(["xdg-open", str(url)], check=True)
                return True
            return False
        except Exception:
            return False

    def open_file(path):
        """Open a file path in the default app for its type."""
        return open_url(path)

    def open_browser_tab(url):
        """Open `url` as a new tab in the default browser.

        macOS: uses AppleScript to target the front browser (or launches
        one) and asks it to open a new tab with the URL.
        Windows/Linux: falls back to webbrowser.open_new_tab.
        """
        try:
            if _system == "Darwin":
                safe = str(url).replace("\\", "\\\\").replace('"', '\\"')
                script = (
                    'tell application "System Events"\n'
                    '  set frontBrowser to first application process '
                    'whose frontmost is true and (name contains "Safari" '
                    'or name contains "Chrome" or name contains "Firefox" '
                    'or name contains "Brave" or name contains "Edge" '
                    'or name contains "Arc")\n'
                    '  set browserName to name of frontBrowser\n'
                    'end tell\n'
                    f'tell application browserName to open location "{safe}"\n'
                )
                r = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                )
                if r.returncode == 0:
                    return True
                # No front browser? Launch Safari with the URL as a new tab.
                subprocess.run(
                    ["osascript", "-e", f'open location "{safe}"'],
                    check=True,
                )
                return True
            elif _system == "Windows":
                # Newer Windows: use msedge default-handler via shell
                # protocol; webbrowser works fine in practice.
                return webbrowser.open_new_tab(str(url))
            elif _system == "Linux":
                subprocess.run(["xdg-open", str(url)], check=True)
                return True
            return False
        except Exception:
            return False

    # --- Clipboard ----------------------------------------------------

    def clipboard_get():
        """Read the current clipboard contents as a string."""
        try:
            if _system == "Darwin":
                r = subprocess.run(["pbpaste"], capture_output=True, text=True)
                return r.stdout if r.returncode == 0 else ""
            elif _system == "Windows":
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                    capture_output=True,
                    text=True,
                )
                return r.stdout if r.returncode == 0 else ""
            elif _system == "Linux":
                if shutil.which("xclip"):
                    r = subprocess.run(
                        ["xclip", "-selection", "clipboard", "-o"],
                        capture_output=True,
                        text=True,
                    )
                    return r.stdout if r.returncode == 0 else ""
                if shutil.which("xsel"):
                    r = subprocess.run(
                        ["xsel", "--clipboard", "--output"],
                        capture_output=True,
                        text=True,
                    )
                    return r.stdout if r.returncode == 0 else ""
                return ""
            return ""
        except Exception:
            return ""

    def clipboard_set(text):
        """Write `text` to the clipboard. Returns True on success."""
        try:
            if _system == "Darwin":
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(str(text).encode("utf-8"))
                return p.returncode == 0
            elif _system == "Windows":
                ps = f"Set-Clipboard -Value '{str(text).replace(chr(39), chr(39)+chr(39))}'"
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True,
                )
                return r.returncode == 0
            elif _system == "Linux":
                if shutil.which("xclip"):
                    p = subprocess.Popen(
                        ["xclip", "-selection", "clipboard"],
                        stdin=subprocess.PIPE,
                    )
                    p.communicate(str(text).encode("utf-8"))
                    return p.returncode == 0
                if shutil.which("xsel"):
                    p = subprocess.Popen(
                        ["xsel", "--clipboard", "--input"],
                        stdin=subprocess.PIPE,
                    )
                    p.communicate(str(text).encode("utf-8"))
                    return p.returncode == 0
                return False
            return False
        except Exception:
            return False

    # --- Speech (TTS) -------------------------------------------------

    def say(text, voice=None):
        """Speak `text` aloud. macOS uses `say` (with optional -v voice).
        Linux uses `espeak` if available, else `spd-say`. Windows uses
        the SpeechSynthesizer COM object via PowerShell. Returns True
        on success."""
        try:
            if _system == "Darwin":
                cmd = ["say"]
                if voice:
                    cmd += ["-v", str(voice)]
                cmd.append(str(text))
                subprocess.run(cmd, check=True)
                return True
            elif _system == "Linux":
                if shutil.which("espeak"):
                    cmd = ["espeak"]
                    if voice:
                        cmd += ["-v", str(voice)]
                    cmd.append(str(text))
                    subprocess.run(cmd, check=True)
                    return True
                if shutil.which("spd-say"):
                    subprocess.run(["spd-say", str(text)], check=True)
                    return True
                return False
            elif _system == "Windows":
                ps = (
                    "Add-Type -AssemblyName System.Speech; "
                    "(New-Object System.Speech.Synthesis.SpeechSynthesizer)."
                    f"Speak('{str(text).replace(chr(39), chr(39)+chr(39))}');"
                )
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True,
                )
                return r.returncode == 0
            return False
        except Exception:
            return False

    # --- Volume -------------------------------------------------------

    def get_volume():
        """Return system volume 0..100. macOS only; -1 on other OS."""
        if _system != "Darwin":
            return -1
        try:
            r = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True,
                text=True,
            )
            return int((r.stdout or "0").strip())
        except Exception:
            return -1

    def set_volume(level):
        """Set system volume (0..100). macOS only; returns False elsewhere."""
        if _system != "Darwin":
            return False
        try:
            v = max(0, min(100, int(level)))
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {v}"],
                check=True,
            )
            return True
        except Exception:
            return False

    # --- Misc ---------------------------------------------------------

    def beep():
        """Make the OS default beep sound."""
        try:
            if _system == "Darwin":
                subprocess.run(["osascript", "-e", "beep"], check=True)
                return True
            elif _system == "Linux":
                if shutil.which("paplay"):
                    subprocess.run(
                        ["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
                        capture_output=True,
                    )
                    return True
                if shutil.which("speaker-test"):
                    subprocess.run(
                        ["speaker-test", "-t", "sine", "-f", "1000", "-l", "1"],
                        capture_output=True,
                    )
                    return True
                print("\a", end="", flush=True)
                return True
            elif _system == "Windows":
                print("\a", end="", flush=True)
                return True
            return False
        except Exception:
            return False

    def system_info():
        """Return a dict with os, version, arch, hostname, user, cwd."""
        info = {
            "os": _system.lower(),
            "version": _platform.version(),
            "release": _platform.release(),
            "arch": _platform.machine(),
            "hostname": _platform.node(),
            "user": os.environ.get("USER") or os.environ.get("USERNAME") or "",
            "cwd": os.getcwd(),
            "python": _platform.python_version(),
        }
        return info

    # Register everything
    env.define("setWallpaper", set_wallpaper)
    env.define("notify", notify)
    env.define("alert", alert)
    env.define("confirm", confirm)
    env.define("prompt", prompt)
    env.define("openUrl", open_url)
    env.define("openFile", open_file)
    env.define("openBrowserTab", open_browser_tab)
    env.define("clipboardGet", clipboard_get)
    env.define("clipboardSet", clipboard_set)
    env.define("say", say)
    env.define("getVolume", get_volume)
    env.define("setVolume", set_volume)
    env.define("beep", beep)
    env.define("systemInfo", system_info)

    # --- Blocking modal "please wait" overlay -----------------------

    def show_wait(message="Working...", title=""):
        """Open a blocking modal window. Returns a dict with:
            setText(newText)  — update the message mid-run
            setProgress(n, total) — show an optional progress bar
            close()            — close the window
        The window is fullscreen-ish (large, on top, no close button)
        and grabs focus so other apps can't be interacted with until
        close() is called. Returns None if Tk isn't available.
        """
        try:
            import tkinter as tk
            from tkinter import ttk
        except Exception:
            return None

        root = tk.Tk()
        root.title(str(title) or "Please wait")
        root.configure(bg="#1c1c1e")
        root.attributes("-topmost", True)
        root.protocol("WM_DELETE_WINDOW", lambda: None)  # disable X

        # Make it big and centered.
        w, h = 520, 220
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        try:
            root.resizable(False, False)
        except Exception:
            pass

        title_lbl = tk.Label(
            root,
            text=str(title) or "Please wait",
            font=("Helvetica", 16, "bold"),
            fg="white",
            bg="#1c1c1e",
        )
        title_lbl.pack(pady=(28, 6))

        msg_var = tk.StringVar(value=str(message))
        msg_lbl = tk.Label(
            root,
            textvariable=msg_var,
            font=("Helvetica", 13),
            fg="#d1d1d6",
            bg="#1c1c1e",
            wraplength=480,
            justify="center",
        )
        msg_lbl.pack(pady=(0, 14))

        prog = ttk.Progressbar(root, length=440, mode="determinate", maximum=100)
        prog.pack(pady=(0, 18))
        prog.pack_forget()  # hidden until setProgress is called

        def pump():
            try:
                root.update()
            except Exception:
                pass

        def _set_progress(n, total=100):
            prog.pack(pady=(0, 18))
            prog.configure(maximum=int(total))
            prog["value"] = int(n)
            pump()

        handle = {
            "setText": lambda t: (msg_var.set(str(t)), pump()),
            "setProgress": _set_progress,
            "close": lambda: (safe_close(root), None)[1],
            "_pump": pump,
            "_root": root,
        }

        def safe_close(r):
            try:
                r.grab_release()
            except Exception:
                pass
            try:
                r.destroy()
            except Exception:
                pass

        try:
            root.attributes("-topmost", True)
            root.focus_force()
            root.grab_set_global()
        except Exception:
            # Fallback to a window-local grab if global fails (some DEs).
            try:
                root.grab_set()
            except Exception:
                pass

        pump()
        return handle

    env.define("showWait", show_wait)


@register_native_lib("json")
def _lib_json(interp, env):
    """JSON encoding/decoding, backed by Python's json module.

    Lumen values map onto JSON directly: dicts <-> objects, lists <->
    arrays, strings/numbers/true/false/null <-> the same. Only those
    types can be encoded — class instances and functions can't.
    """
    import json as _json

    def parse(text):
        try:
            return _json.loads(str(text))
        except _json.JSONDecodeError as e:
            raise ValueError(f"invalid JSON: {e}") from None

    def stringify(value, indent=None):
        try:
            if indent is None or indent is False:
                return _json.dumps(value)
            return _json.dumps(value, indent=int(indent))
        except TypeError as e:
            raise TypeError(f"cannot convert to JSON: {e}") from None

    def stringify_pretty(value):
        return stringify(value, 2)

    def is_valid(text):
        try:
            _json.loads(str(text))
            return True
        except _json.JSONDecodeError:
            return False

    env.define("jsonParse", parse)
    env.define("jsonStringify", stringify)
    env.define("jsonStringifyPretty", stringify_pretty)
    env.define("jsonIsValid", is_valid)


@register_native_lib("re")
def _lib_re(interp, env):
    """Regular expressions, backed by Python's re module.

    Patterns use standard regex syntax (e.g. `\\d+`, `[a-z]+`, `^...$`).
    Since Lumen strings don't have a raw-string form, backslashes in
    patterns need escaping same as any other string: `"\\\\d+"` for `\\d+`.
    """
    import re as _re

    def _compiled(pattern):
        try:
            return _re.compile(str(pattern))
        except _re.error as e:
            raise ValueError(f"invalid regex '{pattern}': {e}") from None

    def test(pattern, s):
        return _compiled(pattern).search(str(s)) is not None

    def match(pattern, s):
        m = _compiled(pattern).search(str(s))
        return m.group(0) if m else None

    def find_all(pattern, s):
        return [m.group(0) for m in _compiled(pattern).finditer(str(s))]

    def groups(pattern, s):
        m = _compiled(pattern).search(str(s))
        if not m:
            return None
        return list(m.groups())

    def replace(pattern, s, repl):
        return _compiled(pattern).sub(str(repl), str(s))

    def replace_first(pattern, s, repl):
        return _compiled(pattern).sub(str(repl), str(s), count=1)

    def re_split(pattern, s):
        return _compiled(pattern).split(str(s))

    env.define("reTest", test)
    env.define("reMatch", match)
    env.define("reFindAll", find_all)
    env.define("reGroups", groups)
    env.define("reReplace", replace)
    env.define("reReplaceFirst", replace_first)
    env.define("reSplit", re_split)


@register_native_lib("datetime")
def _lib_datetime(interp, env):
    """Date/time formatting and arithmetic, backed by Python's datetime
    module. Times are represented as Unix timestamps (seconds since
    1970, the same numbers `clock()` from the `sys` library returns) so
    they're plain numbers you can store, compare, and do math on.
    """
    import time as _time
    import datetime as _dt

    def now():
        return _time.time()

    def format_time(ts, fmt="%Y-%m-%d %H:%M:%S"):
        return _dt.datetime.fromtimestamp(float(ts)).strftime(str(fmt))

    def now_string(fmt="%Y-%m-%d %H:%M:%S"):
        return format_time(now(), fmt)

    def today():
        return format_time(now(), "%Y-%m-%d")

    def parse_time(s, fmt="%Y-%m-%d %H:%M:%S"):
        dt = _dt.datetime.strptime(str(s), str(fmt))
        return dt.timestamp()

    def part(field):
        def getter(ts):
            dt = _dt.datetime.fromtimestamp(float(ts))
            return getattr(dt, field)
        return getter

    def weekday_name(ts):
        dt = _dt.datetime.fromtimestamp(float(ts))
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday"][dt.weekday()]

    def add_seconds(ts, secs):
        return float(ts) + float(secs)

    def add_days(ts, days):
        return float(ts) + float(days) * 86400

    env.define("now", now)
    env.define("nowString", now_string)
    env.define("today", today)
    env.define("formatTime", format_time)
    env.define("parseTime", parse_time)
    env.define("year", part("year"))
    env.define("month", part("month"))
    env.define("day", part("day"))
    env.define("hour", part("hour"))
    env.define("minute", part("minute"))
    env.define("second", part("second"))
    env.define("weekdayName", weekday_name)
    env.define("addSeconds", add_seconds)
    env.define("addDays", add_days)


@register_native_lib("format")
def _lib_format(interp, env):
    """Text/number formatting helpers that need precise Python behavior
    (float formatting, padding) rather than plain Lumen logic."""

    def to_fixed(x, digits=2):
        return f"{float(x):.{int(digits)}f}"

    def pad_start(s, width, ch=" "):
        return str(s).rjust(int(width), str(ch)[:1] or " ")

    def pad_end(s, width, ch=" "):
        return str(s).ljust(int(width), str(ch)[:1] or " ")

    def with_commas(x):
        return f"{x:,}" if isinstance(x, int) else f"{float(x):,.2f}"

    def zero_pad(n, width):
        return str(int(n)).rjust(int(width), "0")

    env.define("toFixed", to_fixed)
    env.define("padStart", pad_start)
    env.define("padEnd", pad_end)
    env.define("withCommas", with_commas)
    env.define("zeroPad", zero_pad)


@register_native_lib("file")
def _lib_file(interp, env):
    """File and directory operations.

    The text read/write functions intentionally operate on UTF-8 text.
    Recursive discovery and path helpers are backed by Python's os module.
    """

    def read_file(path):
        with open(str(path), "r", encoding="utf-8") as f:
            return f.read()

    def write_file(path, text):
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(str(text))
        return True

    def append_file(path, text):
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(str(text))
        return True

    def read_lines(path):
        with open(str(path), "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f.readlines()]

    def file_exists(path):
        return os.path.exists(str(path))

    def delete_file(path):
        os.remove(str(path))
        return True

    def make_dir(path):
        os.makedirs(str(path), exist_ok=True)
        return True

    def list_dir(path):
        return sorted(os.listdir(str(path)))

    def remove_dir(path):
        os.rmdir(str(path))
        return True

    def copy_file(src, dst):
        import shutil
        shutil.copy2(str(src), str(dst))
        return True

    def move_file(src, dst):
        import shutil
        shutil.move(str(src), str(dst))
        return True

    def rename_file(src, dst):
        os.rename(str(src), str(dst))
        return True

    def file_size(path):
        return os.path.getsize(str(path))

    def is_file(path):
        return os.path.isfile(str(path))

    def is_dir(path):
        return os.path.isdir(str(path))

    def base_name(path):
        return os.path.basename(str(path))

    def dir_name(path):
        return os.path.dirname(str(path))

    def join_path(a, b):
        return os.path.join(str(a), str(b))

    def abs_path(path):
        return os.path.abspath(str(path))

    def current_dir():
        return os.getcwd()

    def find_files(path, pattern="*"):
        import fnmatch

        root = os.path.abspath(str(path))
        results = []

        for current_root, dirs, files in os.walk(root):
            dirs.sort()
            files.sort()

            for filename in files:
                if fnmatch.fnmatch(filename, str(pattern)):
                    full = os.path.join(current_root, filename)
                    results.append(os.path.relpath(full, root))

        return sorted(results)

    def find_dirs(path, pattern="*"):
        import fnmatch

        root = os.path.abspath(str(path))
        results = []

        for current_root, dirs, files in os.walk(root):
            dirs.sort()

            for dirname in dirs:
                if fnmatch.fnmatch(dirname, str(pattern)):
                    full = os.path.join(current_root, dirname)
                    results.append(os.path.relpath(full, root))

        return sorted(results)

    def search_in_file(path, needle):
        """Lines in `path` containing `needle`, as {"line": n, "text": s}
        dicts (1-indexed, like most editors)."""
        matches = []
        with open(str(path), "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                if str(needle) in line:
                    matches.append({"line": i, "text": line.rstrip("\n")})
        return matches

    def search_in_files(dir_path, needle, pattern="*"):
        """search_in_file, applied to every file under `dir_path` whose
        name matches `pattern`. Returns {"file": ..., "line": ..., "text": ...}
        dicts, sorted by file path then line number."""
        import fnmatch

        root = os.path.abspath(str(dir_path))
        results = []
        for current_root, dirs, files in os.walk(root):
            dirs.sort()
            files.sort()
            for filename in files:
                if not fnmatch.fnmatch(filename, str(pattern)):
                    continue
                full = os.path.join(current_root, filename)
                try:
                    for m in search_in_file(full, needle):
                        results.append({
                            "file": os.path.relpath(full, root),
                            "line": m["line"],
                            "text": m["text"],
                        })
                except (UnicodeDecodeError, OSError):
                    continue
        return results

    env.define("readFile", read_file)
    env.define("writeFile", write_file)
    env.define("appendFile", append_file)
    env.define("readLines", read_lines)

    env.define("fileExists", file_exists)
    env.define("deleteFile", delete_file)

    env.define("makeDir", make_dir)
    env.define("listDir", list_dir)
    env.define("removeDir", remove_dir)

    env.define("copyFile", copy_file)
    env.define("moveFile", move_file)
    env.define("renameFile", rename_file)

    env.define("fileSize", file_size)
    env.define("isFile", is_file)
    env.define("isDir", is_dir)

    env.define("baseName", base_name)
    env.define("dirName", dir_name)
    env.define("joinPath", join_path)
    env.define("absPath", abs_path)
    env.define("currentDir", current_dir)

    env.define("findFiles", find_files)
    env.define("findDirs", find_dirs)

    env.define("searchInFile", search_in_file)
    env.define("searchInFiles", search_in_files)


@register_native_lib("subgame")
def _lib_subgame(interp, env):
    """
    A tiny game/graphics library, in the spirit of pygame but much smaller.
    Backed by Python's built-in tkinter, so it needs no extra installs.
    Opens a real window, draws shapes, and reads the keyboard.
    """
    import tkinter as tk

    state = {"root": None, "canvas": None, "keys": set(), "open": False}

    def window(width, height, title="Subgame"):
        root = tk.Tk()
        root.title(str(title))
        canvas = tk.Canvas(root, width=int(width), height=int(height), bg="white")
        canvas.pack()

        def on_key_press(event):
            state["keys"].add(event.keysym)

        def on_key_release(event):
            state["keys"].discard(event.keysym)

        def on_close():
            state["open"] = False
            root.destroy()

        root.bind("<KeyPress>", on_key_press)
        root.bind("<KeyRelease>", on_key_release)
        root.protocol("WM_DELETE_WINDOW", on_close)
        canvas.focus_set()

        state["root"] = root
        state["canvas"] = canvas
        state["open"] = True
        return None

    def clear():
        if state["canvas"] is not None:
            state["canvas"].delete("all")

    def rect(x, y, w, h, color="black"):
        if state["canvas"] is not None:
            state["canvas"].create_rectangle(x, y, x + w, y + h, fill=color, outline=color)

    def circle(x, y, r, color="black"):
        if state["canvas"] is not None:
            state["canvas"].create_oval(x - r, y - r, x + r, y + r, fill=color, outline=color)

    def line(x1, y1, x2, y2, color="black"):
        if state["canvas"] is not None:
            state["canvas"].create_line(x1, y1, x2, y2, fill=color)

    def text(x, y, s, color="black"):
        if state["canvas"] is not None:
            state["canvas"].create_text(x, y, text=s, fill=color)

    def update():
        if state["open"] and state["root"] is not None:
            try:
                state["root"].update()
            except tk.TclError:
                state["open"] = False

    def is_open():
        return bool(state["open"])

    def key_pressed(key):
        return key in state["keys"]

    def quit_():
        if state["root"] is not None:
            try:
                state["root"].destroy()
            except tk.TclError:
                pass
        state["open"] = False

    env.define("window", window)
    env.define("clear", clear)
    env.define("rect", rect)
    env.define("circle", circle)
    env.define("line", line)
    env.define("text", text)
    env.define("update", update)
    env.define("isOpen", is_open)
    env.define("keyPressed", key_pressed)
    env.define("quit", quit_)


def install_native_libs(interp):
    # Native libs are registered lazily via `import "name"` (see do_import),
    # this function exists so future eager-loading logic has a hook point.
    pass


# ----------------------------------------------------------------------
# 6. ENTRY POINT
# ----------------------------------------------------------------------

def do_get(names, dest_dir=None):
    """Downloads one or more `.lu` libraries from GITHUB_REPO into a local
    libs/ folder (or `dest_dir` if given). Uses only the standard library,
    so no extra installs are needed on the machine running this."""
    import urllib.request
    import urllib.error

    if GITHUB_REPO.startswith("YOUR-USERNAME"):
        print("GITHUB_REPO isn't set yet — edit the top of lumen.py and")
        print('set GITHUB_REPO = "your-username/your-repo" first.')
        sys.exit(1)

    lib_dir = dest_dir or os.path.join(os.getcwd(), "libs")
    os.makedirs(lib_dir, exist_ok=True)

    ok = True
    for name in names:
        url = library_url(name)
        dest = os.path.join(lib_dir, name + ".lu")
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = resp.read()
        except urllib.error.HTTPError as e:
            print(f"Could not download '{name}': {e.code} {e.reason} ({url})")
            ok = False
            continue
        except urllib.error.URLError as e:
            print(f"Could not download '{name}': {e.reason}")
            ok = False
            continue
        with open(dest, "wb") as f:
            f.write(data)
        print(f"Downloaded {name}.lu -> {dest}")
    if not ok:
        sys.exit(1)


def repl():
    """A minimal interactive REPL. Reads statements, buffering multi-line
    blocks until braces balance, and auto-prints bare expression results."""
    print("Lumen REPL — type 'exit' or Ctrl-D to quit")
    interp = Interpreter()
    buffer = ""
    while True:
        prompt = "... " if buffer else ">>> "
        try:
            line = input(prompt)
        except EOFError:
            print()
            break
        if not buffer and line.strip() in ("exit", "quit"):
            break
        buffer += line + "\n"
        if buffer.count("{") > buffer.count("}"):
            continue
        try:
            ast = parse(buffer)
            for stmt in ast[1]:
                if stmt[0] == "exprstmt":
                    val = interp.eval(stmt[1], interp.globals)
                    if val is not None:
                        print(to_display(val))
                else:
                    interp.exec_stmt(stmt, interp.globals)
        except Exception as e:
            print(f"Error: {e}")
        buffer = ""


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "get":
        if len(sys.argv) < 3:
            print("Usage: lumen get <library> [library ...]")
            print(f"Downloads .lu libraries from https://github.com/{GITHUB_REPO}")
            sys.exit(1)
        do_get(sys.argv[2:])
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "repl":
        repl()
        return
    if len(sys.argv) < 2:
        repl()
        return
    path = sys.argv[1]
    search_paths = sys.argv[2:]
    with open(path, encoding="utf-8") as f:
        source = f.read()
    interp = Interpreter(search_paths=search_paths)
    interp.run(source, filename=path)


if __name__ == "__main__":
    main()
