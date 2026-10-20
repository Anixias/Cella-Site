# Conditional compilation

Some code belongs only in some builds: a Windows call that doesn't exist on Linux, logging that a release build should leave out, a check that only debug builds pay for. Cella decides this at compile time with build flags. A `when` block keeps its contents only in builds whose flags match, a `use when` line keeps or drops a whole file, and a function marked `when` disappears, calls and all, from builds where its flag is off.

## `when` blocks

`when` is followed by a flag condition and a block. In a build where the condition holds, the block's contents are compiled as if the `when` weren't there. Otherwise they're left out:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when debug
	{
		printf("debug build\n")
	}

	when release
	{
		printf("release build\n")
	}
}
```

```output
debug build
```

Built with `--release`, the same program prints the other line:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when debug
	{
		printf("debug build\n")
	}

	when release
	{
		printf("release build\n")
	}
}
```

```options
--release
```

```output
release build
```

The braces are required, even around a single statement. A `when` block doesn't start a scope, so a declaration inside it stays visible after it, as the next section shows.

### `else when` and `else`

`else when` and `else` chain further branches. The first branch whose condition holds is kept, and `else` is kept when none does:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when release
	{
		val mode: cstr = "release"
	}
	else when debug && overflowChecks
	{
		val mode: cstr = "checked debug"
	}
	else
	{
		val mode: cstr = "debug"
	}

	printf("%s\n", mode)
}
```

```output
checked debug
```

Each branch declares `mode`, and only one of them is ever compiled, so the `printf` after the chain sees exactly one `mode`.

### Conditions

A condition is made of flag names, `!`, `&&`, `||` and parentheses, with the same meaning and precedence as in ordinary expressions. Nothing else can appear in it: no values, no comparisons, no calls. A name that isn't a flag is an error, with a suggestion when a flag has a close spelling:

```cella error
mod example

main: fun
{
	when debg
	{
	}

	when profiling
	{
	}
}
```

```errors
Flag 'debg' not found
Flag 'profiling' not found
```

### Where `when` blocks go

`when` blocks can surround top-level declarations, members of records, enums, traits and other types, enum cases, the members of an `ext` block, statements, and the contents of visibility blocks:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
when debug
{
	label: const cstr = "debug"
}
else
{
	label: const cstr = "release"
}

Counter: rec
{
	n: i32

	when debug
	{
		describe: fun(self) => printf("%s counter at %d\n", label, self.n)
	}
	else
	{
		describe: fun(self) => printf("%d\n", self.n)
	}
}

Step: enum
{
	start

	when debug
	{
		traced
	}

	finish
}

main: fun
{
	val c = Counter(4)
	c.describe()
	printf("%d\n", i32(Step.finish))
}
```

```output
debug counter at 4
2
```

`Step.finish` is 2 in a debug build, because `traced` takes the value 1. In a release build `traced` doesn't exist and `finish` is 1.

Inside a `match`, `when` groups arms, with `else` for the other builds. The match's `else` arm stays the last arm:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
size: fun(x: i32) -> i32 => match x
{
	0 => 0
	when debug
	{
		1 => 10
	}
	else
	{
		1 => 20
	}
	else => 5
}

main: fun
{
	printf("%d %d %d\n", size(0), size(1), size(2))
}
```

```output
0 10 5
```

### Code in other builds is only parsed

A branch that isn't kept is parsed but not checked. It can call functions that don't exist in this build, use types that don't exist and name symbols from other platforms, so platform-specific code compiles on every platform:

```cella norun
~ mod example
~
when windows
{
	ext("kernel32")
	{
		GetCurrentProcessId: fun -> u32
	}

	processId: fun -> u32 => GetCurrentProcessId()
}
else
{
	ext
	{
		getpid: fun -> i32
	}

	processId: fun -> u32 => u32(getpid())
}

main: fun -> i32 => i32(processId() % 100)
```

On Windows, only the first branch is checked and built; on Linux, only the second. Building with `--target`, as described in [Projects and building](projects.md), checks the branches for another platform.

Syntax errors are reported in every branch, since every branch is parsed:

```cella error
mod example

main: fun
{
	when linux && windows
	{
		val c = 'ab'
	}
}
```

```errors
Invalid character literal
```

## Built-in flags

These flags are always defined:

| Flag | On when |
| --- | --- |
| `windows`, `linux`, `macos` | building for that operating system |
| `x64`, `x86`, `arm64`, `wasm64` | building for that processor |
| `debug` | building without `--release` |
| `release` | building with `--release` |
| `boundsChecks` | the project's `BoundsChecks` setting is on |
| `overflowChecks` | the project's `OverflowChecks` setting is on |

`boundsChecks` and `overflowChecks` follow the settings of the project that declares the code, so code that checks its own bounds or overflow can do it exactly when the built-in checks are on. `OverflowChecks` is on by default in debug builds only:

```cella
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
}
```

```options
--release
```

```output
overflow checks off
```

[Checks and panics](panics.md) covers both settings.

## Project flags

A project declares its own flags in a `[Flags]` table in its `.celp` file, each with a default value:

```celp group=projectFlags
OutputType = "Executable"

[Flags]
logging = true
profiling = false
```

```cella group=projectFlags
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when logging
	{
		printf("logging\n")
	}

	when profiling
	{
		printf("profiling\n")
	}
}
```

```output
logging
```

The table can also be written on one line, as `Flags = { logging = true, profiling = false }`. A flag name must be a valid identifier and can't be the name of a built-in flag.

`--flag` sets a flag for one build, overriding its default. `--flag profiling` turns it on, and `--flag profiling=false` turns it off:

```sh
cella build --flag profiling
cella run --flag logging=false
```

Built with `--flag profiling`, the program above prints both lines:

```cella group=projectFlagsSet
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	when logging
	{
		printf("logging\n")
	}

	when profiling
	{
		printf("profiling\n")
	}
}
```

```celp group=projectFlagsSet
OutputType = "Executable"

[Flags]
logging = true
profiling = false
```

```options
--flag profiling
```

```output
logging
profiling
```

`--flag` only sets flags the project declares. A name that isn't declared is "Flag 'missing' not found", and setting a built-in flag such as `debug` is "Cannot set built-in flag 'debug'". Flags belong to the project that declares them: a library's code is built with the flags and defaults in the library's own `.celp`.

## Leaving out whole files

`use when` with a condition, written right after the `mod` line, keeps or leaves out the whole file. A file left out is only parsed, like a `when` branch that isn't kept:

```cella group=useWhen file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%s\n", mode())
}
```

```cella group=useWhen file=debug.ce
mod example
use when debug

mode: fun -> cstr => "debug"
```

```cella group=useWhen file=release.ce
mod example
use when !debug

mode: fun -> cstr => "release"
```

```output
debug
```

Each build sees exactly one `mode`. The `use when` line must directly follow the `mod` line, before any other import ("'use when' must directly follow the module name"), and a file has at most one:

```cella error group=useWhenTwice
mod example
use when debug
use when windows

main: fun
{
}
```

```errors
Cannot declare more than one 'use when'
Cannot declare more than one 'use when'
```

## `when` functions

A function can carry a condition of its own, written after its signature: `trace: fun(value: i32) when logging`. Unlike a `when` block, a `when` function is checked in every build. In builds where its condition holds, it's an ordinary function. In other builds it doesn't exist, and every call to it is removed along with its arguments, so they aren't evaluated:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
calls: var i32 = 0

count: fun(value: i32) -> i32
{
	calls += 1
	ret value
}

trace: fun(value: i32) when debug
{
	printf("trace %d\n", value)
}

measure: fun(value: i32) when release
{
	printf("measure %d\n", value)
}

main: fun
{
	trace(count(1))
	measure(count(2))
	printf("%d calls\n", calls)
}
```

```output
trace 1
1 calls
```

The call to `measure` and its argument `count(2)` are gone from this debug build, so `count` ran once.

Because the arguments are still checked as if the call ran, a program means the same in every build. Here `log` would use `text` after it was moved, which is an error even in a release build where `log` is never called:

```cella error
~ mod example
~
Text: rec
{
	id: i32

	drop: op
	{
	}
}

take: fun(own text: Text)
{
}

log: fun(imm text: Text) when release
{
}

main: fun
{
	val text = Text(1)
	take(own text)
	log(imm text)
}
```

```errors
Cannot use moved values
```

To leave code out unchecked, put it in a `when` block instead.

Methods and static functions can be `when` functions too, and generic functions and functions taking templates work the same way. Since calls to them may vanish, `when` functions are limited to what a removed call can't miss:

- They return nothing, and they can't be `-> never`.
- They can't take `own` parameters, since a removed call would leave the value unmoved.
- They can't be used as values.
- `main`, constructors, destructors, getters, setters, operators and `ext` functions can't be `when` functions, a trait can't require one, and one can't implement a trait's member.

```cella error
~ mod example
~
total: fun(value: i32) -> i32 when debug => value

keep: fun(own value: i32) when debug
{
}

trace: fun(value: i32) when debug
{
}

apply: fun(action: fun[i32]) => action(1)

main: fun
{
	apply(trace)
}
```

```errors
Cannot return values from 'when' functions
Cannot take 'own' parameters in 'when' functions
Cannot use 'when' functions as values
```

## Conditional project settings

A `.celp` file can hold tables named `[When."condition"]`, with a condition written as in `when`. Their settings apply only to builds where the condition holds and override the settings at the top of the file. A condition that is a single flag can drop the quotes, as in `[When.debug]`:

```celp group=conditionalSettings
OutputType = "Executable"
OverflowChecks = true

[Flags]
fast = false

[When."release && fast"]
OverflowChecks = false
```

```cella group=conditionalSettings
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
		printf("checked\n")
	}
	else
	{
		printf("unchecked\n")
	}
}
```

```options
--release
```

```output
checked
```

Built with `--release --flag fast`, the same program prints `unchecked`.

A conditional table can also add project references, which are added to the ones at the top level:

```text
[[When."windows || linux".ProjectReferences]]
Path = 'platform/platform.celp'
```

`OutputType` and `[Flags]` can't be set in a conditional table. When two tables that both apply set the same setting, the build fails with an error naming both tables. [Project settings](project-settings.md) lists which settings can be conditional.
