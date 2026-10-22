# Calling C

Cella calls C functions directly, with no wrappers or generated bindings: you declare a C function's signature in Cella types, and calls to it follow the platform's C calling convention. The same works the other way, so C code can call Cella functions and read Cella globals. Everything that crosses between the two languages is marked with the `ext` keyword.

## `ext` blocks

An `ext` block declares functions that are defined in C. Each member is a name and a signature, with no body:

```cella
~ mod example
~
ext
{
	puts: fun(text: cstr) -> i32
	abs: fun(value: i32) -> i32
	strlen: fun(text: cstr) -> usize
}

main: fun
{
	puts("hello from C")
	if abs(-3) == 3 && strlen("four") == 4
		puts("both right")
}
```

```output
hello from C
both right
```

These three come from the C runtime, which every program links. Functions from other libraries need the library named, as [Linking](#linking) describes.

The declarations are ordinary module names: a module can have any number of `ext` blocks, and code in any of its files can call them. A block with a single member can drop the braces, as in `ext puts: fun(text: cstr) -> i32`.

The signature must be complete. Every parameter needs a name and a type, and the result follows `->` as for any function; a C function that returns `void` has no `->`. A body is an error, since the function is defined elsewhere:

```cella error
~ mod example
~
ext
{
	abs: fun(value: i32) -> i32 => value
	labs: fun(value) -> i32
}

main: fun
{
}
```

```errors
Cannot declare bodies for 'ext' functions
Expected ':' and a type
```

`ext` functions can't be overloaded. Two declarations with one name are an error on each of them:

```cella error
~ mod example
~
ext
{
	abs: fun(value: i32) -> i32
	abs: fun(value: i64) -> i64
}

main: fun
{
}
```

```errors
'ext' functions cannot be overloaded
'ext' functions cannot be overloaded
```

A C function that never returns, such as `exit` or `abort`, is declared `-> never`, and calls to it end their path like `ret`:

```cella
~ mod example
~
ext
{
	puts: fun(text: cstr) -> i32
	exit: fun(code: i32) -> never
}

check: fun(ready: bool) -> i32
{
	if ready
		ret 1

	puts("not ready")
	exit(0)
}

main: fun
{
	check(true)
	check(false)
	puts("unreachable")
}
```

```output
not ready
```

### Visibility

Like other top-level declarations, the names in an `ext` block are visible to the whole project. A visibility word in front of the block applies to every member: `pvt ext { ... }` keeps them in one file, `mod ext { ... }` in the module, and `pub ext { ... }` lets projects that reference this one call them, as in `lib.abs(-3)`. Visibility words can't appear inside the block:

```cella error
~ mod example
~
ext
{
	pvt
	{
		strlen: fun(text: cstr) -> usize
	}
}

main: fun
{
}
```

```errors
Cannot use 'pvt' in 'ext' blocks
```

[Modules and visibility](modules.md) covers the visibility levels.

## C types in Cella

Each C type has a Cella type with the same size and layout:

| C | Cella |
| --- | --- |
| `signed char`, `unsigned char` | `i8`, `u8` |
| `short`, `unsigned short` | `i16`, `u16` |
| `int`, `unsigned int` | `i32`, `u32` |
| `long long`, `unsigned long long` | `i64`, `u64` |
| `long`, `unsigned long` | `i32`, `u32` on Windows; `i64`, `u64` on Linux |
| `size_t`, `ptrdiff_t` | `usize`, `isize` |
| `float`, `double` | `f32`, `f64` |
| `bool` | `bool` |
| `const char*` to a zero-terminated string | `cstr` |
| `void*` | `ptr` |
| `T*` | `ptr[T]` |
| `struct` | `rec` |
| `union` | `union` |
| `enum` | `ext enum` |
| function pointer | `ext fun[...]` |
| `__int128` | `i128` |

`ptr[T]` points to a `T` and `ptr` points to anything; [Pointers](pointers.md) covers both. A C function with a variable argument list, such as `printf`, ends its parameters with `...`; [Variadic functions](variadics.md#c-variadics) covers what can be passed through it.

## Renaming with `ext("name")`

A declaration takes the C name from its own name. `ext("name")` before `fun` gives the C name separately, so the Cella name can follow Cella's style or avoid a clash:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	printLine: ext("puts") fun(text: cstr) -> i32
	absolute: ext("llabs") fun(value: i64) -> i64
}

main: fun
{
	printLine("renamed")
	printf("%lld\n", absolute(-5000000000))
}
```

```output
renamed
5000000000
```

The C name must be a plain identifier:

```cella error
~ mod example
~
ext
{
	dotted: ext("app.counter") fun -> i32
	blank: ext("") fun -> i32
}

main: fun
{
}
```

```errors
Cannot use 'app.counter' as an 'ext' name
Cannot use empty 'ext' names
```

### Several signatures for one C function

Since the C name and the Cella name are separate, one C function can be declared several times with different Cella signatures, in one module or in several. Each call uses the signature of the declaration it calls. This is how a C function that takes a `void*` can be given typed parameters for each use:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Point: rec
{
	x: i32
	y: i32
}

ext
{
	clearBytes: ext("memset") fun(target: ptr[array[u8, 4]], value: i32, count: usize) -> ptr
	clearPoint: ext("memset") fun(target: ptr[Point], value: i32, count: usize) -> ptr
}

main: fun
{
	var bytes: array[u8, 4] = [1, 2, 3, 4]
	var point = Point(5, 6)
	clearBytes(@bytes, 0, 4)
	clearPoint(@point, 0, sizeOf(Point))
	printf("%d %d %d\n", bytes[3], point.x, point.y)
}
```

```output
0 0 0
```

## Strings

C strings are pointers to zero-terminated bytes, and Cella's type for them is `cstr`. A string literal converts to a `cstr` where one is expected, with the terminating zero added. A `cstr` can also be `null`, which C functions often return to mean "not found":

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	strchr: fun(text: cstr, c: i32) -> cstr
	getenv: fun(name: cstr) -> cstr
}

main: fun
{
	val rest = strchr("hello world", 119)
	printf("%s\n", rest)
	val missing = strchr("hello", 122)
	printf("%d\n", i32(missing == null))
	printf("%d\n", i32(getenv("NO_SUCH_VARIABLE_HERE") == null))
}
```

```output
world
1
1
```

A `cstr` has no length, so indexing one reads a byte without a bounds check, and it has no arithmetic. Cella's own string type, `str`, holds a pointer and a length and can't be passed to C; its `data` property gives the pointer to its bytes. [Bool, char and strings](text.md#cstr) covers both types.

## Records and unions

A record crosses into C by value with the same layout as a C `struct` with the same fields in the same order, and a [union](unions.md) crosses like a C `union`. C's `div` returns a struct of two `int`s:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Quotient: rec
{
	quot: i32
	rem: i32
}

ext
{
	div: fun(numerator: i32, denominator: i32) -> Quotient
}

main: fun
{
	val result = div(17, 5)
	printf("%d remainder %d\n", result.quot, result.rem)
}
```

```output
3 remainder 2
```

C functions that take a pointer to fill in can be declared with a `ptr[T]` parameter and called with `@x`, or declared with a `mut` parameter and called with `mut x`, which passes the address the same way. An `imm` parameter passes the address of a value C only reads. C's `modf` splits a number and stores the whole part through its second parameter:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	modf: fun(value: f64, mut whole: f64) -> f64
	strlen: fun(imm text: array[u8, 8]) -> usize
}

main: fun
{
	var whole = 0.0
	val fraction = modf(3.75, mut whole)
	printf("%.1f %.2f\n", whole, fraction)

	val text: array[u8, 8] = [104, 105, 0, 0, 0, 0, 0, 0]
	printf("%zu\n", strlen(imm text))
}
```

```output
3.0 0.75
2
```

An array can't be passed by value, as in C. Pass its address with `imm`, `mut` or a pointer instead. [Parameter modes](parameter-modes.md) covers `imm` and `mut`.

## `ext enum`

A C enum isn't limited to its named values: C code can store any integer in one, and new versions of a library add values. A plain Cella `enum` can only hold its own cases, so it can't cross into C. An `ext enum` is the open version: any value of its tag type is valid, named or not.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Status: ext enum
{
	success = 0
	notReady
	timeout
	outOfMemory = -1
}

describe: fun(status: Status) -> cstr => match status
{
	success => "success"
	timeout => "timeout"
	else => "other"
}

main: fun
{
	val code = -1000
	val unknown = Status(code)
	printf("%s %s %s\n", describe(Status.timeout), describe(unknown), describe(Status(-1)))
	printf("%d %d\n", i32(unknown), i32(sizeOf(Status)))
}
```

```output
timeout other other
-1000 4
```

Converting an integer to an `ext enum` never fails, and a `match` on one must have an `else` arm even when it names every case:

```cella error
~ mod example
~
Status: ext enum
{
	success
	failed
}

main: fun
{
	val status = Status.success
	val code = match status { success => 0, failed => 1 }
}
```

```errors
This match doesn't handle every value of 'Status'
```

The tag is an `i32`, like a C `enum`, unless written `ext enum(T)` with another integer type. The default value is the one whose bits are all zero, whether or not a case has it. Constant values must fit in the tag type:

```cella error
~ mod example
~
Format: ext enum(u8)
{
	rgba8 = 37
	bgra8 = 44
}

main: fun
{
	val wide = Format(300)
}
```

```errors
'300' doesn't fit in 'u8'
```

Cases can carry payloads, as in a plain enum. An `ext enum` with payloads is laid out like the C struct `{ T tag; union { ... } payloads; }`, which matches C APIs that pass events as a tag and a union:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Event: ext enum(u32)
{
	quit = 0x100
	keyDown(key: i32, repeat: bool) = 0x300
	click(x: i32, y: i32) = 0x400
}

handle: ext fun(event: Event) -> i32 => match event
{
	keyDown(val key, _) => key
	click(val x, val y) => x + y
	else => 0
}

main: fun
{
	printf("%d %d %d\n", handle(Event.keyDown(65, false)), handle(Event.click(2, 3)), i32(sizeOf(Event)))
}
```

```output
65 5 12
```

`ext` goes before `enum`, and an `ext enum` keeps its Cella name; `ext("name")` is an error on it. There are no `ext rec` declarations: every record already has C's layout.

[Enums](enums.md) covers what `ext enum` shares with plain enums: case values, payloads and matching.

## Callbacks with `ext fun`

`ext fun[A, B -> R]` is the type of a C function pointer: a function that takes an `A` and a `B`, returns an `R`, and uses the C calling convention. A function declared in an `ext` block is one, and so is a Cella function declared with `ext fun` and a body; any other Cella function named directly converts to one. C's `qsort` takes one to compare elements:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	qsort: fun(items: ptr, count: usize, size: usize, compare: ext fun[ptr, ptr -> i32])
}

descending: ext fun(left: ptr, right: ptr) -> i32
{
	val a = *ptr[i32](left)
	val b = *ptr[i32](right)
	if a < b
		ret 1
	if a > b
		ret -1
	ret 0
}

main: fun
{
	var values = [5, 3, 9, 1, 7]
	qsort(@values, 5, sizeOf(i32), descending)
	printf("%d %d %d %d %d\n", values[0], values[1], values[2], values[3], values[4])
}
```

```output
9 7 5 3 1
```

A lambda works too, as long as it captures nothing, since a C function pointer has nowhere to keep captured values:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	qsort: fun(items: ptr, count: usize, size: usize, compare: ext fun[ptr, ptr -> i32])
}

main: fun
{
	var values = [5, 3, 9, 1]
	qsort(@values, 4, sizeOf(i32), fun(a, b) => *ptr[i32](a) - *ptr[i32](b))
	printf("%d %d %d %d\n", values[0], values[1], values[2], values[3])
}
```

```output
1 3 5 9
```

```cella error
~ mod example
~
ext
{
	qsort: fun(items: ptr, count: usize, size: usize, compare: ext fun[ptr, ptr -> i32])
}

main: fun
{
	var values = [5, 3, 9, 1]
	val sign = -1
	qsort(@values, 4, sizeOf(i32), fun(a, b) => sign * (*ptr[i32](a) - *ptr[i32](b)))
}
```

```errors
Cannot capture 'sign' in 'ext fun[ptr, ptr -> i32]'
```

`ext fun` values can be stored in variables, fields and arrays and called like functions. An `ext fun` converts to the matching Cella function type `fun[...]`, but a `fun` value doesn't convert to an `ext fun`, since it may be a closure:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	abs: fun(value: i32) -> i32
}

twice: ext fun(value: i32) -> i32 => value * 2

Handler: rec
{
	callback: ext fun[i32 -> i32]
	argument: i32
}

main: fun
{
	val handlers = [Handler(abs, -4), Handler(twice, 21)]
	for handler in handlers
		printf("%d\n", handler.callback(handler.argument))

	val plain: fun[i32 -> i32] = twice
	printf("%d\n", plain(5))
}
```

```output
4
42
10
```

`ext fun` declarations with bodies can't be members of a type, and an `ext fun` value can't be `null`. A C API whose callback is optional can be declared with a tagless enum over the function type, whose `none` case is the null pointer. C's `signal` takes and returns such a callback:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Optional[T: null]: enum match T
{
	none = null
	some(value) = else
}

ext
{
	signal: fun(number: i32, handler: Optional[ext fun[i32]]) -> Optional[ext fun[i32]]
	raise: fun(number: i32) -> i32
}

caught: var i32 = 0

onSignal: ext fun(number: i32)
{
	caught = number
}

main: fun
{
	val previous = signal(2, some(onSignal))
	raise(2)
	printf("%d %d\n", caught, i32(previous is none))
}
```

```output
2 1
```

[Enums](enums.md#tagless-enums) covers tagless enums, and [Function values and closures](closures.md) covers function types in general.

## The `T: ext` constraint

A type parameter can appear in an `ext` signature, by value, behind a pointer or in an `ext fun` type, only when it has the `ext` constraint. `T: ext` means `T` can cross into C, and every type argument is checked for it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Point: rec
{
	x: i32
	y: i32
}

call[T: ext]: fun(f: ext fun[T -> i32], value: T) -> i32 => f(value)

twice: ext fun(x: i32) -> i32 => x * 2
sum: ext fun(p: Point) -> i32 => p.x + p.y

main: fun
{
	printf("%d %d\n", call(twice, 21), call(sum, Point(3, 4)))
}
```

```output
42 7
```

Without the constraint, the signature is rejected:

```cella error
~ mod example
~
call[T]: fun(f: ext fun[T -> i32], imm value: T) -> i32 => f(value)

main: fun
{
}
```

```errors
Cannot use 'T' in 'ext' signatures
```

A type that can't cross into C can't be the type argument:

```cella error
~ mod example
~
Token: own rec
{
	id: i32

	drop: op
	{
	}
}

call[T: ext]: fun(f: ext fun[T -> i32], value: T) -> i32 => f(value)

main: fun
{
	call[Token](undef, Token(1))
}
```

```errors
'call' requires 'T: ext'
```

The error's note says why: "'Token' can't be used in 'ext' signatures". Types that cross into C can always be copied and never hold borrows, so a `T: ext` meets `copy` and `noref` bounds, and `ext` can't be combined with `drop`.

## What can't cross into C

C knows nothing about Cella's ownership, borrows, traits or closures, so types that depend on them can't appear in `ext` signatures. That covers `ext` block members, `ext fun` definitions and `ext fun` types, and every field, element and payload of the types they use:

- types with destructors, since C would copy them bit by bit and never drop them
- plain `enum`s, since C can hand back a value that isn't a case
- `str`, borrow types (`imm[T]`, `mut[T]`) and records that hold borrows
- Cella function types (`fun[...]`, `ref fun[...]` and owned closures), trait objects (`dyn[...]`) and templates (`fstr[...]`)
- arrays by value

```cella error
~ mod example
~
Buffer: own rec
{
	data: ptr

	drop: op
	{
	}
}

Holder: own rec
{
	buffer: Buffer
	count: i32
}

Team: enum
{
	red
	blue
}

ext
{
	write: fun(text: str) -> i32
	release: fun(buffer: Buffer)
	keep: fun(holder: Holder)
	pick: fun -> Team
	sort: fun(imm compare: fun[i32, i32 -> i32])
	fill: fun(values: array[i32, 4])
}

main: fun
{
}
```

```errors
Cannot use 'str' in 'ext' signatures
Cannot use types with destructors in 'ext' signatures
Cannot use types with destructors in 'ext' signatures
Cannot use plain enums in 'ext' signatures
Cannot use 'fun[i32, i32 -> i32]' in 'ext' signatures
Cannot use 'array[i32, 4]' in 'ext' signatures
```

When the problem is inside a field, the error's note names it, as in "'Holder' contains 'Buffer'". A pointer to a type with a destructor can cross, since C only passes the address along: `keep: fun(holder: ptr[Holder])` is fine.

## Exporting Cella to C

A Cella function declared `ext fun` with a body uses the C calling convention, so C can call it through a pointer, as `qsort` called `descending` above. To give it a symbol that C code can link against by name, make it `pub`: a `pub ext fun` gets a plain C symbol with its own name, or with the name in `ext("name")`. Globals work the same way with `ext val` and `ext var`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
scale: pub ext("scale_value") fun(value: i32) -> i32 => value * 10
triple: pub ext fun(value: i32) -> i32 => value * 3
hits: pub ext("hit_count") var i32 = 2

ext
{
	scaleThroughC: ext("scale_value") fun(value: i32) -> i32
	tripleThroughC: ext("triple") fun(value: i32) -> i32
	hitsThroughC: ext("hit_count") var i32
}

main: fun
{
	hitsThroughC += 1
	printf("%d %d %d\n", scaleThroughC(4), tripleThroughC(5), hits)
}
```

```output
40 15 3
```

The `ext` block here imports the program's own exports by their C names, the way C code would see them. An `ext var` or `ext val` in an `ext` block declares a C global and has no initializer; one defined at the top level has one. An `ext val` always lives in memory, so C can read it, and its value is never folded into the code that uses it.

`pub` items of executables and shared libraries are exported, so a program can export functions for plugins it loads, and a shared library's `pub ext fun`s can be called from C. Other `pub` items keep Cella's own symbol names, which include the module, so overloads and equal names in different modules stay apart. Two `ext` definitions with the same C name in one program, `pub` or not, are an error on each of them. An `ext fun` that isn't `pub` still uses the C calling convention, and with `ext("name")` it still defines that symbol for C code linked into the same program, but nothing outside the program sees it.

The rules for `ext` signatures apply to exported functions and globals too:

```cella error
~ mod example
~
Team: enum
{
	red
	blue
}

current: ext var Team = Team.red

main: fun
{
}
```

```errors
Cannot use plain enums in 'ext' signatures
```

## Linking

An `ext` block with a library name, `ext("name") { ... }`, takes its functions from that library, and the build links it:

- On Windows, the name is an import or static library, `name.lib`, found in the project's folder or the linker's library paths. `ext("user32")` links `user32.lib`, which makes the program load `user32.dll`.
- On Linux, the name `m` means `libm.so` or `libm.a`, found in the project's folder or the system's library paths.

A name can be a path relative to the project's folder, such as `ext("lib/bin/plugin")`. Without a name, functions come from the C runtime and the system libraries that every program links. Since library names differ between systems, a [`when` block](conditional-compilation.md#when-blocks) picks the right one:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
when windows
{
	ext("kernel32")
	{
		processId: ext("GetCurrentProcessId") fun -> u32
	}
}
else
{
	ext
	{
		processId: ext("getpid") fun -> i32
	}
}

main: fun
{
	printf("%d\n", i32(processId() > 0))
}
```

```output
1
```

A missing library and a missing function are both reported at their declarations:

```cella error
~ mod example
~
ext("no_such_library")
{
	missing: fun -> i32
}

main: fun
{
	missing()
}
```

```errors
Cannot find the library 'no_such_library'
```

```cella error
~ mod example
~
ext
{
	no_such_function: fun -> i32
}

main: fun
{
	no_such_function()
}
```

```errors
Cannot find 'no_such_function' in the linked libraries
```

### Linking the C runtime

On Windows, programs built with Visual Studio's tools link the C runtime either as a DLL or into the program itself. The `SystemLinkPreference` setting picks one: `"Dynamic"`, the default, uses the DLL, and `"Static"` copies the runtime into the program, so it runs without the runtime installed:

```celp
OutputType = "Executable"
SystemLinkPreference = "Static"
```

Every part of a program has to use the same C runtime, so a program that links it statically can't use a shared library project, and a library used by several programs that link it differently is an error. [Project settings](project-settings.md#systemlinkpreference) lists the setting with the others.
