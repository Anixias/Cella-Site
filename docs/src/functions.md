# Functions

A function is a named piece of code that takes parameters and may return a result. This chapter covers declaring and calling functions, default values, overloading, functions that never return, the order arguments run in, and `main`, where a program starts.

## Declaring a function

A function is declared like everything else in Cella: a name, a colon, then what the name is. `fun` makes it a function. The parameters follow in parentheses, then `->` and the result type, then the body in braces:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
area: fun(width: i32, height: i32) -> i32
{
	ret width * height
}

main: fun
{
	printf("%d\n", area(3, 4))
}
```

```output
12
```

A call names the function and passes its arguments in parentheses, separated by commas. `ret` ends the function and gives back its result.

A function that takes no parameters leaves out the parentheses, as `main` does above. Empty parentheses, as in `answer: fun() -> i32`, are accepted too, and `--hints` reports them as redundant. A call always has parentheses, even when it passes nothing:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
answer: fun -> i32
{
	ret 42
}

main: fun
{
	printf("%d\n", answer())
}
```

```output
42
```

A function's name without them is a function value, covered in [Function values and closures](closures.md).

## Parameters

Each parameter has a name and a type, written `name: type`. Parameter names in one function must be different, and `_` names a parameter the body doesn't use:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
second: fun(_: i32, b: i32) -> i32
{
	ret b
}

main: fun
{
	printf("%d\n", second(1, 2))
}
```

```output
2
```

A parameter like these gets its own copy of the argument. The function can change it, and the caller's value stays as it was. Using one name for two parameters is an error:

```cella error
~ mod example
~
same: fun(a: i32, a: i32) -> i32
{
	ret a
}
~
~ main: fun
~ {
~ }
```

```errors
Parameter 'a' is declared more than once
Parameter 'a' is declared more than once
```

A parameter can also borrow its argument, with the modes `imm` and `mut` written before its name, and a parameter without a mode takes over a value that can't be copied. [Parameter modes](parameter-modes.md) covers them.

## Results and `ret`

The type after `->` is the function's result. Every path through the body must end in a `ret` with a value of that type, or in something that never finishes, such as an endless `loop`:

```cella error
~ mod example
~
sign: fun(n: i32) -> i32
{
	if n > 0
		ret 1
	else if n < 0
		ret -1
}

answer: fun -> i32
{
	ret
}
~
~ main: fun
~ {
~ }
```

```errors
Not all paths return a value
'answer' must return a value
```

A function without `->` returns nothing. Its body runs to its end, or to a `ret` with no value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
report: fun(count: i32)
{
	if count == 0
	{
		printf("nothing\n")
		ret
	}

	printf("%d items\n", count)
}

main: fun
{
	report(0)
	report(3)
}
```

```output
nothing
3 items
```

Such a function can't return a value, and a call to it can't be used as one:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
greet: fun
{
	printf("hi\n")
	ret 5
}

main: fun
{
	val x = greet()
}
```

```errors
Cannot return a value from 'greet'
'greet' doesn't return a value
```

A function with a result can be called as a statement, and its result is thrown away. That's how the examples in this documentation call `printf`, which returns an `i32`.

Code right after a `ret`, which can never run, gets the warning "Unreachable code".

## Expression bodies

When a function's body is a single expression, `=>` replaces the braces and the `ret`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
square: fun(n: i32) -> i32 => n * n

volume: fun(width: i64, height: i64, depth: i64) -> i64 =>
	width * height * depth

show: fun(n: i32) => printf("%d\n", n)

main: fun
{
	show(square(5))
	printf("%lld\n", volume(2, 3, 4))
}
```

```output
25
24
```

In a function with a result, the expression is the result. In a function without one, like `show`, the expression runs and its value, if any, is thrown away. A long expression wraps after `=>`, never before it.

The expression can be a `match`, with its arms on the lines below. [Pattern matching](pattern-matching.md) covers `match`.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
describe: fun(n: i32) -> cstr => match n
{
	0 => "zero"
	1..=9 => "small"
	else => "large"
}

main: fun
{
	printf("%s %s %s\n", describe(0), describe(7), describe(250))
}
```

```output
zero small large
```

## Default parameter values

A parameter can have a default value, written `= value` after its type. A call may leave out trailing parameters that have defaults:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
greet: fun(name: cstr = "world", times: i32 = 1)
{
	for _ in 0..times
		printf("hello, %s\n", name)
}

main: fun
{
	greet()
	greet("Ada")
	greet("Bob", 2)
}
```

```output
hello, world
hello, Ada
hello, Bob
hello, Bob
```

Arguments fill parameters from the left, so a call can't skip a parameter and pass a later one. The rules for defaults:

- A default must be a constant: a literal, a named `const`, an enum case, `null` or a function's name. It can't call a function.
- Every parameter after one with a default needs a default too.
- `mut` parameters can't have defaults, since they need a place to change.

```cella error
~ mod example
~
limit: fun -> i32 => 10

clamp: fun(value: i32, low: i32 = 0, high: i32) -> i32 => value

reset: fun(mut value: i32 = 0) => value = 0

cap: fun(value: i32, high: i32 = limit()) -> i32 => value
~
~ main: fun
~ {
~ }
```

```errors
Cannot take parameters without defaults after parameters with defaults
Cannot declare defaults for 'mut' parameters
The default value of 'high' must be a constant
```

Defaults belong to the declaration, not to the function's type. A call through a function value passes every argument:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
greet: fun(name: cstr = "world", times: i32 = 1) => printf("hello, %s\n", name)

main: fun
{
	val f = greet
	f("Ada")
}
```

```errors
'f' takes 2 arguments
```

## Overloading

Several functions can share a name if their parameters differ in number or in type. A call picks the one its arguments fit:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
show: fun(n: i32) => printf("i32 %d\n", n)
show: fun(n: i64) => printf("i64 %lld\n", n)
show: fun(n: f64) => printf("f64 %.1f\n", n)
show: fun(n: i32, width: i32) => printf("%*d\n", width, n)

main: fun
{
	val small: i16 = 7
	val count: u32 = 8
	show(5)
	show(small)
	show(count)
	show(2.5)
	show(5000000000)
	show(42, 6)
}
```

```output
i32 5
i32 7
i64 8
f64 2.5
i64 5000000000
    42
```

An argument that matches a parameter's type exactly is the best fit. Otherwise the argument converts, and a call prefers the overload whose conversions are cheapest: an `i16` reaches both `i32` and `i64`, and the narrower `i32` wins. A `u32` doesn't fit in an `i32`, so it goes to `i64`. A literal takes the type of the overload it fits best, so `5` is an `i32` and `5000000000`, too large for one, is an `i64`. [Conversions](conversions.md) lists which conversions happen implicitly.

When no overload is a better fit than the others, the call is ambiguous, and the error lists the candidates:

```cella error
~ mod example
~
pick: fun(a: i32, b: i64) -> i32 => 1
pick: fun(a: i64, b: i32) -> i32 => 2

main: fun
{
	val x: i16 = 1
	val y = pick(x, x)
}
```

```errors
Call to 'pick' is ambiguous
```

A call that fits no overload says so:

```cella error
~ mod example
~
scale: fun(n: i32) -> i32 => n * 2
scale: fun(n: i32, factor: i32) -> i32 => n * factor

main: fun
{
	val x = scale(1, 2, 3)
}
```

```errors
No overload of 'scale' accepts these arguments
```

### Overloads that conflict

Overloads must be told apart by the arguments of a call. Parameter names and result types don't count; parameter modes do, through the call's marks ([Parameter modes](parameter-modes.md#overloads-and-modes)). Two overloads also conflict when defaults let one call reach both. Each of these is an error on every declaration involved:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
area: fun(width: i32, height: i32) -> i32 => width * height
area: fun(w: i32, h: i32) -> i32 => w + h

parse: fun(text: cstr) -> i32 => 0
parse: fun(text: cstr) -> f64 => 0.0

log: fun(level: i32 = 0) => printf("level %d\n", level)
log: fun => printf("log\n")
~
~ main: fun
~ {
~ }
```

```errors
'area' is declared more than once with the same signature
'area' is declared more than once with the same signature
'parse' overloads cannot differ only in return type
'parse' overloads cannot differ only in return type
'log' overloads cannot accept the same arguments
'log' overloads cannot accept the same arguments
```

`log()` could call either `log`, so the default on the first one could never be used.

## Recursion and declaration order

A function can call itself, and functions can call each other. The order of declarations in a file doesn't matter: a function can call one declared below it, and `main` can come first or last.

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
	printf("%lld %d %d\n", factorial(10), isEven(10), isEven(7))
}

factorial: fun(n: i64) -> i64
{
	if n <= 1
		ret 1

	ret n * factorial(n - 1)
}

isEven: fun(n: i32) -> bool
{
	if n == 0
		ret true

	ret isOdd(n - 1)
}

isOdd: fun(n: i32) -> bool
{
	if n == 0
		ret false

	ret isEven(n - 1)
}
```

```output
3628800 1 0
```

The same holds across files: every function in a project can be used from anywhere the [module rules](modules.md) allow.

## Calling through a module

Every function belongs to the module named by its file's `mod` line. A function in another module is called through that module's name:

```cella group=geometry file=geometry.ce
mod geometry

area: fun(width: i32, height: i32) -> i32 => width * height
```

```cella group=geometry
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d\n", geometry.area(2, 3))
}
```

```output group=geometry
6
```

Without the module name, `area` isn't found from `example`, unless the file imports it with `use`. Code can name a function of its own module the same way. [Modules and visibility](modules.md) covers imports, nested modules and which declarations other modules can see.

## Functions that never return

A function whose result type is `never` doesn't return to its caller: it ends the program, or loops forever. C's `exit` is one, declared that way in an `ext` block:

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
	exit: fun(code: i32) -> never
}

fail: fun(message: cstr) -> never
{
	printf("error: %s\n", message)
	exit(1)
}

divide: fun(a: i32, b: i32) -> i32
{
	if b != 0
		ret a / b

	fail("division by zero")
}

main: fun
{
	printf("%d\n", divide(10, 2))
	divide(1, 0)
	printf("not printed\n")
}
```

```output
5
error: division by zero
```

`divide` has no `ret` after the call to `fail`, and it doesn't need one: since `fail` never returns, the compiler knows that path never reaches the end of `divide`. Code after a call to a `never` function gets the "Unreachable code" warning.

A `never` function can't `ret` at all, and no path may reach the end of its body. `never` is only a result type; parameters, variables and fields can't have it:

```cella error
~ mod example
~
ext
{
	abort: fun -> never
}

stop: fun(n: i32) -> never
{
	if n == 0
		ret

	abort()
}

falls: fun(n: i32) -> never
{
	if n == 0
		abort()
}

take: fun(value: never)
{
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot return from 'stop'
'falls' can reach its end
'never' can only be a return type
```

[Checks and panics](panics.md) covers `panic`, the usual way to stop a program with an error.

## Evaluation order

Arguments run from left to right, before the call. Operands of an operator run left to right too, whatever the operator's precedence:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
trace: fun(name: cstr, value: i32) -> i32
{
	printf("%s ", name)
	ret value
}

sum: fun(a: i32, b: i32, c: i32) -> i32 => a + b + c

main: fun
{
	val total = sum(trace("a", 1), trace("b", 2) + trace("c", 3) * trace("d", 4), trace("e", 5))
	printf("= %d\n", total)
}
```

```output
a b c d e = 20
```

Arguments passed with `mut` or `imm` reach their place at the call, after the other arguments have run. [Parameter modes](parameter-modes.md#evaluation-order) shows where that matters.

## The `main` function

A program starts in the function named `main`. A project that builds a program needs exactly one.

### Results and exit codes

`main` can return nothing, an `i32` or `never`:

- With no result, the program exits with code 0 when `main` ends.
- With `-> i32`, the value `main` returns is the program's exit code.
- With `-> never`, `main` never returns, and the program ends some other way, such as a call to C's `exit`.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
countErrors: fun -> i32 => 2

main: fun -> i32
{
	val errors = countErrors()
	if errors > 0
	{
		printf("%d errors\n", errors)
		ret 1
	}

	ret 0
}
```

```output
2 errors
```

This program exits with code 1.

### Command-line arguments

To read its command-line arguments, `main` takes a pointer to the first one and their count:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun(args: ptr[str], count: usize)
{
	for i in 1..count
	{
		val arg = args[i]
		printf("%zu: %.*s\n", i, i32(arg.byteLength), arg.data)
	}
}
```

```args
red green blue
```

```output
1: red
2: green
3: blue
```

Each argument is a `str`, UTF-8 text. The first one, at index 0, is the path of the program itself, so a program's own arguments start at index 1. [Pointers](pointers.md) covers `ptr[T]` and indexing through it, and [Bool, char and strings](text.md) covers `str`.

`main` can instead take one parameter of any type that can be built from that pointer and count, that is, one with a constructor taking a `ptr[str]` and a `usize`. A record with those two fields works, through its field-by-field constructor:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Arguments: rec
{
	items: ptr[str]
	count: usize
}

main: fun(args: Arguments)
{
	val last = args.items[args.count - 1]
	printf("%zu arguments, last %.*s\n", args.count - 1, i32(last.byteLength), last.data)
}
```

```args
red green blue
```

```output
3 arguments, last blue
```

A type with a destructor is taken by value or with `imm`, as in `main: fun(args: Arguments)`, and its destructor runs when `main` ends. [Records](records.md) covers constructors.

### Rules for `main`

`main` must have one of the shapes above, with no defaults, no type parameters and no `mut` parameter:

```cella error
~ mod example
~
main: fun(count: i32) -> i32
{
	ret count
}
```

```errors
'main' must take no parameters, 'ptr[str]' and 'usize', or one parameter that meets 'new(ptr[str], usize)'
```

```cella error
~ mod example
~
main: fun -> i64
{
	ret 0
}
```

```errors
'main' must return 'i32', 'never' or nothing
```

```cella error
~ mod example
~
main: fun -> i32 => 0

main: fun(args: ptr[str], count: usize) -> i32 => 1
```

```errors
The program has more than one 'main' function
The program has more than one 'main' function
```

A program with no `main` at all fails with "The program has no 'main' function".

## Starting somewhere else with `--entry`

`cella build` and `cella run` take `--entry` with a function's full name, module first. The program then starts in that function instead of `main`:

```cella norun
~ mod tools
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
selfTest: pub fun -> i32
{
	printf("self test\n")
	ret 2
}

main: fun
{
	printf("main\n")
}
```

```sh
cella run
cella run --entry tools.selfTest
```

The first command prints `main` and exits with 0. The second prints `self test` and exits with 2.

The entry function must be `pub`, take no parameters, have no type parameters, and return `i32`, `never` or nothing, like `main`. The project then doesn't need a `main`, and one that exists is ignored, whatever its shape. [Projects and building](projects.md) covers the build commands and their options.
