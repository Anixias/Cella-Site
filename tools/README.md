# Cella documentation

The documentation's chapters are Markdown files in `docs/src`, listed in order in `docs/src/SUMMARY.md`. `tools/docs.py` turns them into the HTML pages in `docs/`, compiling and running every example on the way.

## Building

The script uses the newest Cella installed in `CELLA_HOME` (`C:\cella` or `~/.cella`), its standard library and its language server. `--version <name>` picks another installed version, and `--cella <folder>` (or `CELLA_REPO`) uses the Debug build of a Cella checkout instead. The version's name appears in each page's header. The script runs on Windows and needs Python 3.

```
python tools/docs.py
python tools/docs.py --only records.md --only enums.md
```

A full build writes every page and the search index and checks every link. `--only` checks and writes just the named chapters. The script prints each problem it finds and exits with 1 if there were any. Results are cached in `tools/.cache` by example and toolchain, so an unchanged example isn't compiled again until the compiler or standard library changes.

## Writing chapters

A chapter starts with one `#` heading, its title. `##` and `###` headings make the "On this page" list and the anchors other pages link to (`[records](records.md#constructors)`). Paragraphs, lists (`-` or `1.`), tables, `> notes`, `**bold**`, `*italic*`, `` `code` `` and links work as in Markdown.

### Examples

A `cella` code block is a program. The script builds it as its own project with the standard library referenced, runs it, and checks what it prints:

````
```cella
mod example

main: fun
{
}
```
````

- An `output` block right after it is the program's expected output (standard output, then standard error). A program that prints needs one, and a mismatch is an error.
- `cella error` marks a program the compiler must reject. An `errors` block after it lists the expected error messages, one per line, in order; each line must appear in the matching message. The page shows each error under the line it points to.
- `cella norun` builds the program without running it.
- Lines that start with `~ ` (or are just `~`) are compiled but not shown. Use them for the `mod` line, the `ext` block and other setup that isn't the point of the example. The copy button copies the whole program, hidden lines included.
- `group=name` puts several blocks in one project, each `file=name.ce` (the default is `main.ce`). A `celp group=name` block replaces the project file, and a `celp group=name file=lib/lib.celp` block adds another project file to the group. `output` and `errors` blocks apply to the last example before them, or to `group=name`.
- An `args` block after an example lists the command-line arguments the program gets, and an `options` block lists extra arguments for `cella build`, such as `--release` or `--flag logging`. Neither is shown on the page.

Other code blocks (`sh`, `powershell`, `text`, a `celp` block without `group`) are shown as they are and never checked.

### The usual setup lines

```
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
```
