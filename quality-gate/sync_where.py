#!/usr/bin/env python3
"""
sync_where.py — parse a sync's `where { }` clause into a normalized form shared
by the spec and its Java implementation.

Why this exists:
  A `where` clause binds variables from action inputs/completions, reads concept
  state, guards, collects, and fans out. The spec documented this grammar
  (`templates/sync.md`, `SYNCHRONIZATIONS.md`) but nothing parsed it, so
  implementation parity could not compare binding provenance — a rule could
  change a binding's source and still pass (experiment finding 3). This module
  parses the *documented* grammar and the Java DSL into one normalized clause
  list, so the parity check can compare every clause and source.

Documented spec grammar (one clause per line, `//` or `#` comments):

    where {
        bind ( triggerInput("username") as ?u )
        bind ( uuid() as ?id )
        Counter: { ?u count: ?count }
        OPTIONAL { Comment: { ?post body: ?body } }
        BIND ( ?id AS ?_eachthen )
        fanOut ( ?loanId ; "Lending" ; "borrower" ; ?memberId )
        absent ( "Lending" ; ?loanId ; "returnedAt" )
        collect ( ?loanId as ?openLoans )
        collect distinct ( <source> as ?<var> )
        collect by ?groupKey ( <source> as ?<var> )
    }

`<expr>`/`<source>` is a DSL source factory (uuid, triggerInput, triggerField,
siblingInput, siblingField, conjunctInput, conjunctField, stateRead, subjects,
collect, distinct, scan, ref, lit) or a Pattern-D read `Concept: { ?id f: ?v }`.

Normalized clauses (the comparison key):
  bind ?x from <source>            (bind("?x", <source>))
  fanOut ?v Concept pred <object>  (fanOut("?v","Concept","pred",<object>))
  absent ?v Concept pred [<object>]
  collectBy ?v from <source> by ?k (collectBy("?v", <source>, "?k"))
  collectRecords ?r [..] by ?k
  optional ( ... )
  group ?x as ?y                   (BIND (?x AS ?y))
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

_SOURCE_FACTORIES = {
    "uuid", "triggerInput", "triggerField", "siblingInput", "siblingField",
    "conjunctInput", "conjunctField", "stateRead", "subjects", "collect",
    "distinct", "scan", "ref", "lit",
}

_TOKEN = re.compile(
    r"""
      (?P<ws>\s+)
    | (?P<string>"(?:\\.|[^"\\])*")
    | (?P<var>\?\w+)
    | (?P<ident>[A-Za-z_][A-Za-z0-9_./]*)
    | (?P<number>-?\d+(?:\.\d+)?)
    | (?P<punct>[()\[\],=*])
    """,
    re.VERBOSE,
)


class WhereParseError(ValueError):
    pass


@dataclass(frozen=True)
class Source:
    factory: str
    args: Tuple[object, ...]

    def sig(self) -> str:
        parts = [a.sig() if isinstance(a, Source) else str(a) for a in self.args]
        return f"{self.factory}({', '.join(parts)})"


@dataclass(frozen=True)
class Clause:
    kind: str
    fields: Tuple[str, ...]

    def sig(self) -> str:
        return (f"{self.kind} " + " ".join(self.fields)).strip()


# --------------------------------------------------------------------------
# Source expressions
# --------------------------------------------------------------------------

def _tokens(text: str):
    out, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise WhereParseError(f"unexpected character {text[pos]!r}")
        pos = m.end()
        if m.lastgroup == "ws":
            continue
        val = m.group()
        if m.lastgroup == "string":
            val = val[1:-1]
        out.append((m.lastgroup, val))
    return out


class _Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def take(self, kind=None, val=None):
        k, v = self.peek()
        if k is None:
            raise WhereParseError("unexpected end of source expression")
        if kind and k != kind:
            raise WhereParseError(f"expected {kind}, got {k} {v!r}")
        if val is not None and v != val:
            raise WhereParseError(f"expected {val!r}, got {v!r}")
        self.i += 1
        return v

    def accept(self, kind=None, val=None):
        k, v = self.peek()
        if (kind is None or k == kind) and (val is None or v == val):
            self.i += 1
            return True
        return False

    def source(self) -> Source:
        k, name = self.peek()
        if k != "ident" or name not in _SOURCE_FACTORIES:
            raise WhereParseError(f"expected a source factory, got {k} {name!r}")
        self.take("ident")
        self.take("punct", "(")
        args: List[object] = []
        if not self.accept("punct", ")"):
            while True:
                args.append(self.arg())
                if self.accept("punct", ","):
                    continue
                self.take("punct", ")")
                break
        return _canon_source(Source(name, tuple(args)))

    def arg(self) -> object:
        k, v = self.peek()
        if k == "ident":
            if self.i + 1 < len(self.toks) and self.toks[self.i + 1] == ("punct", "("):
                return self.source()
            self.take("ident")
            return v
        if k in ("string", "var", "number"):
            self.take(k)
            return v
        raise WhereParseError(f"unexpected argument token {k} {v!r}")


def _canon_source(src: Source) -> Source:
    args: List[object] = []
    for a in src.args:
        if isinstance(a, Source):
            args.append(_canon_source(a))
        elif isinstance(a, str) and a.startswith("?") and src.factory != "ref":
            args.append(Source("ref", (a,)))
        else:
            args.append(a)
    if src.factory in ("siblingInput", "siblingField") and args \
            and isinstance(args[0], str) and "/" in args[0]:
        concept, action = args[0].split("/", 1)
        args = [concept, action] + args[1:]
    return Source(src.factory, tuple(args))


def _source_sig(text: str, symbols=None) -> str:
    text = text.strip()
    if text.startswith("<") and text.endswith(">"):
        return text  # generator placeholder, e.g. <source>
    if text.startswith("?"):
        return Source("ref", (text,)).sig()
    if re.fullmatch(r'"[^"]*"|-?\d+(?:\.\d+)?|[A-Za-z_]\w*', text):
        return _unquote(text)
    if _PATTERN_D.match(text):
        return _as_source(text).sig()
    p = _Parser(_tokens(text))
    src = p.source()
    if p.i != len(p.toks):
        raise WhereParseError(f"trailing tokens after source: {text!r}")
    if symbols:
        src = _resolve(src, symbols)
    return src.sig()


def _resolve(src: Source, symbols) -> Source:
    args = []
    for a in src.args:
        if isinstance(a, Source):
            args.append(_resolve(a, symbols))
        elif isinstance(a, str) and a in symbols:
            args.append(symbols[a])
        else:
            args.append(a)
    return Source(src.factory, tuple(args))


# --------------------------------------------------------------------------
# Spec grammar
# --------------------------------------------------------------------------

_PATTERN_D = re.compile(r"^(\w+)\s*:\s*\{(.*)\}$", re.DOTALL)
_BIND = re.compile(r"^bind\s*\((.*)\)$", re.DOTALL)
_COLLECT = re.compile(
    r"^collect(?:\s+(distinct)|(?:\s+by\s+(\?\w+)))?\s*\((.*)\)$", re.DOTALL)
_FANOUT = re.compile(r"^fanOut\s*\((.*)\)$", re.DOTALL)
_ABSENT = re.compile(r"^absent\s*\((.*)\)$", re.DOTALL)
_BINDGROUP = re.compile(r"^BIND\s*\(\s*(\?\w+)\s+AS\s+(\?\w+)\s*\)$", re.DOTALL)


def _split_as(inner: str) -> Tuple[str, str]:
    """Split `<expr> as ?var` on the top-level ` as `."""
    depth, in_str, i = 0, False, 0
    while i < len(inner):
        ch = inner[i]
        if in_str:
            if ch == '"' and inner[i - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif depth == 0 and inner[i:i + 4] == " as ":
            return inner[:i].strip(), inner[i + 4:].strip()
        i += 1
    raise WhereParseError(f"expected `<expr> as ?var`, got {inner!r}")


def _split_semis(inner: str) -> List[str]:
    parts, depth, cur, in_str = [], 0, [], False
    for i, ch in enumerate(inner):
        if in_str:
            cur.append(ch)
            if ch == '"' and inner[i - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == ";" and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def _pattern_d_clauses(inner: str, concept: str) -> List[Clause]:
    """`?id field: ?v ; field2: ?w` -> a bind-from-stateRead per field."""
    parts = _split_semis(inner)
    if not parts:
        return []
    head = parts[0]
    m = re.match(r"^(\?\w+)\s*(.*)$", head)
    if not m:
        raise WhereParseError(f"Pattern-D read missing subject: {head!r}")
    subject, rest = m.group(1), m.group(2)
    bindings = ([rest] if rest else []) + parts[1:]
    clauses = []
    for b in bindings:
        fm = re.match(r"^(\w+)\s*:\s*(\?\w+)$", b)
        if not fm:
            raise WhereParseError(f"Pattern-D binding must be `field: ?var`: {b!r}")
        clauses.append(Clause("bind", (
            fm.group(2), Source("stateRead", (
                concept, Source("ref", (subject,)), fm.group(1))).sig())))
    return clauses


def _clause_line(text: str) -> List[Clause]:
    m = _BIND.match(text)
    if m:
        expr, var = _split_as(m.group(1))
        if not var.startswith("?"):
            raise WhereParseError(f"`bind (... as ?var)` needs a ?var, got {var!r}")
        return [Clause("bind", (var, _source_sig(expr)))]
    m = _COLLECT.match(text)
    if m:
        distinct, by, inner = m.group(1), m.group(2), m.group(3)
        src_text, var = _split_as(inner)
        if not var.startswith("?"):
            raise WhereParseError(f"collect target must be a ?var, got {var!r}")
        if by:
            return [Clause("collectBy", (var, _source_sig(src_text), by))]
        wrapped = ("distinct" if distinct else "collect")
        return [Clause("bind", (var, Source(wrapped, (
            _as_source(src_text),)).sig()))]
    m = _FANOUT.match(text)
    if m:
        parts = _split_semis(m.group(1))
        if len(parts) != 4:
            raise WhereParseError("fanOut needs `?var ; \"Concept\" ; \"pred\" ; ?obj`")
        return [Clause("fanOut", (
            _var(parts[0]), _unquote(parts[1]), _unquote(parts[2]),
            _source_sig(parts[3])))]
    m = _ABSENT.match(text)
    if m:
        parts = _split_semis(m.group(1))
        if len(parts) not in (3, 4):
            raise WhereParseError(
                "absent needs `\"Concept\" ; ?var ; \"pred\" [ ; ?obj ]`")
        obj = _source_sig(parts[3]) if len(parts) == 4 else ""
        return [Clause("absent", (
            _var(parts[1]), _unquote(parts[0]), _unquote(parts[2]), obj))]
    m = _BINDGROUP.match(text)
    if m:
        return [Clause("group", (m.group(1), m.group(2)))]
    m = _PATTERN_D.match(text)
    if m:
        return _pattern_d_clauses(m.group(2), m.group(1))
    raise WhereParseError(f"unrecognized where clause: {text!r}")


def _as_source(text: str) -> Source:
    text = text.strip()
    if text.startswith("?"):
        return Source("ref", (text,))
    if text.startswith("<") and text.endswith(">"):
        return Source("ref", (text,))
    m = _PATTERN_D.match(text)
    if m:
        # A Pattern-D read used as a collect source: the field it yields.
        parts = _split_semis(m.group(2))
        head = re.match(r"^(\?\w+)\s*(\w+)\s*:\s*(\?\w+)$", parts[0].strip())
        if not head:
            raise WhereParseError(f"unsupported Pattern-D collect source: {text!r}")
        return Source("stateRead", (m.group(1), Source("ref", (head.group(1),)),
                                    head.group(2)))
    p = _Parser(_tokens(text))
    return p.source()


def _var(tok: str) -> str:
    tok = tok.strip()
    if not tok.startswith("?"):
        raise WhereParseError(f"expected a ?variable, got {tok!r}")
    return tok


def _unquote(tok: str) -> str:
    tok = tok.strip()
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return tok[1:-1]
    return tok


def parse_spec_where(block_text: str) -> List[Clause]:
    """Parse the body of a spec `where { ... }` block into normalized clauses."""
    clauses: List[Clause] = []
    lines = block_text.split("\n")
    i = 0
    while i < len(lines):
        raw = _strip_comment(lines[i]).strip()
        i += 1
        if not raw:
            continue
        if re.match(r"^OPTIONAL\b", raw, re.IGNORECASE):
            # Gather the balanced `{ ... }` body, possibly spanning lines.
            body = raw[raw.index("{"):] if "{" in raw else ""
            depth = body.count("{") - body.count("}")
            while depth > 0 and i < len(lines):
                nxt = _strip_comment(lines[i]).strip()
                i += 1
                body += "\n" + nxt
                depth += nxt.count("{") - nxt.count("}")
            inner = body[1:body.rindex("}")] if "{" in body and "}" in body else body
            sub = parse_spec_where(inner)
            clauses.append(Clause("optional",
                                  ("(" + " ; ".join(c.sig() for c in sub) + ")",)))
            continue
        clauses.extend(_clause_line(raw))
    return clauses


def _strip_comment(line: str) -> str:
    # Remove `//` and `#` comments that are not inside a string.
    out, in_str = [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_str:
            out.append(ch)
            if ch == '"' and line[i - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
            out.append(ch)
        elif ch == "#":
            break
        elif ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out)


# --------------------------------------------------------------------------
# Java DSL
# --------------------------------------------------------------------------

def _split_top_level(text: str) -> List[str]:
    parts, depth, cur, in_str = [], 0, [], False
    for i, ch in enumerate(text):
        if in_str:
            cur.append(ch)
            if ch == '"' and text[i - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def _java_clause(text: str, symbols=None) -> Optional[Clause]:
    m = re.match(r"^(\w+)\s*\((.*)\)$", text.strip(), re.DOTALL)
    if not m:
        return None
    kw, body = m.group(1), m.group(2)
    args = _split_top_level(body)
    if kw == "bind" and len(args) == 2:
        return Clause("bind", (_var(_unquote(args[0])),
                               _source_sig(args[1], symbols)))
    if kw == "guard" and len(args) == 2:
        return Clause("guard", (_var(_unquote(args[0])),
                                _source_sig(args[1], symbols)))
    if kw == "absent" and len(args) in (3, 4):
        obj = _source_sig(args[3], symbols) if len(args) == 4 else ""
        return Clause("absent", (_var(_unquote(args[0])), _unquote(args[1]),
                                 _unquote(args[2]), obj))
    if kw == "fanOut" and len(args) == 4:
        return Clause("fanOut", (_var(_unquote(args[0])), _unquote(args[1]),
                                 _unquote(args[2]), _source_sig(args[3], symbols)))
    if kw == "collectBy" and len(args) == 3:
        group = "*" if args[2].strip() in ("null", "*") else _var(_unquote(args[2]))
        return Clause("collectBy", (_var(_unquote(args[0])),
                                    _source_sig(args[1], symbols), group))
    if kw in ("collectRecords", "collectRecordsBy") and len(args) >= 2:
        vars_ = re.findall(r'"(\?\w+)"', args[1])
        group = "*"
        if kw == "collectRecordsBy" and len(args) > 2:
            group = "*" if args[2].strip() in ("null", "*") else _var(_unquote(args[2]))
        return Clause("collectRecords", (_var(_unquote(args[0])),
                                         "[" + ", ".join(vars_) + "]", group))
    if kw == "optional" and len(args) == 1:
        inner = _java_clause(args[0], symbols)
        if inner is not None:
            return Clause("optional", ("(" + inner.sig() + ")",))
    return None


def parse_java_where(where_body: str, symbols=None) -> List[Clause]:
    """Parse the argument list of a `.where(...)` call into normalized clauses."""
    clauses = []
    for part in _split_top_level(where_body):
        clause = _java_clause(part, symbols)
        if clause is not None:
            clauses.append(clause)
    return clauses


def extract_java_where(rule_body: str) -> str:
    """The text inside the first `.where(...)` call in a Java rule body."""
    m = re.search(r"\.where\s*\(", rule_body)
    if not m:
        return ""
    start = m.end()
    depth, in_str, i = 1, False, start
    while i < len(rule_body):
        ch = rule_body[i]
        if in_str:
            if ch == '"' and rule_body[i - 1] != "\\":
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return rule_body[start:i]
        i += 1
    return ""


def extract_where_block(text: str) -> str:
    """The body of the first `where { ... }` block, or '' when absent."""
    m = re.search(r"\bwhere\s*\{", text)
    if not m:
        return ""
    start, depth, i = m.end(), 1, m.end()
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
        i += 1
    return ""


def spec_where_clauses(text: str):
    """Parsed clauses of a spec's `where { ... }` block, or None when absent."""
    block = extract_where_block(text)
    if not block.strip():
        return None
    return parse_spec_where(block)


def clause_signatures(clauses: List[Clause]) -> List[str]:
    return sorted(c.sig() for c in clauses)
