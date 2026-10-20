"""Small, deliberately lexical extractor for the pinned free-format COBOL slice.

This is not a compiler, copybook expander, complete grammar, or control-flow graph.
No executable business rules are inferred here. Source text is never copied into
the generated evidence index; identifiers, declarations and lexical references
are indexed, with hashes that can be verified against a separately fetched tree.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


LIMITATIONS = [
    "Free-format, UTF-8 COBOL only; fixed-format and continuation literals are unsupported.",
    "COPY references are indexed, not expanded; COPY REPLACING and compiler preprocessing are unsupported.",
    "Data hierarchy is lexical; REDEFINES, RENAMES, OCCURS storage and dialect-specific clauses are not evaluated.",
    "CALL/PERFORM references are lexical, not reachability, execution order, a complete CFG, or runtime proof.",
    "Dynamic CALL targets, inline PERFORM loops, fall-through, GO TO and exception flow are not resolved.",
    "Business semantics and regulatory mappings are reviewed annotations, not automatically inferred facts.",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal, absolute paths and symlinks escaping the source root."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"Invalid source path: {relative!r}")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Source path must stay inside the source tree: {relative}")
    root = root.resolve()
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Source path escapes the source tree: {relative}")
    return resolved


def permalink(repository: str, commit: str, path: str, start: int, end: int) -> str:
    if not repository.startswith("https://"):
        repository = "https://github.com/" + repository
    return f"{repository.rstrip('/')}/blob/{commit}/{quote(path, safe='/')}#L{start}-L{end}"


def evidence_ref(path: str, start: int, end: int, source: bytes, repository: str, commit: str) -> dict:
    # Preserve the exact original line terminators, including the final newline.
    excerpt = b"".join(source.splitlines(keepends=True)[start - 1:end])
    return {
        "path": path,
        "start_line": start,
        "end_line": end,
        "excerpt_sha256": digest(excerpt),
        "permalink": permalink(repository, commit, path, start, end),
    }


@dataclass(frozen=True)
class Token:
    value: str
    kind: str
    line: int


def lex_line(line: str, number: int) -> tuple[str, list[Token], bool]:
    """Strip *> comments only outside literals; preserve doubled quote escapes."""
    tokens: list[Token] = []
    i = 0
    while i < len(line):
        if line[i:i + 2] == "*>":
            return line[:i], tokens, False
        char = line[i]
        if char in "\"'":
            delimiter, start = char, i
            i += 1
            while i < len(line):
                if line[i] == delimiter:
                    if i + 1 < len(line) and line[i + 1] == delimiter:
                        i += 2
                        continue
                    i += 1
                    tokens.append(Token(line[start + 1:i - 1].replace(delimiter * 2, delimiter), "literal", number))
                    break
                i += 1
            else:
                return line, tokens, True
            continue
        match = re.match(r"[A-Za-z0-9][A-Za-z0-9-]*", line[i:])
        if match:
            value = match.group()
            tokens.append(Token(value.upper(), "word", number))
            i += len(value)
        else:
            if char == ".":
                tokens.append(Token(".", "punctuation", number))
            i += 1
    return line, tokens, False


def mask_literals(text: str) -> str:
    """Blank literals without changing offsets, for keyword/clause recognition."""
    result = list(text)
    i = 0
    while i < len(text):
        if text[i] not in "\"'":
            i += 1
            continue
        delimiter, start = text[i], i
        i += 1
        while i < len(text):
            if text[i] == delimiter:
                if i + 1 < len(text) and text[i + 1] == delimiter:
                    i += 2
                    continue
                i += 1
                break
            i += 1
        result[start:i] = " " * (i - start)
    return "".join(result)


DECLARATION = re.compile(r"^\s*(0[1-9]|[1-4][0-9]|66|77|78|88)\s+([A-Z][A-Z0-9-]*)\b", re.I)
CLAUSE_BOUNDARY = r"\s+(?:USAGE|COMP(?:-[0-9])?|BINARY|DISPLAY|OCCURS|REDEFINES|JUSTIFIED|SYNC(?:HRONIZED)?|SIGN|BLANK|EXTERNAL|GLOBAL)(?![\w-])"
NON_PARAGRAPHS = set("""
ACCEPT ADD ALTER CALL CANCEL CLOSE COMPUTE CONTINUE DELETE DISPLAY DIVIDE
ELSE END END-ACCEPT END-ADD END-CALL END-COMPUTE END-DELETE END-DISPLAY
END-DIVIDE END-EVALUATE END-IF END-MULTIPLY END-PERFORM END-READ END-RECEIVE
END-RETURN END-REWRITE END-SEARCH END-START END-STRING END-SUBTRACT END-UNSTRING
END-WRITE EVALUATE EXIT GOBACK GO IF INITIALIZE INSPECT MERGE MOVE MULTIPLY
OPEN PERFORM READ RELEASE RETURN REWRITE SEARCH SET SORT START STOP STRING
SUBTRACT UNSTRING WHEN WRITE
""".split())
INLINE_PERFORM = {"UNTIL", "VARYING", "WITH", "TEST", "TIMES", "FOREVER"}


def parse_source(path: str, source: bytes, repository: str, commit: str) -> dict:
    text = source.decode("utf-8")
    lines = text.splitlines()
    cleaned: list[str] = []
    all_tokens: list[Token] = []
    warnings: list[dict] = []
    for number, line in enumerate(lines, 1):
        if re.match(r"^\d{6}[ */-]", line):
            raise ValueError(f"{path}:{number}: fixed-format COBOL is unsupported")
        code, tokens, unclosed = lex_line(line, number)
        if unclosed:
            raise ValueError(f"{path}:{number}: unterminated or continued literal is unsupported")
        if re.search(r"\b(?:REPLACE|COPY\s+.*\bREPLACING)\b", " ".join(t.value for t in tokens if t.kind == "word")):
            warnings.append({"line": number, "code": "preprocessing-not-expanded"})
        cleaned.append(code)
        all_tokens.extend(tokens)

    def ref(start: int, end: int) -> dict:
        return evidence_ref(path, start, end, source, repository, commit)

    proc_line = next((i for i, line in enumerate(cleaned, 1) if re.match(r"\s*PROCEDURE\s+DIVISION\b", line, re.I)), len(lines) + 1)
    fields: list[dict] = []
    stack: list[dict] = []
    last_data: dict | None = None
    i = 0
    while i < min(proc_line - 1, len(cleaned)):
        match = DECLARATION.match(cleaned[i])
        if not match:
            i += 1
            continue
        start = i + 1
        chunks = [cleaned[i].strip()]
        while not chunks[-1].endswith(".") and i + 1 < proc_line - 1:
            next_line = cleaned[i + 1].strip()
            if DECLARATION.match(next_line) or re.match(r"(?:COPY\b|\w[\w-]*\s+(?:SECTION|DIVISION)\b)", next_line, re.I):
                break
            i += 1
            if next_line:
                chunks.append(next_line)
        declaration = " ".join(chunks)
        if declaration.endswith("."):
            declaration = declaration[:-1]
        masked = mask_literals(declaration)
        level, name = int(match.group(1)), match.group(2).upper()
        # 88 entries are predicates on the preceding item, never new storage.
        if level == 88:
            parent = last_data
            if parent is None:
                warnings.append({"line": start, "code": "orphan-condition-name"})
        elif level in (66, 77, 78):
            parent = None
            stack.clear()
        else:
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            parent = stack[-1] if stack else None
        picture = re.search(r"(?<![\w-])PIC(?:TURE)?\s+(?:IS\s+)?([^\s]+)", masked, re.I)
        value = re.search(r"(?<![\w-])VALUES?\s+(?:(?:IS|ARE)\s+)?", masked, re.I)
        value_text = None
        if value:
            # The whitespace in a blanked string is not part of the VALUE prefix.
            prefix = re.search(r"(?<![\w-])VALUES?\s+(?:(?:IS|ARE)\s+)?", declaration, re.I)
            start_value = prefix.end()
            boundary = re.search(CLAUSE_BOUNDARY, masked[start_value:], re.I)
            end_value = start_value + boundary.start() if boundary else len(declaration)
            value_text = declaration[start_value:end_value].strip()
        usage = re.search(r"(?<![\w-])(?:USAGE\s+(?:IS\s+)?)?(COMP(?:-[0-9])?|BINARY|DISPLAY|PACKED-DECIMAL)(?![\w-])", masked, re.I)
        occurs = re.search(r"(?<![\w-])OCCURS\s+(\d+)(?:\s+TO\s+(\d+))?(?:\s+TIMES)?(?:\s+DEPENDING\s+ON\s+([A-Z0-9-]+))?", masked, re.I)
        redefines = re.search(r"(?<![\w-])REDEFINES\s+([A-Z0-9-]+)", masked, re.I)
        kind = "condition" if level == 88 else "constant" if level == 78 else "field" if picture else "group"
        field = {
            "id": f"{path}:{start}:{name}", "name": name, "level": level, "kind": kind,
            "parent": parent["id"] if parent else None,
            "qualified_name": f"{parent['qualified_name']}.{name}" if parent else name,
            "picture": picture.group(1).upper() if picture else None,
            "value": value_text,
            "usage": usage.group(1).upper() if usage else None,
            "occurs": {"min": int(occurs.group(1)), "max": int(occurs.group(2) or occurs.group(1)), "depending_on": occurs.group(3)} if occurs else None,
            "redefines": redefines.group(1).upper() if redefines else None,
            "evidence": ref(start, i + 1),
        }
        if level == 66:
            warnings.append({"line": start, "code": "renames-not-resolved"})
        fields.append(field)
        if level != 88:
            last_data = field
            if level not in (66, 77, 78):
                stack.append(field)
        i += 1

    program_id = None
    for pos, token in enumerate(all_tokens):
        if token.kind == "word" and token.value == "PROGRAM-ID" and pos + 2 < len(all_tokens):
            if all_tokens[pos + 1].value == ".":
                program_id = all_tokens[pos + 2].value
                break

    paragraphs: list[dict] = []
    for number, line in enumerate(cleaned, 1):
        if number <= proc_line:
            continue
        match = re.fullmatch(r"\s*([A-Z0-9][A-Z0-9-]*)(?:\s+(SECTION))?\.\s*", line, re.I)
        if match and match.group(1).upper() not in NON_PARAGRAPHS:
            paragraphs.append({"name": match.group(1).upper(), "kind": "section" if match.group(2) else "paragraph", "start_line": number})
    for pos, para in enumerate(paragraphs):
        end = paragraphs[pos + 1]["start_line"] - 1 if pos + 1 < len(paragraphs) else len(lines)
        para["evidence"] = ref(para.pop("start_line"), end)
    para_names = {p["name"] for p in paragraphs}

    def enclosing(line: int) -> str:
        return next((p["name"] for p in reversed(paragraphs) if p["evidence"]["start_line"] <= line), "<entry>")

    copies: list[dict] = []
    edges: list[dict] = []
    for pos, token in enumerate(all_tokens[:-1]):
        if token.kind != "word":
            continue
        target = all_tokens[pos + 1]
        if token.value == "COPY" and token.line < proc_line and target.kind in {"word", "literal"}:
            copies.append({"name": target.value, "evidence": ref(token.line, target.line), "expanded": False})
        if token.line <= proc_line or token.value not in {"CALL", "PERFORM"}:
            continue
        if target.kind not in {"word", "literal"}:
            continue
        if token.value == "PERFORM" and (target.kind != "word" or target.value in INLINE_PERFORM or target.value[0].isdigit()):
            continue
        edge = {
            "kind": token.value.lower(), "from": enclosing(token.line), "target": target.value,
            "resolution": "literal-program" if token.value == "CALL" and target.kind == "literal" else "dynamic-unresolved" if token.value == "CALL" else "local-paragraph" if target.value in para_names else "unresolved-paragraph",
            "evidence": ref(token.line, target.line), "epistemic_status": "observed",
        }
        if token.value == "PERFORM" and pos + 3 < len(all_tokens) and all_tokens[pos + 2].value in {"THRU", "THROUGH"}:
            through = all_tokens[pos + 3]
            edge["through"] = through.value
            edge["evidence"] = ref(token.line, through.line)
        edges.append(edge)

    return {
        "path": path, "sha256": digest(source), "git_blob_sha": blob_sha(source),
        "line_count": len(lines), "program_id": program_id,
        "data_items": fields, "copy_references": copies, "paragraphs": paragraphs,
        "control_references": edges, "warnings": warnings,
    }


def verify_source(lock: dict, source_dir: Path) -> dict[str, bytes]:
    if lock.get("schema_version") != "1.0":
        raise ValueError("source-lock.json: expected schema_version '1.0'")
    repository, commit = lock.get("repository"), lock.get("commit")
    if not isinstance(repository, str) or not re.fullmatch(r"(?:https://github\.com/)?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("source-lock.json: repository must be a GitHub owner/repo or HTTPS URL")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("source-lock.json: commit must be a full 40-character SHA")
    files = lock.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("source-lock.json: nonempty files array required")
    contents = {}
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("source-lock.json: each file must be an object")
        path = item.get("path")
        local = safe_path(source_dir, path)
        if path in contents:
            raise ValueError(f"source-lock.json: duplicate path {path}")
        try:
            content = local.read_bytes()
        except OSError as exc:
            raise ValueError(f"Cannot read locked source {path}: {exc.strerror}") from exc
        if digest(content) != item.get("sha256"):
            raise ValueError(f"Source drift: SHA256 mismatch for {path}; fetch the exact locked commit")
        if blob_sha(content) != item.get("git_blob_sha"):
            raise ValueError(f"Source drift: Git blob SHA mismatch for {path}")
        contents[path] = content
    return contents


def extract(lock: dict, contents: dict[str, bytes]) -> dict:
    files = [parse_source(path, content, lock["repository"], lock["commit"]) for path, content in sorted(contents.items()) if Path(path).suffix.lower() in {".cob", ".cbl", ".cpy"}]
    return {
        "schema_version": "1.0", "source": {"repository": lock["repository"], "commit": lock["commit"]},
        "method": "lexical indexing; not compiled or executed", "limitations": LIMITATIONS, "files": files,
    }
