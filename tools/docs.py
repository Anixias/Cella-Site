import argparse
import concurrent.futures
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import threading

SITE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = SITE / "docs" / "src"
OUTPUT = SITE / "docs"
CACHE = SITE / "tools" / ".cache"
CACHE_VERSION = "4"

DEFAULT_PROJECT = 'OutputType = "Executable"\nSystemLinkPreference = "Dynamic"\n'

RESERVED = {
    "true", "false", "null", "undef", "sizeOf", "alignOf", "nameOf", "ret", "var", "val", "const", "if", "else",
    "for", "in", "loop", "while", "do", "break", "cont", "match", "is", "mut", "own", "imm", "self", "fun", "dyn",
    "atomic", "when", "new", "default", "drop", "panic", "ref",
}

CONTEXTUAL = {
    "mod", "use", "pub", "ext", "rec", "enum", "union", "op", "req", "pvt", "set", "get", "prop", "noref", "copy",
    "trait", "impl", "as",
}

TOKEN_KINDS = ["type", "struct", "enum", "interface", "typeParameter", "function", "method", "parameter", "variable",
               "property", "enumMember", "keyword", "namespace"]

MODIFIERS = ["declaration", "readonly", "static", "drop", "ref", "defaultLibrary"]

INTEGER_SUFFIX = r"(?:[iu](?:8|16|32|64|128|size)|f32|f64|u)?"
NUMBER = re.compile(
    r"0[xX][0-9a-fA-F_]+" + INTEGER_SUFFIX + r"|0[bB][01_]+" + INTEGER_SUFFIX + r"|0[oO][0-7_]+" + INTEGER_SUFFIX +
    r"|[0-9][0-9_]*(?:\.[0-9][0-9_]*)?(?:[eE][+-]?[0-9]+)?" + INTEGER_SUFFIX)
IDENTIFIER = re.compile(r"[^\W\d]\w*")
SUFFIX = re.compile(r"(?:[iu](?:8|16|32|64|128|size))")


class BuildError(Exception):
    pass


def compiler_paths(repo, version):
    if repo:
        base = pathlib.Path(repo) / "src" / "csharp"
        compiler = base / "Cella.Compiler" / "bin" / "Debug" / "net10.0" / "win-x64" / "cella.exe"
        server = base / "Cella.LanguageServer" / "bin" / "Debug" / "net10.0" / "win-x64" / "cella-lsp.exe"
        label = (pathlib.Path(repo) / "version.txt").read_text().strip()
    else:
        home = pathlib.Path(os.environ.get("CELLA_HOME") or ("C:\\cella" if os.name == "nt" else "~/.cella"))
        home = home.expanduser()
        versions = [path for path in home.iterdir() if (path / "cella.exe").exists()] if home.exists() else []
        if version:
            versions = [path for path in versions if path.name == version]
        if not versions:
            raise BuildError(f"No installed Cella version in {home}; install one or pass --cella <repo>")
        installed = max(versions, key=lambda path: (path / "cella.exe").stat().st_mtime)
        compiler, server, label = installed / "cella.exe", installed / "cella-lsp.exe", installed.name
    for path in (compiler, server):
        if not path.exists():
            raise BuildError(f"Missing {path}")
    return compiler, server, label


def tool_stamp(compiler, server):
    digest = hashlib.sha256()
    for directory in (compiler.parent, server.parent):
        for name in ("Cella.Core.dll", "cella.dll", "cella-lsp.dll"):
            path = directory / name
            if path.exists():
                digest.update(name.encode())
                digest.update(str(path.stat().st_mtime_ns).encode())
    library = compiler.parent / "lib"
    for path in sorted(library.rglob("*")) if library.exists() else []:
        if path.is_file() and not {"bin", "obj"} & set(path.relative_to(library).parts):
            digest.update(str(path.relative_to(library)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


# ---------------------------------------------------------------- examples

class Example:
    def __init__(self, chapter, key):
        self.chapter = chapter
        self.key = key
        self.files = {}
        self.order = []
        self.project = None
        self.expects_error = False
        self.compile_only = False
        self.expected_output = None
        self.expected_errors = None
        self.result = None
        self.args = []
        self.options = []
        self.line = 0

    def add_file(self, name, text):
        if name in self.files:
            raise BuildError(f"{self.chapter}: example '{self.key}' declares {name} twice")
        self.files[name] = text
        self.order.append(name)

    def digest(self, stamp):
        content = json.dumps([CACHE_VERSION, stamp, self.project or DEFAULT_PROJECT, self.files, self.args, self.options],
                             sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:24]


def strip_hidden(text):
    shown, compiled = [], []
    for line in text.split("\n"):
        if line == "~" or line.startswith("~ ") or line.startswith("~\t"):
            compiled.append(line[2:] if len(line) > 1 else "")
            shown.append(None)
        else:
            compiled.append(line)
            shown.append(line)
    return "\n".join(compiled), shown


def run_example(example, compiler, stamp):
    key = example.digest(stamp)
    directory = CACHE / key
    result_path = directory / "result.json"
    if result_path.exists():
        example.result = json.loads(result_path.read_text(encoding="utf-8"))
        example.result["directory"] = str(directory)
        return
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    (directory / "test.celp").write_text(example.project or DEFAULT_PROJECT, encoding="utf-8")
    for name, text in example.files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    build = subprocess.run([str(compiler), "build", "test.celp", "--hints", *example.options], cwd=directory, capture_output=True, timeout=300)
    compile_output = (build.stdout + build.stderr).decode("utf-8", "replace").replace("\r\n", "\n")
    result = {"compileExit": build.returncode, "compileOutput": compile_output, "runOutput": None, "runExit": None}
    if build.returncode == 0 and not example.compile_only and not example.expects_error:
        programs = list((directory / "bin").glob("*.exe"))
        if programs:
            run = subprocess.run([str(programs[0]), *example.args], cwd=directory, capture_output=True, timeout=60)
            result["runOutput"] = (run.stdout + run.stderr).decode("utf-8", "replace").replace("\r\n", "\n")
            result["runExit"] = run.returncode
    result_path.write_text(json.dumps(result), encoding="utf-8")
    result["directory"] = str(directory)
    example.result = result


DIAGNOSTIC = re.compile(r"^(Error|Warning|Hint) at (.+?):(\d+):(\d+)$")


def parse_diagnostics(output):
    diagnostics = []
    lines = output.split("\n")
    i = 0
    while i < len(lines):
        match = DIAGNOSTIC.match(lines[i])
        if not match:
            i += 1
            continue
        severity, file, line, column = match.group(1), match.group(2), int(match.group(3)), int(match.group(4))
        message, notes, length = "", [], 1
        i += 1
        while i < len(lines) and lines[i].strip() and not DIAGNOSTIC.match(lines[i]):
            text = lines[i]
            if "╘" in text and not message:
                start = text.index("╘")
                end = text.index("╛", start) if "╛" in text[start:] else start
                length = end - start + 1
                message = text[end + 1:].strip()
            elif re.match(r"^\s*\^ ", text) and not message:
                message = text[text.index("^") + 1:].strip()
            elif message and text.strip().startswith("|"):
                notes.append(text.strip()[1:].strip())
            elif not message and not re.match(r"^\s*\d+ │", text) and text.strip():
                message = text.strip()
            i += 1
        diagnostics.append({"severity": severity.lower(), "file": file.replace("\\", "/"), "line": line,
                            "column": column, "length": length, "message": message, "notes": notes})
    return diagnostics


def check_example(example):
    problems = []
    result = example.result
    diagnostics = parse_diagnostics(result["compileOutput"])
    result["diagnostics"] = diagnostics
    errors = [d for d in diagnostics if d["severity"] == "error"]
    where = f"{example.chapter}:{example.line}"
    if example.expects_error:
        if result["compileExit"] == 0:
            problems.append(f"{where}: expected a compile error, but it compiled")
        expected = example.expected_errors or []
        actual = [d["message"] for d in errors]
        if len(expected) != len(actual) or any(e not in a for e, a in zip(expected, actual)):
            problems.append(f"{where}: errors differ\n  expected: {expected}\n  actual:   {actual}")
    else:
        if result["compileExit"] != 0:
            detail = result["compileOutput"].strip()
            problems.append(f"{where}: compilation failed\n{detail}")
        warnings = [d for d in diagnostics if d["severity"] != "error"]
        for warning in warnings:
            problems.append(f"{where}: {warning['severity']} at {warning['line']}:{warning['column']}: "
                            f"{warning['message']}")
        if example.expected_output is not None and not example.compile_only:
            actual = (result["runOutput"] or "").rstrip("\n")
            expected = example.expected_output.rstrip("\n")
            if actual != expected:
                problems.append(f"{where}: output differs\n--- expected\n{expected}\n--- actual\n{actual}")
        elif example.expected_output is None and not example.compile_only and result["runOutput"]:
            problems.append(f"{where}: program printed output but the example has no output block:\n"
                            f"{result['runOutput'].rstrip()}")
    return problems


# ---------------------------------------------------------------- semantic tokens

class LanguageServer:
    def __init__(self, path, roots):
        self.process = subprocess.Popen([str(path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL)
        self.counter = 0
        self.responses = {}
        self.condition = threading.Condition()
        threading.Thread(target=self.read, daemon=True).start()
        folders = [{"uri": pathlib.Path(root).as_uri(), "name": pathlib.Path(root).name} for root in roots]
        self.request("initialize", {"processId": None, "rootUri": None, "workspaceFolders": folders,
                                    "capabilities": {}})
        self.notify("initialized", {})

    def read(self):
        stream = self.process.stdout
        while True:
            headers = {}
            while True:
                line = stream.readline()
                if not line:
                    with self.condition:
                        self.responses[None] = True
                        self.condition.notify_all()
                    return
                line = line.decode().strip()
                if not line:
                    break
                name, value = line.split(":", 1)
                headers[name.lower()] = value.strip()
            body = json.loads(stream.read(int(headers["content-length"])))
            if "id" in body and "method" not in body:
                with self.condition:
                    self.responses[body["id"]] = body
                    self.condition.notify_all()
            elif "id" in body:
                self.send({"jsonrpc": "2.0", "id": body["id"], "result": None})

    def send(self, message):
        data = json.dumps(message).encode()
        self.process.stdin.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
        self.process.stdin.flush()

    def notify(self, method, parameters):
        self.send({"jsonrpc": "2.0", "method": method, "params": parameters})

    def request(self, method, parameters):
        self.counter += 1
        identifier = self.counter
        self.send({"jsonrpc": "2.0", "id": identifier, "method": method, "params": parameters})
        with self.condition:
            while identifier not in self.responses:
                if None in self.responses:
                    raise BuildError("The language server stopped")
                self.condition.wait(120)
            return self.responses.pop(identifier)

    def close(self):
        try:
            self.request("shutdown", None)
            self.notify("exit", None)
        except (BuildError, OSError):
            pass
        self.process.kill()


def decode_tokens(data):
    tokens = []
    line = character = 0
    for i in range(0, len(data), 5):
        delta_line, delta_character, length, kind, modifiers = data[i:i + 5]
        line += delta_line
        character = character + delta_character if delta_line == 0 else delta_character
        names = [MODIFIERS[bit] for bit in range(len(MODIFIERS)) if modifiers & (1 << bit)]
        tokens.append((line, character, length, TOKEN_KINDS[kind], names))
    return tokens


def collect_tokens(examples, server_path):
    pending = []
    for example in examples:
        path = pathlib.Path(example.result["directory"]) / "tokens.json"
        if path.exists():
            example.result["tokens"] = json.loads(path.read_text(encoding="utf-8"))
        else:
            pending.append(example)
    for start in range(0, len(pending), 40):
        batch = pending[start:start + 40]
        server = LanguageServer(server_path, [example.result["directory"] for example in batch])
        try:
            for example in batch:
                for name in example.order:
                    path = pathlib.Path(example.result["directory"]) / name
                    server.notify("textDocument/didOpen", {"textDocument": {
                        "uri": path.as_uri(), "languageId": "cella", "version": 1,
                        "text": example.files[name]}})
            for example in batch:
                tokens = {}
                for name in example.order:
                    path = pathlib.Path(example.result["directory"]) / name
                    response = server.request("textDocument/semanticTokens/full",
                                              {"textDocument": {"uri": path.as_uri()}})
                    data = (response.get("result") or {}).get("data", [])
                    tokens[name] = decode_tokens(data)
                example.result["tokens"] = tokens
                (pathlib.Path(example.result["directory"]) / "tokens.json").write_text(json.dumps(tokens),
                                                                                       encoding="utf-8")
        finally:
            server.close()


# ---------------------------------------------------------------- highlighting

def lex(text, classes, start=0, end=None, stop_at_brace=False):
    end = len(text) if end is None else end
    i = start
    depth = 0
    while i < end:
        c = text[i]
        if c == "\n" or c in " \t\r":
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = end if j < 0 else j
            mark(classes, i, j, "comment")
            i = j
        elif text.startswith("/*", i):
            level, j = 0, i
            while j < end:
                if text.startswith("/*", j):
                    level += 1
                    j += 2
                elif text.startswith("*/", j):
                    level -= 1
                    j += 2
                    if level == 0:
                        break
                else:
                    j += 1
            mark(classes, i, j, "comment")
            i = j
        elif c == '"':
            i = lex_string(text, classes, i, end)
        elif c == "'":
            j = i + 1
            while j < end and text[j] != "'" and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            j = min(j + 1, end)
            suffix = SUFFIX.match(text, j)
            if suffix:
                j = suffix.end()
            mark(classes, i, j, "literal")
            i = j
        elif c.isdigit():
            match = NUMBER.match(text, i)
            j = match.end()
            if text.startswith("..", j - 1) and "." in text[i:j] and not text.startswith("...", j - 1):
                j = text.index(".", i)
            mark(classes, i, j, "literal")
            i = j
        elif c.isalpha() or c == "_":
            match = IDENTIFIER.match(text, i)
            word = match.group(0)
            if word in RESERVED:
                mark(classes, i, match.end(), "keyword")
            i = match.end()
        elif stop_at_brace and c == "{":
            depth += 1
            i += 1
        elif stop_at_brace and c == "}":
            if depth == 0:
                return i
            depth -= 1
            i += 1
        elif stop_at_brace and c == ":" and depth == 0:
            close = text.find("}", i)
            if close < 0:
                return end
            mark(classes, i, close, "literal")
            return close
        else:
            i += 1
    return i


def lex_string(text, classes, start, end):
    i = start + 1
    segment = start
    while i < end and text[i] != "\n":
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            i += 1
            suffix = SUFFIX.match(text, i)
            if suffix:
                i = suffix.end()
            mark(classes, segment, i, "literal")
            return i
        if c == "{":
            mark(classes, segment, i + 1, "literal")
            close = lex(text, classes, i + 1, end, stop_at_brace=True)
            i = close
            segment = close
            continue
        i += 1
    mark(classes, segment, i, "literal")
    return i


def mark(classes, start, end, name):
    for k in range(start, min(end, len(classes))):
        classes[k] = name


def semantic_class(kind, modifiers):
    if kind == "keyword":
        return "type" if "defaultLibrary" in modifiers else "keyword"
    if kind in ("struct", "enum", "type"):
        return "type"
    if kind == "interface":
        return "trait"
    if kind == "typeParameter":
        return "typeparam"
    if kind in ("function", "method"):
        return "function"
    if kind == "enumMember":
        return "case"
    if kind == "parameter":
        return "parameter"
    if kind == "namespace":
        return "module"
    if kind == "property":
        return "field"
    if kind == "variable":
        return "constant" if "static" in modifiers and "readonly" in modifiers else "variable"
    return None


def highlight(text, tokens):
    classes = [None] * len(text)
    lex(text, classes)
    starts = [0]
    for k, c in enumerate(text):
        if c == "\n":
            starts.append(k + 1)
    for line, character, length, kind, modifiers in tokens:
        if line >= len(starts):
            continue
        offset = starts[line] + character
        name = semantic_class(kind, modifiers)
        if name and all(classes[k] != "comment" for k in range(offset, min(offset + length, len(text)))):
            mark(classes, offset, offset + length, name)
    lines, current, line_classes = [], [], []
    for k, c in enumerate(text + "\n"):
        if c == "\n":
            lines.append(render_runs(current, line_classes))
            current, line_classes = [], []
        else:
            current.append(c)
            line_classes.append(classes[k] if k < len(classes) else None)
    return lines


def render_runs(chars, classes):
    out = []
    k = 0
    while k < len(chars):
        name = classes[k]
        j = k
        while j < len(chars) and classes[j] == name:
            j += 1
        piece = html.escape("".join(chars[k:j]), quote=False)
        out.append(f'<span class="c-{name}">{piece}</span>' if name and name != "variable" else piece)
        k = j
    return "".join(out)


def highlight_toml(text):
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            lines.append(f'<span class="c-comment">{html.escape(line, quote=False)}</span>')
        elif stripped.startswith("["):
            lines.append(f'<span class="c-type">{html.escape(line, quote=False)}</span>')
        elif "=" in line:
            key, value = line.split("=", 1)
            lines.append(f'<span class="c-field">{html.escape(key, quote=False)}</span>='
                         f'{toml_value(value)}')
        else:
            lines.append(html.escape(line, quote=False))
    return lines


def toml_value(value):
    out = []
    for piece in re.split(r"(\"[^\"]*\"|'[^']*'|\btrue\b|\bfalse\b|\b\d+\b)", value):
        if not piece:
            continue
        escaped = html.escape(piece, quote=False)
        out.append(f'<span class="c-literal">{escaped}</span>' if re.match(r"[\"'\d]|true|false", piece)
                   else escaped)
    return "".join(out)


def visual_column(line, column):
    width = 0
    for c in line[:column - 1]:
        width = (width // 4 + 1) * 4 if c == "\t" else width + 1
    return width


# ---------------------------------------------------------------- markdown

def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    return re.sub(r"[ _]+", "-", text).strip("-") or "section"


def inline(text):
    parts = re.split(r"(`+)(.+?)\1", text)
    out = []
    k = 0
    while k < len(parts):
        if k % 3 == 0:
            out.append(inline_text(parts[k]))
            k += 1
        else:
            out.append(f"<code>{html.escape(parts[k + 1], quote=False)}</code>")
            k += 2
    return "".join(out)


def inline_text(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)

    def link(match):
        label, target = match.group(1), match.group(2)
        if not re.match(r"[a-z]+:", target):
            target = re.sub(r"\.md(#|$)", r".html\1", target)
            if target.startswith("introduction.html"):
                target = "index.html" + target[len("introduction.html"):]
        external = ' target="_blank" rel="noopener"' if target.startswith("http") else ""
        return f'<a href="{target}"{external}>{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)


class Page:
    def __init__(self, path, title, part):
        self.path = path
        self.title = title
        self.part = part
        self.slug = "index" if path.stem == "introduction" else path.stem
        self.html = ""
        self.headings = []
        self.examples = []
        self.search = []


FENCE = re.compile(r"^(`{3,})\s*([\w-]*)\s*(.*)$")


def parse_attributes(text):
    attributes = {}
    for item in text.split():
        if "=" in item:
            name, value = item.split("=", 1)
            attributes[name] = value
        else:
            attributes[item] = True
    return attributes


def parse_page(page):
    lines = page.path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fence = FENCE.match(line)
        if fence:
            marker, language, attributes = fence.group(1), fence.group(2), parse_attributes(fence.group(3))
            body = []
            start = i + 1
            i += 1
            while i < len(lines) and lines[i].rstrip() != marker:
                body.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", language, attributes, "\n".join(body), start))
            continue
        if not line.strip():
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            blocks.append(("heading", len(heading.group(1)), heading.group(2).strip()))
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            blocks.append(("table", rows))
            continue
        if line.startswith(">"):
            quoted = []
            while i < len(lines) and lines[i].startswith(">"):
                quoted.append(lines[i][1:].lstrip())
                i += 1
            blocks.append(("note", " ".join(quoted)))
            continue
        if re.match(r"^(\s*)([-*]|\d+\.)\s+", line):
            items = []
            while i < len(lines) and lines[i].strip() and (re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[i]) or
                                                           lines[i].startswith("  ")):
                items.append(lines[i])
                i += 1
            blocks.append(("list", items))
            continue
        paragraph = []
        while i < len(lines) and lines[i].strip() and not FENCE.match(lines[i]) and \
                not re.match(r"^(#{1,4})\s", lines[i]) and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) and \
                not lines[i].startswith(">") and not lines[i].startswith("|"):
            paragraph.append(lines[i].strip())
            i += 1
        blocks.append(("paragraph", " ".join(paragraph)))
    return blocks


def render_list(items):
    def parse(index, indent):
        out = []
        ordered = None
        while index < len(items):
            line = items[index]
            match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
            depth = len(match.group(1)) if match else len(line) - len(line.lstrip())
            if depth < indent:
                break
            if match and depth == indent:
                if ordered is None:
                    ordered = match.group(2)[0].isdigit()
                text = match.group(3)
                index += 1
                while index < len(items) and not re.match(r"^\s*([-*]|\d+\.)\s+", items[index]):
                    text += " " + items[index].strip()
                    index += 1
                children = ""
                if index < len(items):
                    child = re.match(r"^(\s*)", items[index]).group(1)
                    if len(child) > indent:
                        children, index = parse(index, len(child))
                out.append(f"<li>{inline(text)}{children}</li>")
            else:
                index += 1
        tag = "ol" if ordered else "ul"
        return f"<{tag}>{''.join(out)}</{tag}>", index

    rendered, _ = parse(0, 0)
    return rendered


def render_table(rows):
    def cells(row):
        text = row.strip()
        text = text[1:] if text.startswith("|") else text
        text = text[:-1] if text.endswith("|") and not text.endswith("\\|") else text
        result, current, ticks, k = [], [], 0, 0
        while k < len(text):
            c = text[k]
            if c == "\\" and k + 1 < len(text) and text[k + 1] == "|":
                current.append("|")
                k += 2
                continue
            if c == "`":
                run = len(text[k:]) - len(text[k:].lstrip("`"))
                ticks = 0 if ticks == run else (run if ticks == 0 else ticks)
                current.append(text[k:k + run])
                k += run
                continue
            if c == "|" and ticks == 0:
                result.append("".join(current).strip())
                current = []
            else:
                current.append(c)
            k += 1
        result.append("".join(current).strip())
        return result

    head = "".join(f"<th>{inline(cell)}</th>" for cell in cells(rows[0]))
    body = "".join("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in cells(row)) + "</tr>"
                   for row in rows[2:])
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def plain(text):
    return html.unescape(re.sub(r"<[^>]+>", "", inline(text)))


def prepare_examples(page, blocks):
    groups = {}
    last = None
    counter = 0
    for index, block in enumerate(blocks):
        if block[0] != "code":
            continue
        _, language, attributes, body, start = block
        if language == "cella":
            key = attributes.get("group")
            if key is None:
                counter += 1
                key = f"#{counter}"
            example = groups.get(key)
            if example is None:
                example = Example(f"{page.path.name}", key)
                example.line = start
                groups[key] = example
                page.examples.append(example)
            compiled, _ = strip_hidden(body)
            name = attributes.get("file", "main.ce")
            if attributes.get("error"):
                example.expects_error = True
            if attributes.get("norun"):
                example.compile_only = True
            example.add_file(name, compiled + "\n")
            last = example
        elif language == "celp" and attributes.get("group"):
            key = attributes["group"]
            example = groups.get(key)
            if example is None:
                example = Example(f"{page.path.name}", key)
                example.line = start
                groups[key] = example
                page.examples.append(example)
            if attributes.get("file") and attributes["file"] != "test.celp":
                example.add_file(attributes["file"], body + "\n")
            else:
                example.project = body + "\n"
        elif language == "output":
            target = groups.get(attributes["group"]) if attributes.get("group") else last
            if target is None:
                raise BuildError(f"{page.path.name}:{start}: output block without an example")
            target.expected_output = body
        elif language == "errors":
            target = groups.get(attributes["group"]) if attributes.get("group") else last
            if target is None:
                raise BuildError(f"{page.path.name}:{start}: errors block without an example")
            target.expected_errors = [line.strip() for line in body.split("\n") if line.strip()]
        elif language == "options":
            last.options = body.split()
        elif language == "args":
            target = last
            target.args = body.split()
    return groups


def render_page(page, blocks, groups, copy_counter):
    out = []
    used = set()
    counter = 0
    section = None
    for block in blocks:
        kind = block[0]
        if kind == "heading":
            level, text = block[1], block[2]
            anchor = slugify(inline(text))
            base, n = anchor, 2
            while anchor in used:
                anchor, n = f"{base}-{n}", n + 1
            used.add(anchor)
            if level == 1:
                out.append(f"<h1>{inline(text)}</h1>")
                section = {"title": plain(text), "anchor": "", "text": []}
            else:
                out.append(f'<h{level} id="{anchor}"><a class="anchor" href="#{anchor}">{inline(text)}</a>'
                           f'</h{level}>')
                if level <= 3:
                    page.headings.append((level, plain(text), anchor))
                section = {"title": plain(text), "anchor": anchor, "text": []}
            page.search.append(section)
        elif kind == "paragraph":
            out.append(f"<p>{inline(block[1])}</p>")
            if section:
                section["text"].append(plain(block[1]))
        elif kind == "note":
            out.append(f'<div class="note"><p>{inline(block[1])}</p></div>')
            if section:
                section["text"].append(plain(block[1]))
        elif kind == "list":
            out.append(render_list(block[1]))
            if section:
                section["text"].append(" ".join(plain(re.sub(r"^\s*([-*]|\d+\.)\s+", "", item)) for item in block[1]))
        elif kind == "table":
            out.append(render_table(block[1]))
            if section:
                section["text"].append(" ".join(plain(row) for row in block[1][2:]))
        elif kind == "code":
            _, language, attributes, body, start = block
            if language == "cella":
                key = attributes.get("group")
                if key is None:
                    counter += 1
                    key = f"#{counter}"
                example = groups[key]
                copy_counter[0] += 1
                out.append(render_cella(example, attributes.get("file", "main.ce"), body, attributes,
                                        copy_counter[0]))
            elif language == "celp":
                copy_counter[0] += 1
                out.append(render_block(highlight_toml(body), "toml", attributes.get("file"), body,
                                        copy_counter[0]))
            elif language == "output":
                out.append(f'<div class="output"><div class="label">Output</div>'
                           f'<pre>{html.escape(body, quote=False)}</pre></div>')
            elif language in ("errors", "args", "options"):
                continue
            else:
                copy_counter[0] += 1
                lines = [html.escape(line, quote=False) for line in body.split("\n")]
                out.append(render_block(lines, language or "text", attributes.get("file"), body, copy_counter[0]))
    return "\n".join(out)


def render_block(lines, language, title, raw, number, annotations=None):
    rows = []
    for k, line in enumerate(lines):
        rows.append(f'<span class="line">{line or " "}</span>')
        for annotation in (annotations or {}).get(k, []):
            rows.append(annotation)
    header = f'<div class="code-title">{html.escape(title)}</div>' if title else ""
    copy = (f'<button class="copy" type="button" aria-label="Copy code" data-copy="copy-{number}"></button>'
            f'<textarea hidden id="copy-{number}">{html.escape(raw)}</textarea>')
    return f'<div class="code {language}">{header}{copy}<pre><code>{"".join(rows)}</code></pre></div>'


def render_cella(example, name, body, attributes, number):
    compiled, shown = strip_hidden(body)
    full = example.files[name]
    tokens = (example.result or {}).get("tokens", {}).get(name, [])
    rendered = highlight(full.rstrip("\n"), tokens)
    lines, mapping = [], {}
    for k, line in enumerate(shown):
        if line is not None:
            mapping[k] = len(lines)
            lines.append(rendered[k] if k < len(rendered) else "")
    annotations = {}
    if example.expects_error and example.result:
        for diagnostic in example.result.get("diagnostics", []):
            if diagnostic["file"] != name or diagnostic["severity"] != "error":
                continue
            source_line = diagnostic["line"] - 1
            target = mapping.get(source_line)
            if target is None:
                continue
            raw_line = full.split("\n")[source_line]
            indent = visual_column(raw_line, diagnostic["column"])
            notes = "".join(f'<span class="diagnostic-note">{html.escape(note)}</span>'
                            for note in diagnostic["notes"])
            annotations.setdefault(target, []).append(
                f'<span class="diagnostic"><span class="squiggle" style="margin-left:{indent}ch;'
                f'width:{max(1, diagnostic["length"])}ch"></span><span class="diagnostic-text" '
                f'style="margin-left:{indent}ch">{html.escape(diagnostic["message"])}{notes}</span></span>')
    title = attributes.get("file") if attributes.get("file") else None
    language = "cella error" if example.expects_error else "cella"
    return render_block(lines, language, title, compiled, number, annotations)


# ---------------------------------------------------------------- site

def read_summary():
    parts = []
    current = None
    for line in (SOURCE / "SUMMARY.md").read_text(encoding="utf-8").split("\n"):
        if line.startswith("# "):
            current = {"title": line[2:].strip(), "pages": []}
            parts.append(current)
        else:
            match = re.match(r"^\s*-\s+\[(.+?)\]\((.+?)\)", line)
            if match:
                if current is None:
                    current = {"title": "", "pages": []}
                    parts.append(current)
                current["pages"].append(Page(SOURCE / match.group(2), match.group(1), current["title"]))
    return parts


def sidebar(parts, page):
    out = []
    number = 0
    for part in parts:
        if part["title"]:
            out.append(f'<li class="part">{html.escape(part["title"])}</li>')
        for entry in part["pages"]:
            if entry.slug != "index":
                number += 1
            label = f'<span class="number">{number}.</span> ' if entry.slug != "index" else ""
            current = ' class="current"' if entry is page else ""
            out.append(f'<li><a href="{entry.slug}.html"{current}>{label}{html.escape(entry.title)}</a></li>')
    return "<ul>" + "".join(out) + "</ul>"


def write_pages(parts, selected, version, full):
    template = (SITE / "tools" / "page.html").read_text(encoding="utf-8")
    pages = [page for part in parts for page in part["pages"]]
    search = []
    for k, page in enumerate(pages):
        if page not in selected:
            continue
        previous = pages[k - 1] if k > 0 else None
        following = pages[k + 1] if k + 1 < len(pages) else None
        navigation = '<nav class="pager">'
        navigation += (f'<a class="previous" href="{previous.slug}.html"><span>Previous</span>'
                       f'{html.escape(previous.title)}</a>' if previous else "<span></span>")
        navigation += (f'<a class="next" href="{following.slug}.html"><span>Next</span>'
                       f'{html.escape(following.title)}</a>' if following else "<span></span>")
        navigation += "</nav>"
        toc = "".join(f'<li class="level-{level}"><a href="#{anchor}">{html.escape(text)}</a></li>'
                      for level, text, anchor in page.headings)
        toc = f'<div class="toc-title">On this page</div><ul>{toc}</ul>' if toc else ""
        title = "Cella Documentation" if page.slug == "index" else f"{page.title} - Cella Documentation"
        content = (template.replace("{{title}}", html.escape(title))
                   .replace("{{version}}", version)
                   .replace("{{sidebar}}", sidebar(parts, page))
                   .replace("{{content}}", page.html)
                   .replace("{{toc}}", toc)
                   .replace("{{pager}}", navigation))
        (OUTPUT / f"{page.slug}.html").write_text(content, encoding="utf-8", newline="\n")
        for section in page.search:
            search.append({"page": page.title, "title": section["title"],
                           "url": f"{page.slug}.html" + (f"#{section['anchor']}" if section["anchor"] else ""),
                           "text": " ".join(section["text"])[:2000]})
    if full:
        (OUTPUT / "search-index.js").write_text("window.searchIndex = " + json.dumps(search) + ";\n",
                                            encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description="Builds the Cella documentation")
    parser.add_argument("--cella", default=os.environ.get("CELLA_REPO"),
                        help="use the Debug build of this Cella checkout instead of an installed version")
    parser.add_argument("--version", help="the installed version to use, the newest when not given")
    parser.add_argument("--only", action="append", default=[], help="check only these chapter files")
    parser.add_argument("--jobs", type=int, default=8)
    arguments = parser.parse_args()

    compiler, server, version = compiler_paths(arguments.cella, arguments.version)
    stamp = tool_stamp(compiler, server)
    CACHE.mkdir(parents=True, exist_ok=True)
    parts = read_summary()
    pages = [page for part in parts for page in part["pages"]]
    selected = [page for page in pages if not arguments.only or page.path.name in arguments.only]
    for page in selected:
        if not page.path.exists():
            raise BuildError(f"Missing {page.path}")

    parsed = {}
    examples = []
    for page in selected:
        blocks = parse_page(page)
        parsed[page.path] = (blocks, prepare_examples(page, blocks))
        examples.extend(page.examples)

    with concurrent.futures.ThreadPoolExecutor(arguments.jobs) as pool:
        list(pool.map(lambda example: run_example(example, compiler, stamp), examples))
    collect_tokens(examples, server)
    for example in examples:
        directory = pathlib.Path(example.result["directory"])
        for output in [path for path in directory.rglob("*") if path.is_dir() and path.name in ("bin", "obj")]:
            shutil.rmtree(output, ignore_errors=True)
    if not arguments.only:
        used = {pathlib.Path(example.result["directory"]).name for example in examples}
        for entry in CACHE.iterdir():
            if entry.is_dir() and entry.name not in used:
                shutil.rmtree(entry, ignore_errors=True)

    problems = []
    for example in examples:
        problems.extend(check_example(example))

    copy_counter = [0]
    for page in selected:
        blocks, groups = parsed[page.path]
        page.html = render_page(page, blocks, groups, copy_counter)
    write_pages(parts, selected, version, not arguments.only)
    if not arguments.only:
        problems.extend(check_links(pages))

    print(f"{len(selected)} pages, {len(examples)} examples")
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


def check_links(pages):
    anchors = {f"{page.slug}.html": set(re.findall(r'id="([^"]+)"', page.html)) for page in pages}
    problems = []
    for page in pages:
        for target in re.findall(r'href="([^"]+)"', page.html):
            if re.match(r"[a-z]+:", target) or target.startswith("../"):
                continue
            name, _, anchor = target.partition("#")
            name = name or f"{page.slug}.html"
            if name not in anchors:
                problems.append(f"{page.path.name}: link to missing page {target}")
            elif anchor and anchor not in anchors[name]:
                problems.append(f"{page.path.name}: link to missing anchor {target}")
    return problems


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
