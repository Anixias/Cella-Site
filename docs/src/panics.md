# Checks and panics

Some mistakes can't be found until a program runs: an index past the end of an array, a sum too large for its type, a division by zero. Cella checks for these as the program runs, and when a check fails, the program panics: it stops with a message that says what went wrong and where. A program can also panic on purpose with a `panic` expression. What a panic does is decided by a `panic` operator that a library or the program itself declares.

## What a panic looks like

This program reads past the end of an array:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
pick: fun(index: usize) -> i32
{
	val values = [10, 20, 30]
	ret values[index]
}

main: fun
{
	printf("%d\n", pick(2))
	printf("%d\n", pick(3))
	printf("done\n")
}
```

```output
30
Panic at main.ce:11:6: index out of bounds
```

The second call fails the bounds check, so the program stops before it prints `done`. The message names the file, line and column of the checked expression, here `values[index]`.

The panic in this program comes from the standard library, which every project uses unless its `StandardLibrary` setting is `"Core"` or `"None"`. Its `panic` first flushes output the program has buffered, such as `printf`'s, then writes `Panic at`, the location and the message to standard error, and then ends the program as a crash, so the operating system's crash handling and an attached debugger see it.

## Checks at compile time

When the compiler can see that a check would fail, it reports an error instead of building a program that panics. This happens when the values involved are constants:

```cella error
~ mod example
~
Code: enum
{
	none
	first = 100
}

main: fun
{
	val values = [1, 2, 3]
	val a = values[5]
	val b = 10 / 0
	val c = i32(2147483647) + 1
	val d = u8(300)
	val e = Code(50)
}
```

```errors
Index 5 is out of range for 'array[i32, 3]'
Division by zero
Addition overflows 'i32'
'300' doesn't fit in 'u8'
'Code' has no case with the value 50
```

The rest of this chapter is about the checks that run, which are the ones on values the compiler doesn't know.

## The built-in checks

| Check | Message | Runs |
| --- | --- | --- |
| Indexing an array or a `str` | `index out of bounds` | with bounds checks |
| `+`, `-`, `*` on integers, and their compound assignments | `addition overflow`, `subtraction overflow`, `multiplication overflow` | with overflow checks |
| `-` on a signed integer | `negation overflow` | with overflow checks |
| A numeric conversion that loses information | `conversion overflow` | with overflow checks |
| Arithmetic on `char` past the last code point | `char overflow` | with overflow checks |
| Reading a `char` that isn't a valid code point | `invalid char` | with overflow checks |
| `/` and `%` by zero | `division by zero` | always |
| The smallest signed integer divided by `-1` | `division overflow` | always |
| An integer converted to an enum with no case for it | `'Code' has no case with this value` | always |
| A tagless enum case given a value it doesn't cover | `'Parity.odd' can't hold this value` | always |

Bounds checks are on in every build. Overflow checks are on in debug builds and off in release builds. Both can be changed in the project's settings, as [described below](#turning-checks-on-and-off).

### Bounds checks

Every index into an array or a `str` is checked against its length. Indexing a `str` reads a byte:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
byteAt: fun(text: str, index: usize) -> u8 => text[index]

main: fun
{
	printf("%c\n", byteAt("abc", 0))
	printf("%c\n", byteAt("abc", 3))
}
```

```output
a
Panic at main.ce:8:47: index out of bounds
```

Indexing through a pointer is never checked; see [Pointers](pointers.md#what-isnt-checked).

### Overflow checks

With overflow checks on, integer arithmetic whose result doesn't fit in its type panics instead of wrapping around, and so does a conversion `T(x)` whose value doesn't fit in the new type. [Numbers](numbers.md#overflow) shows both, along with the wrapping operators `+%`, `-%` and `*%`, which never panic.

Negating the smallest value of a signed type has no result that fits, so it panics too:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
flip: fun(value: i8) -> i8 => -value

main: fun
{
	printf("%d\n", flip(-127))
	printf("%d\n", flip(-128))
}
```

```output
127
Panic at main.ce:8:32: negation overflow
```

`char` holds a Unicode code point, so arithmetic that leaves the range of code points is `char overflow`, and converting an integer that isn't a code point to `char` is `conversion overflow`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
shift: fun(letter: char, by: i32) -> char => letter + by

main: fun
{
	printf("%c\n", shift('a', 2))
	printf("%c\n", shift(char(1114111), 1))
}
```

```output
c
Panic at main.ce:8:46: char overflow
```

A `char` read from a [union](unions.md) member whose bytes aren't a valid code point is `invalid char`.

### Division checks

Integer division and remainder by zero panic with `division by zero`, and dividing the smallest value of a signed type by `-1` panics with `division overflow`. Both checks run in every build. Float division by zero doesn't panic; it gives an infinity or a NaN. [Numbers](numbers.md#division-by-zero) has an example.

### Enum checks

Converting an integer to an enum checks that some case has that value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Level: enum
{
	low
	medium
	high
}

toLevel: fun(value: i32) -> Level => Level(value)

main: fun
{
	printf("%d\n", i32(toLevel(2)))
	printf("%d\n", i32(toLevel(7)))
}
```

```output
2
Panic at main.ce:15:38: 'Level' has no case with this value
```

A tagless enum (`enum match`) case lists the values it covers, and creating the case with any other value panics:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Digit: enum match u8
{
	even(value) = 0, 2, 4, 6, 8
	odd(value) = 1, 3, 5, 7, 9
	other(value) = else
}

makeOdd: fun(value: u8) -> Digit => Digit.odd(value)

main: fun
{
	val three = makeOdd(3)
	printf("%d\n", i32(three is odd(_)))
	makeOdd(4)
}
```

```output
1
Panic at main.ce:15:37: 'Digit.odd' can't hold this value
```

An `ext enum`, which mirrors a C enum, accepts every value of its tag type, so converting to one never panics. [Enums](enums.md#tagless-enums) and [Calling C](calling-c.md#ext-enum) cover both kinds.

## Turning checks on and off

Two project settings control the checks:

| Setting | Default | Controls |
| --- | --- | --- |
| `BoundsChecks` | `true` | index checks |
| `OverflowChecks` | `true` in debug builds, `false` in release builds | arithmetic, negation, conversion and `char` checks |

Division and enum checks don't depend on either setting.

With overflow checks off, integer arithmetic wraps around, integer conversions keep the low bits, float conversions saturate to the smallest or largest value of the type, and `char` values aren't checked. Built with `cella build --release`, this program wraps where a debug build would panic, but still stops at the division by zero:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
next: fun(value: u8) -> u8 => value + 1
toByte: fun(value: i32) -> u8 => u8(value)
toInt: fun(value: f64) -> i32 => i32(value)
share: fun(total: i32, people: i32) -> i32 => total / people

main: fun
{
	printf("%d %d %d\n", next(255), toByte(300), toInt(1e20))
	printf("%d\n", share(12, 0))
}
```

```options
--release
```

```output
0 44 2147483647
Panic at main.ce:11:47: division by zero
```

The setting overrides the build's default. This project turns overflow checks off in every build, debug builds included:

```celp group=wrapping
OutputType = "Executable"
OverflowChecks = false
```

```cella group=wrapping
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
next: fun(value: u8) -> u8 => value + 1
toByte: fun(value: i32) -> u8 => u8(value)
toInt: fun(value: f64) -> i32 => i32(value)

main: fun
{
	printf("%d %d %d\n", next(255), toByte(300), toInt(1e20))
}
```

```output
0 44 2147483647
```

`OverflowChecks = true` keeps the checks in release builds too. With `BoundsChecks = false`, an index past the end reads or writes whatever memory is there, as in C.

Each setting applies to the code of the project that sets it, so a library keeps its own checks whatever the program that uses it chooses. Code can test the same settings with the `boundsChecks` and `overflowChecks` flags in a `when` block; see [Conditional compilation](conditional-compilation.md#built-in-flags).

## Panicking on purpose

`panic` followed by a message stops the program the same way a failed check does:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
parseDigit: fun(c: char) -> i32
{
	if c < '0' || c > '9'
		panic "not a digit"

	ret i32(c) - i32('0')
}

main: fun
{
	printf("%d\n", parseDigit('7'))
	printf("%d\n", parseDigit('x'))
}
```

```output
7
Panic at main.ce:11:3: not a digit
```

`panic` is a keyword, not a function, so the message follows it without parentheses. The location in the message is where the `panic` is written. With the standard library's `panic`, the message is a `str`, and any `str` value works, not only a literal:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
fail: fun(reason: str) -> never => panic reason

main: fun
{
	printf("checking\n")
	fail("configuration missing")
}
```

```output
checking
Panic at main.ce:8:36: configuration missing
```

The location here is inside `fail`, since that is where the `panic` is.

The message is optional. A `panic` on its own stops the program with only the location:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
half: fun(value: i32) -> i32
{
	if value % 2 != 0
		panic

	ret value / 2
}

main: fun
{
	printf("%d\n", half(8))
	printf("%d\n", half(7))
}
```

```output
4
Panic at main.ce:11:3
```

### `panic` and `never`

A `panic` expression never produces a value, and its type is `never`. A path that reaches it ends there, like `ret`, so it can end a function that returns a value, or fill a `match` arm of any type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: enum
{
	triangle
	square
	circle
}

corners: fun(shape: Shape) -> i32 => match shape
{
	triangle => 3
	square => 4
	circle => panic "a circle has no corners"
}

main: fun
{
	printf("%d\n", corners(Shape.square))
	printf("%d\n", corners(Shape.circle))
}
```

```output
4
Panic at main.ce:19:12: a circle has no corners
```

A function that always panics, like `fail` above, is declared `-> never`. Calls to it end their path the same way. Its body must not return or reach its end:

```cella error
~ mod example
~
stop: fun(code: i32) -> never
{
	if code == 0
		panic "stopped"
}

main: fun
{
}
```

```errors
'stop' can reach its end
```

`never` is only a return type, so a `panic` can't be stored in a variable. [Functions](functions.md#functions-that-never-return) covers `-> never` in general.

## Declaring a panic operator

What a panic does is decided by `panic` operators, declared at the top level of a module in one of two forms:

- `panic: op(message: str, location: str) -> never` takes a message and the location.
- `panic: op(location: str) -> never` takes only the location.

The location is a `str` such as `main.ce:11:3` that gives the file's path in its project, the line and the column. Neither form may return. `panic expr` calls the form with a message, passing `expr`, and a bare `panic` calls the form without one. Built-in checks call the form with a message, passing their fixed messages, or the location-only form when it's the only one. A module can declare both, as the standard library does: they are overloads of one operator.

A project that doesn't use the standard library can declare its own. This one prints the panic to standard output and exits with code 3:

```celp group=own
OutputType = "Executable"
StandardLibrary = "None"
```

```cella group=own
~ mod example
~
ext
{
	printf: fun(format: cstr, ...) -> i32
	exit: fun(code: i32) -> never
}

panic: op(message: str, location: str) -> never
{
	printf("stopped at %.*s: %.*s\n", i32(location.byteLength), location.data, i32(message.byteLength),
		message.data)
	exit(3)
}

main: fun
{
	val values = [1, 2, 3]
	for i in 0..4
		printf("%d\n", values[usize(i)])
}
```

```output
1
2
3
stopped at main.ce:20:18: index out of bounds
```

A panic operator can use `when debug` and `when release` to behave differently in each build, for example exiting with a code in debug builds and crashing in release builds.

Each form must end with a `str` location and return `never`. The message's type is the operator's choice, but it must accept a `str`, since the built-in checks pass their messages as `str`:

```cella error
~ mod example
~
panic: op(message: i32, location: str) -> never
{
	loop
	{
	}
}

main: fun
{
}
```

```errors
'panic' operators need a message that accepts 'str'
```

```cella error
~ mod example
~
panic: op -> never
{
	loop
	{
	}
}

main: fun
{
}
```

```errors
'panic' operators need one or two parameters
```

```cella error
~ mod example
~
panic: op(message: str, location: i32) -> never
{
	loop
	{
	}
}

main: fun
{
}
```

```errors
'panic' operators need a 'str' location
```

```cella error
~ mod example
~
panic: op(message: str, location: str) -> i32 => 0

main: fun
{
}
```

```errors
'panic' operators must return 'never'
```

A `panic` operator belongs to a module, not to a type:

```cella error
~ mod example
~
Buffer: rec
{
	size: i32

	panic: op(message: str, location: str) -> never
	{
		loop
		{
		}
	}
}

main: fun
{
}
```

```errors
Cannot declare 'panic' operators in types
```

A message type other than `str` lets `panic` take other values. Here the operator is generic over any type with a `print` method, so `panic 42` works:

```cella group=generic
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	exit: fun(code: i32) -> never
~ }
~
Print: trait
{
	print: fun(imm self)
}

str: impl Print
{
	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
}

i32: impl Print
{
	print: fun(self) => printf("%d", self)
}

panic[T: Print]: op(imm message: T, location: str) -> never
{
	printf("stopped: ")
	message.print()
	printf("\n")
	exit(4)
}

main: fun
{
	printf("start\n")
	panic 42
}
```

```celp group=generic
OutputType = "Executable"
StandardLibrary = "None"
```

```output
start
stopped: 42
```

Traits and `impl` blocks are covered in [Traits](traits.md).

A message needs the form that takes one. Where only the location-only form is visible, `panic` with a message is an error:

```celp group=location
OutputType = "Executable"
StandardLibrary = "None"
```

```cella error group=location
~ mod example
~
panic: op(location: str) -> never
{
	loop
	{
	}
}

main: fun
{
	panic "stopped"
}
```

```errors group=location
'panic' doesn't accept a message
```

## Which panic a file uses

`panic` is an ordinary name, found like any other: a file uses the `panic` its module declares or that it imports. Built-in checks behave exactly like a `panic` written at the same spot, so they use the `panic` visible in the file where the checked code is written. A library's code keeps using its own `panic`, whichever program uses the library.

The standard library's `panic` is visible in every file of a project that uses the whole standard library. A project can make a library's `panic` visible in all its files with the [`Imports` setting](modules.md#project-imports), which imports names into every file:

```celp group=imports
OutputType = "Executable"
StandardLibrary = "None"
Imports = ["fault.panic"]

[[ProjectReferences]]
Path = 'fault/fault.celp'
```

```celp group=imports file=fault/fault.celp
OutputType = "StaticLibrary"
StandardLibrary = "None"
```

```cella group=imports file=fault/fault.ce
mod fault

ext
{
	printf: fun(format: cstr, ...) -> i32
	exit: fun(code: i32) -> never
}

panic: pub op(message: str, location: str) -> never
{
	printf("fault at %.*s: %.*s\n", i32(location.byteLength), location.data, i32(message.byteLength),
		message.data)
	exit(9)
}
```

```cella group=imports
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
divide: fun(a: i32, b: i32) -> i32 => a / b

main: fun
{
	printf("%d\n", divide(9, 3))
	printf("%d\n", divide(9, 0))
}
```

```output group=imports
3
fault at main.ce:8:39: division by zero
```

A `panic` can also be named through its module, as in `fault.panic "stopped"`, to use one that isn't imported.

Two wildcard imports that both bring in a `panic` make it ambiguous. The compiler reports it at each of the imports, since the file's checks would have no single `panic` to use:

```celp group=ambiguous
OutputType = "Executable"
StandardLibrary = "None"

[[ProjectReferences]]
Path = 'alpha/alpha.celp'

[[ProjectReferences]]
Path = 'beta/beta.celp'
```

```celp group=ambiguous file=alpha/alpha.celp
OutputType = "StaticLibrary"
StandardLibrary = "None"
```

```cella group=ambiguous file=alpha/alpha.ce
mod alpha

panic: pub op(message: str, location: str) -> never
{
	loop
	{
	}
}
```

```celp group=ambiguous file=beta/beta.celp
OutputType = "StaticLibrary"
StandardLibrary = "None"
```

```cella group=ambiguous file=beta/beta.ce
mod beta

panic: pub op(message: str, location: str) -> never
{
	loop
	{
	}
}
```

```cella error group=ambiguous
~ mod example
~
use alpha.*
use beta.*

main: fun
{
}
```

```errors group=ambiguous
'panic' is ambiguous
'panic' is ambiguous
```

When no `panic` is visible at all, as in a project without the standard library that declares none, failed checks still stop the program, but with no message: the program crashes at the failed check. A bare `panic` crashes the same way, and so does one when the only visible `panic` takes a message. With no `panic` visible, there is nowhere for a message to go, so `panic` with a message is an error there too: "'panic' doesn't accept a message".
