# Project settings

A project file, the `.celp` file in a project's folder, is written in TOML. This page lists every setting it can hold, the values each takes and what it does when it's left out. [Projects and building](projects.md) introduces project files and the commands that read them.

## Summary

| Setting | Values | Default | In `[When]` tables |
| --- | --- | --- | --- |
| `OutputType` | `"Executable"`, `"WindowedExecutable"`, `"SharedLibrary"`, `"StaticLibrary"` | required | no |
| `CellaVersion` | a version such as `"0.1.0"` | none | no |
| `StandardLibrary` | `"Full"`, `"Core"`, `"None"` | `"Full"` | no |
| `SystemLinkPreference` | `"Dynamic"`, `"Static"` | `"Dynamic"` | yes |
| `AssemblyName` | a file name | the project file's name | yes |
| `BoundsChecks` | `true`, `false` | `true` | yes |
| `OverflowChecks` | `true`, `false` | `true` in debug builds, `false` in release builds | yes |
| `DebugInfo` | `true`, `false` | `true` | yes |
| `Referenceable` | `true`, `false` | `false` | yes |
| `Imports` | a list of import paths | none | no |
| `Prelude` | a list of import paths | none | no |
| `[Flags]` | flag names set to `true` or `false` | none | no |
| `[[ProjectReferences]]` | `Path` and `Alias` | none | yes |
| `[When."..."]` | a condition and the settings it changes | none | |

Setting names are case-sensitive, and any other name is an error such as "Unknown setting 'Optimize'". A setting given twice is an error too.

## OutputType

What the project builds. It's the one setting every project file needs; without it the build stops with "Missing 'OutputType'".

| Value | Builds | Windows file | Linux file |
| --- | --- | --- | --- |
| `"Executable"` | a program | `name.exe` | `name` |
| `"WindowedExecutable"` | a program that opens no console window on Windows | `name.exe` | `name` |
| `"SharedLibrary"` | a library loaded when a program starts | `name.dll` | `libname.so` |
| `"StaticLibrary"` | a library linked into each program that uses it | `name.lib` | `libname.a` |

`name` is the [AssemblyName](#assemblyname). Executables need a `main` function, as [Functions](functions.md#the-main-function) explains.

## CellaVersion

The version of Cella the project is written for. `cella new` writes the version that created the project. When you run `cella`, the launcher reads this setting and runs that version of the compiler, which must be installed; without it, the launcher runs the newest version installed. [Projects and building](projects.md#the-launcher) covers the launcher.

The compiler compares the setting with its own version. A project pinned to a newer version is an error ("Pinned to Cella 99.0.0, newer than this compiler"), and one pinned to an older version gets a warning. The value must be a full version with three numbers, such as `"0.1.0"` or `"0.2.0-dev"`.

## StandardLibrary

How much of the standard library the project references.

| Value | References |
| --- | --- |
| `"Full"` | all of the standard library |
| `"Core"` | only the parts that don't depend on the operating system |
| `"None"` | nothing |

The standard library's `panic` is in the part that depends on the operating system, so with `"Core"` or `"None"` a project has none unless it declares one, as [Checks and panics](panics.md#declaring-a-panic-operator) shows.

## SystemLinkPreference

How a program links the C runtime when it's built for Windows with Visual Studio's C++ build tools. `"Dynamic"` uses the runtime's DLLs, and `"Static"` copies the runtime into the program. Other builds link the C runtime the same way with either value.

All projects in one program must agree, in every build. A program that links the C runtime statically can't use a shared library project, and a library used by two programs that link differently is an error. [Calling C](calling-c.md#linking-the-c-runtime) covers linking.

## AssemblyName

The name of the output file, without its extension or `lib` prefix. It defaults to the project file's name, so `game.celp` builds `game.exe`. It must be a valid file name, so it can't be empty or contain a path, and the name of a shared library must be ASCII.

## BoundsChecks

Whether indexing an array or a string checks that the index is in range, stopping the program with a panic when it isn't. On by default in every build. The built-in flag `boundsChecks` says whether the checks are on. [Checks and panics](panics.md#turning-checks-on-and-off) covers the checks.

## OverflowChecks

Whether arithmetic checks for overflow, stopping the program with a panic when a result doesn't fit its type. On by default in debug builds and off in release builds. The built-in flag `overflowChecks` says whether the checks are on. [Numbers](numbers.md#overflow) and [Checks and panics](panics.md#turning-checks-on-and-off) cover overflow.

## DebugInfo

Whether the build includes debug information for debuggers. On by default.

## Referenceable

Whether other projects can reference this executable and use its `pub` declarations, as they would a library's. A referenceable executable is built as a shared library that holds its code, and a small program that runs it. The setting applies only to executables, and a referenceable executable can't link the C runtime statically. Referencing an executable without it is an error that names the executable's project file: "... is an executable without 'Referenceable = true'".

## Imports and Prelude

`Imports` lists imports that apply to every source file in the project, written as they would be after `use`. `Prelude` lists imports that apply to every project that references this one. [Modules and visibility](modules.md#project-imports) covers both.

## Flags

`[Flags]` declares the project's own flags, each set to `true` or `false`. Code tests them with `when`:

```celp group=flags
OutputType = "Executable"

[Flags]
verbose = true
```

```cella group=flags
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when verbose
	{
		printf("starting\n")
	}

	printf("done\n")
}
```

```output
starting
done
```

A flag's name must be an identifier, and it can't be the name of a built-in flag. `cella build --flag verbose=false` changes a flag's value for one build, as [Projects and building](projects.md#flags) shows. [Conditional compilation](conditional-compilation.md#project-flags) covers `when`.

The built-in flags are always defined:

| Flag | True when |
| --- | --- |
| `windows`, `linux`, `macos` | building for that operating system |
| `x64`, `x86`, `arm64`, `wasm64` | building for that processor |
| `debug` | building without `--release` |
| `release` | building with `--release` |
| `boundsChecks` | bounds checks are on |
| `overflowChecks` | overflow checks are on |

## ProjectReferences

Each `[[ProjectReferences]]` table makes the project use another one, usually a library. It has two settings:

| Setting | Meaning |
| --- | --- |
| `Path` | The other project's `.celp` file, relative to this project's folder. Required. |
| `Alias` | A name to reach the other project's modules through. Optional. |

Without an alias, the other project's modules are reached by their own names. With one, they are reached only through the alias, which keeps modules of the same name in different projects apart:

```celp group=alias
OutputType = "Executable"

[[ProjectReferences]]
Path = 'geometry/geometry.celp'
Alias = 'geo'
```

```celp group=alias file=geometry/geometry.celp
OutputType = "StaticLibrary"
```

```cella group=alias file=geometry/shapes.ce
mod shapes

area: pub fun(width: f64, height: f64) -> f64 => width * height
```

```cella group=alias
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%.1f\n", geo.shapes.area(2.0, 3.0))
}
```

```output
6.0
```

An alias must be an identifier, can't be the name of a built-in type, and can't name two references. [Projects and building](projects.md#using-a-library-project) covers using library projects.

## When tables

A `[When."condition"]` table changes settings in the builds where its condition holds. The condition uses flags, built-in or the project's own, with `!`, `&&`, `||` and parentheses, as in a `when` block. A condition that is a single flag can leave out the quotes: `[When.debug]`.

```celp group=when
OutputType = "Executable"

[Flags]
fast = false

[When.debug]
OverflowChecks = false

[When."release || fast"]
BoundsChecks = false
```

```cella group=when
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when overflowChecks
	{
		printf("overflow checks on\n")
	}
	else
	{
		printf("overflow checks off\n")
	}

	when boundsChecks
	{
		printf("bounds checks on\n")
	}
}
```

```output
overflow checks off
bounds checks on
```

This is a debug build, so the first table applies and the second doesn't. A release build, or one with `--flag fast`, would also turn bounds checks off.

A setting in a `When` table replaces the one at the top level. Only `SystemLinkPreference`, `AssemblyName`, `BoundsChecks`, `OverflowChecks`, `DebugInfo`, `Referenceable` and project references can go in one. `[[When."condition".ProjectReferences]]` tables add references in the builds where the condition holds, after the ones at the top level:

```celp
[[When.windows.ProjectReferences]]
Path = 'win32/win32.celp'
```

Two tables whose conditions both hold can't set the same setting: that's an error such as "'BoundsChecks' is set more than once, by [When."debug"] and [When."windows || linux"]".

## Problems in project files

The compiler checks the whole project file before building and reports every problem it finds. Besides unknown and repeated settings, it reports values of the wrong kind, each naming the setting and the table it's in:

- "'Program' is not a valid 'OutputType'"
- "'BoundsChecks' must be true or false"
- "'logging' in [Flags] must be true or false"
- "'Imports' must be a list of strings"
- "Missing 'Path' in [[ProjectReferences]]"
- "Project 'lib/lib.celp' not found"
- "Cannot set 'OutputType' in [When."debug"]"
- "Flag 'unknown' not found in [When."debug && unknown"]"

A folder can hold only one project file; a second one is an error, "Cannot share a directory with 'other.celp'".
