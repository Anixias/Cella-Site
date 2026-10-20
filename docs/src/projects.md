# Projects and building

A Cella program is built from a project: a folder with a project file and the source files that belong to it. This chapter covers creating projects, what goes in the project file, building and running with `cella build` and `cella run`, projects that use other projects, and the launcher that manages Cella versions.

## Creating a project

`cella new` creates a project in a new folder:

```sh
cella new game
```

```text
Created 'game'
```

The folder holds two files. `game.celp` is the project file:

```celp
OutputType = "Executable"
CellaVersion = "0.1.0"
```

`main.ce` is the greeting program from [Hello, World](hello-world.md#a-first-program), starting with `mod game`.

The argument can be a path, such as `cella new tools/packer`; the last part of the path is the project's name. Without an argument, `cella new` turns the current folder into a project named after the folder.

The name becomes the project file's name and the name of the module in `main.ce`, so it must be a valid identifier (see [Lexical structure](lexical-structure.md)):

```sh
cella new my-game
```

```text
'my-game' can't be a project name
```

`cella new` never overwrites anything. A folder that already exists and isn't empty is an error, and so is a folder that already has a project file:

```text
'game' already exists
```

### Libraries

`--lib` creates a static library instead of a program:

```sh
cella new physics --lib
```

Its project file has `OutputType = "StaticLibrary"` along with the `CellaVersion` line, and in place of `main.ce` it has a source file named after the project, with one exported function:

```celp group=newlib
OutputType = "StaticLibrary"
```

```cella group=newlib file=physics.ce
mod physics

add: pub fun(a: i32, b: i32) -> i32 => a + b
```

A library has no `main`. Other projects use it through a [project reference](#using-a-library-project).

### A .gitignore file

`--gitignore` also writes a `.gitignore` file that leaves the build folders, `bin/` and `obj/`, out of Git:

```sh
cella new game --gitignore
```

## What a project is

A project is a `.celp` file and the folder it's in. Every `.ce` file in that folder belongs to the project, and so does every `.ce` file in its subfolders, except in a subfolder that has a `.celp` file of its own: that subfolder is a separate project.

Every source file starts with a `mod` line that names its module. Files don't have to be listed anywhere; adding a `.ce` file to the folder adds it to the build.

## The project file

The project file is written in TOML. Each line sets one setting:

```celp
OutputType = "Executable"
CellaVersion = "0.1.0"
```

`OutputType` is the only setting every project needs. It says what the build produces:

| Value | Produces |
| --- | --- |
| `"Executable"` | a program that runs in a terminal |
| `"WindowedExecutable"` | a program that opens no terminal window on Windows |
| `"StaticLibrary"` | a library that is copied into the programs that use it |
| `"SharedLibrary"` | a library loaded when a program starts (`.dll` on Windows, `.so` on Linux) |

`CellaVersion` pins the project to a Cella version. `cella new` writes the version that created the project. The [launcher](#the-launcher) reads the pin to pick which installed compiler builds the project. A project pinned to a newer version than the compiler building it is an error, and one pinned to an older version gets a warning and builds:

```text
game.celp: Pinned to Cella 0.1.0, older than this compiler
```

A misspelled setting or a missing `OutputType` is an error. Problems in a project file are reported with the file's full path, shortened here:

```text
game.celp: Unknown setting 'Outputs'
game.celp: Missing 'OutputType'
```

[Project settings](project-settings.md) lists every setting.

## Building

`cella build` builds the project in the current folder:

```sh
cd game
cella build
```

```text
game -> bin\game.exe
```

The last line names each project built and the file it produced. `cella build` also takes a project file or a folder: `cella build game.celp`, or `cella build projects`, which builds every project in `projects` and its subfolders.

The build writes into two folders beside the project file:

- `bin` holds what the build produces: the program or library, and on Windows its debug information.
- `obj` holds the intermediate files: object files for each module, and the parts of the standard library the project uses.

The program is named after the project file: `game.celp` builds `game.exe` on Windows and `game` on Linux. Both folders can be deleted at any time; the next build makes them again.

Errors and warnings print with the line they point to. A build with errors produces nothing and exits with code 1.

## Build options

`cella build` takes these options, in any order before or after the path:

| Option | Effect |
| --- | --- |
| `--release` | builds with optimizations and without overflow checks |
| `--target <target>` | builds for another system |
| `--flag <name>` | sets a flag to true; `--flag <name>=false` sets it to false |
| `--entry <module.function>` | builds a program that starts in another function |
| `--hints` | also prints hints |
| `--verbose` | prints details of each step of the build, including the linker's command lines |
| `--emit-ir` | also writes each module's LLVM IR into `obj`, as `.ll` files |
| `--emit-asm` | also writes each module's assembly into `obj`, as `.s` files |

### Release builds

Without `--release`, a build is a debug build: no optimizations, and arithmetic that overflows stops the program with a message. `--release` turns on optimizations and leaves out the overflow checks. Bounds checks on array indexing stay on in both. Both kinds of build write to the same `bin` folder. [Checks and panics](panics.md) covers the checks and the settings that change them.

```sh
cella build --release
```

### Targets

`--target` builds for a system other than the one running the compiler:

| Target | Builds for |
| --- | --- |
| `windows-x64` | 64-bit Windows, with Visual Studio's C++ build tools when they're installed and MinGW-w64 otherwise |
| `windows-x64-msvc` | 64-bit Windows, with Visual Studio's C++ build tools |
| `windows-x64-gnu` | 64-bit Windows, with MinGW-w64 |
| `linux-x64` | 64-bit Linux |

```sh
cella build --target linux-x64
```

```text
game -> bin\game
```

Without `--target`, the build is for the system it runs on.

### Flags

Flags are names that are true or false at build time. Code can test them in `when` blocks to leave parts of a program out of some builds. `--flag` sets one for a build, overriding the project's own setting for it:

```sh
cella build --flag logging
cella build --flag logging=false
```

[Conditional compilation](conditional-compilation.md) covers flags and `when`.

### Entry points

`--entry` builds a program that starts in a function other than `main`. The function is named with its module, and it must be `pub` (see [Modules and visibility](modules.md)). This makes it possible to keep small extra programs, such as a demo or a benchmark, in the same project:

```cella norun file=demo.ce
mod game

demo: pub fun
{
	puts("demo")
}
~
~ ext
~ {
~ 	puts: fun(text: cstr) -> i32
~ }
```

```options
--entry game.demo
```

```sh
cella run --entry game.demo
```

```text
demo
```

A program built with `--entry` goes into `obj/entry/<function>` instead of `bin`, so it never replaces the project's own program. [Functions](functions.md) covers what an entry function may look like.

### Hints

Hints point at code that works but could be written better, such as a `var` whose value never changes. They aren't shown unless the build is given `--hints`:

```sh
cella build --hints
```

```text
Hint at main.ce:10:6
 9 │ {
10 │     var shown = 1
             ╘═══╛ 'shown' is never changed

game -> bin\game.exe
```

## Running

`cella run` builds a program and runs it. It takes the same path and options as `cella build`:

```sh
cella run
cella run --release
```

The program runs in the current folder and uses the same terminal. Its output appears as it runs, without the `game -> bin\game.exe` line, and `cella run` exits with the program's exit code. A build with errors doesn't start the program.

Everything after `--` goes to the program as its command-line arguments:

```sh
cella run -- one two
```

The program reads them through the parameters of `main`, as [Functions](functions.md#command-line-arguments) shows.

`cella run` runs only programs built for the system it's on, so `--target` can only name that system:

```text
Cannot run 'linux-x64' programs on this system
```

A library can't be run, and a folder must hold exactly one program:

```text
'physics' is a library
'tools' has several programs: 'packer\packer.celp', 'viewer\viewer.celp'
```

## Several files

A project can have any number of source files. Files that declare the same module share their declarations, so a function in one file can be called from another without anything else:

```cella group=files file=main.ce
~ mod game
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d\n", area(3, 4))
}
```

```cella group=files file=geometry.ce
mod game

area: fun(width: i32, height: i32) -> i32 => width * height
```

```output group=files
12
```

The order of the files doesn't matter, and neither does the order of declarations in them. Files can also declare other modules; [Modules and visibility](modules.md) covers modules, imports and qualified names.

A C function declared in an `ext` block belongs to its module like any other function, so a module declares it once, in one of its files. Declaring the same function in two files of one module is an error.

## Using a library project

A program uses a library project by referencing it in a `[[ProjectReferences]]` table. `Path` is the library's project file, relative to the program's:

```celp group=reference
OutputType = "Executable"

[[ProjectReferences]]
Path = "physics/physics.celp"
```

The library lives in its own folder with its own project file:

```celp group=reference file=physics/physics.celp
OutputType = "StaticLibrary"
```

```cella group=reference file=physics/physics.ce norun
mod physics

add: pub fun(a: i32, b: i32) -> i32 => a + b
```

The program calls the library's functions through the library's module:

```cella group=reference file=main.ce
~ mod game
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d\n", physics.add(2, 3))
}
```

```output group=reference
5
```

Building the program builds the library first, so `cella build` and `cella run` in the program's folder are enough. Each project writes its own `bin` and `obj` folders. A static library is copied into the program; a shared library is a separate file the program loads when it starts.

Only `pub` declarations can be used from other projects. Declarations without a visibility word belong to their own project. [Modules and visibility](modules.md) covers `pub`, imports with `use`, and the other visibility levels.

To reference several projects, repeat the table. `Alias` puts every module of a reference under an extra name, which keeps two libraries apart when they have modules with the same name:

```celp
[[ProjectReferences]]
Path = "a/a.celp"

[[ProjectReferences]]
Path = "b/b.celp"
Alias = "second"
```

With these references, `shared.one()` calls the `shared` module from `a`, and `second.shared.one()` the one from `b`.

## The standard library

Every project uses the standard library unless its project file says otherwise. The `StandardLibrary` setting picks how much of it:

| Value | Uses |
| --- | --- |
| `"Full"` | all of the standard library (the default) |
| `"Core"` | only the parts that don't depend on the operating system |
| `"None"` | none of it |

```celp
OutputType = "Executable"
StandardLibrary = "Core"
```

The standard library is built with the project, into the project's `obj` folder. It is documented separately; this documentation covers only the language.

## The launcher

The `cella` command is a small launcher. It keeps track of the installed Cella versions, and for every command that builds or creates a project it runs the right compiler:

- For a project with a `CellaVersion`, it runs that version. When a folder holds several projects, it runs the highest version any of them pins.
- For a project without a pin, and for `cella new`, it runs the newest installed version.

A pinned version that isn't installed is an error that names the command to install it:

```text
Cella 0.1.0 isn't installed. Run 'cella install 0.1.0'.
```

The launcher has its own commands:

| Command | Effect |
| --- | --- |
| `cella install` | installs the latest release |
| `cella install <version>` | installs that version |
| `cella uninstall <version>` | removes that version |
| `cella list` | lists the installed versions and the ones available to install |
| `cella list --installed` | lists only the installed versions |
| `cella self update` | updates the launcher |
| `cella self uninstall` | removes Cella completely |
| `cella lsp` | starts the language server for the current folder, for editors |
| `cella --version` | prints the compiler's version |

`cella install`, `cella list` (without `--installed`) and `cella self update` are the only commands that use the network. Builds never download anything.

To run one command with another installed version, put `+` and the version before it. This ignores the project's pin for that command only:

```sh
cella +0.1.0 build
```
