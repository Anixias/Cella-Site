# Variables and constants

Variables hold values a program works with. This chapter covers the three kinds of declaration, `val`, `var` and `const`, how a variable's type is chosen, variables that start without a value, assignment, scopes, and variables and constants declared at module level.

## val and var

`val` declares a variable that can't be changed after it gets its value. `var` declares one that can:

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
	val width = 4
	var total = 0
	total = width * 3
	total = total + 1
	printf("%d %d\n", width, total)
}
```

```output
4 13
```

Assigning to a `val`, or to any part of one such as a field of a record or an element of an array, is an error:

```cella error
~ mod example
~
Point: rec
{
	x: i32
	y: i32
}

main: fun
{
	val limit = 5
	limit = 6
	val origin = Point(0, 0)
	origin.x = 1
	val values = [1, 2, 3]
	values[0] = 4
}
```

```errors
Cannot reassign values
Cannot reassign values
Cannot reassign values
```

Use `val` unless the variable needs to change. A `var` that is never changed gets a hint saying so, shown when the build is given `--hints` (see [Projects and building](projects.md)):

```text
Hint at main.ce:5:6
4 │ {
5 │     var count = 1
            ╘═══╛ 'count' is never changed
```

## Types

A type annotation after the name, separated by a colon, says what type the variable has. The value must convert to it:

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
	val small: u8 = 200
	val wide: i64 = 7
	val ratio: f32 = 0.25
	printf("%d %lld %.2f\n", small, wide, ratio)
}
```

```output
200 7 0.25
```

```cella error
~ mod example
~
main: fun
{
	val ready: bool = 1
}
```

```errors
Cannot convert type 'integer literal' to 'bool'
```

[Numbers and arithmetic](numbers.md) covers the number types and which literals fit in them, and [Conversions](conversions.md) covers which values convert to which types.

### Inferred types

Without an annotation, the variable takes the type of its initial value. A value that already has a type, such as the result of a call or another variable, gives it that type.

A literal on its own, like `10` or `0.5`, doesn't have a fixed type yet. A variable that starts from one takes its type from how the variable is used later in the function. When nothing decides it, an integer literal makes an `i32` and a float literal an `f64`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
half: fun(value: i64) -> i64 => value / 2

main: fun
{
	val count = 10
	val ratio = 0.5
	val total = 7
	printf("%lld\n", half(total))
	var level = 0
	val step: u16 = 3
	level = step
	printf("%zu %zu %zu %zu\n", sizeOf(count), sizeOf(ratio), sizeOf(total), sizeOf(level))
}
```

```output
3
4 8 8 2
```

`count` and `ratio` are only printed, so they keep the default types. `total` is passed where an `i64` is expected, so it is an `i64`. `level` is given a `u16`, so it is a `u16`.

The rules are:

- Where the variable is read as a certain type, such as an argument or the value of a typed variable, it takes that type. When it's read as several types, it takes the one of them that converts to all the others.
- Values assigned to it must convert to that type.
- A variable that is only assigned to takes the type that all the assigned values convert to.

When no type works, the declaration is an error that lists the types that disagree:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
wide: fun(value: u16) -> i32 => 0
signed: fun(value: i16) -> i32 => 0

main: fun
{
	val count = 7
	wide(count)
	signed(count)
}
```

```errors
Cannot infer the type of 'count' from 'u16' and 'i16'
```

A declaration needs a type or a value. With neither, there is nothing to take a type from:

```cella error
~ mod example
~
main: fun
{
	var total
}
```

```errors
Cannot infer the type of 'total'
```

## Variables without a value

A `var` declared with a type and no value starts as all zeros, when zeros are a valid value of its type. That holds for numbers, `bool`, pointers, arrays of such values, and records made of them that don't declare their own constructors:

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

main: fun
{
	var count: i32
	var ready: bool
	var origin: Point
	var grid: array[i32, 3]
	count += 1
	grid[1] = 5
	printf("%d %d %d %d %d %d\n", count, ready, origin.x, origin.y, grid[0], grid[1])
}
```

```output
1 0 0 0 0 5
```

A type whose values are made by its own constructors has no zero value of its own (see [Records](records.md)). A variable of that type starts uninitialized, and it must be assigned before it's used:

```cella error
~ mod example
~
Celsius: rec
{
	degrees: f64

	new: op(degrees: f64)
	{
		self.degrees = degrees
	}
}

main: fun
{
	var room: Celsius
	val reading = room.degrees
}
```

```errors
Cannot use uninitialized values
```

### Assigning a val later

A `val` declared without a value gets it from a later assignment. Every path through the function must assign it exactly once before it's read. Here the paths are the two branches of an `if` ([Control flow](control-flow.md) covers `if`):

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
describe: fun(score: i32) -> i32
{
	val bonus: i32
	if score > 50
		bonus = 10
	else
		bonus = 0

	ret score + bonus
}

main: fun
{
	printf("%d %d\n", describe(70), describe(20))
}
```

```output
80 20
```

Reading it before it's assigned, reading it when only some paths assign it, and assigning it twice are errors:

```cella error
~ mod example
~
early: fun -> i32
{
	val x: i32
	ret x
}

maybe: fun(flag: bool) -> i32
{
	val x: i32
	if flag
		x = 1

	ret x
}

twice: fun -> i32
{
	val x: i32
	x = 1
	x = 2
	ret x
}

main: fun
{
}
```

```errors
Cannot use uninitialized values
Cannot use uninitialized values
Cannot reassign values
```

The last error also points at the first assignment, with a note "Assigned on line" and its line number.

### undef

`undef` as the initial value leaves a variable uninitialized on purpose, even when its type has a zero value. It saves the cost of zeroing storage that is about to be filled anyway:

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
	var squares: array[i32, 4] = undef
	for i in 0..4
		squares[i] = i32(i * i)

	printf("%d %d\n", squares[1], squares[3])
}
```

```output
1 9
```

The compiler checks that `undef` storage is written before it's read:

```cella error
~ mod example
~
main: fun
{
	var count: i32 = undef
	count += 1
}
```

```errors
Cannot use uninitialized values
```

`var x = undef` without a type takes its type from later uses, like a variable that starts from a literal. `undef` is only allowed as the initial value of a variable:

```cella error
~ mod example
~
take: fun(value: i32)
{
}

main: fun
{
	take(undef)
}
```

```errors
Cannot use 'undef' outside variable initializers
```

[Pointers and raw memory](pointers.md) shows how to fill `undef` storage through a pointer.

## Assignment

`=` stores a new value in a variable, a field or an array element. The compound assignments `+=`, `-=`, `*=`, `/=`, `%=` and the others combine an operator with assignment: `total += 4` is `total = total + 4`, with `total` evaluated once. [Numbers and arithmetic](numbers.md) lists them all.

An assignment is also an expression. Its value is the variable after the assignment, so assignments can be chained and used as arguments:

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
	var x = 0
	var y = 0
	x = y = 10
	var count = 1
	printf("%d %d %d\n", x, y, count += 4)
	printf("%d\n", count)
}
```

```output
10 10 5
5
```

Assignment groups from the right, so `x = y = 10` assigns `10` to `y` and then `y` to `x`. Assigning a new value to a variable whose old value has a destructor runs that destructor; [Ownership and destructors](ownership.md) covers that.

## Constants

`const` declares a constant: a value computed while compiling. Its initial value must be built from literals, other constants and operators on them:

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
	const rows = 3
	const cells = rows * 4
	val grid: array[i32, cells] = undef
	printf("%zu\n", grid.length)
}
```

```output
12
```

Constants can be used where a value must be known while compiling, such as the length of an array type. A `val` can't, even when its value is a literal: a `val` is storage that holds a value at run time, and a constant isn't.

```cella error
~ mod example
~
main: fun
{
	val rows = 3
	val grid: array[i32, rows] = undef
}
```

```errors
'rows' is not a constant
```

A constant needs a value, the value must be a constant, and its type can't have a destructor:

```cella error
~ mod example
~
Buffer: own rec
{
	id: i32

	drop: op
	{
	}
}

main: fun
{
	val n = 2
	const m = n + 1
	const later: i32
	const handle = Buffer(1)
}
```

```errors
The initial value of 'm' must be a constant
Cannot declare constants without values
Cannot store values with destructors in constants
```

A constant has no address, so `@` can't be applied to it (see [Pointers and raw memory](pointers.md)):

```text
Cannot take the address of constants
```

## Scopes

A variable can be used from its declaration to the end of the block it's declared in. A block is a list of statements in `{ }`, such as a function body, the body of an `if` or a loop, or a block written on its own:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	{
		val inner = 1
		printf("%d\n", inner)
	}

	printf("%d\n", inner)
}
```

```errors
Symbol 'inner' not found in this scope
```

When a block ends, its variables are dropped, in the reverse order of their declarations. [Ownership and destructors](ownership.md) covers what that means for values with destructors.

### Shadowing

A variable in an inner block may have the same name as one outside it. Inside the block, the name means the inner variable. After the block, it means the outer one again. The inner variable doesn't have to have the same type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
double: fun(value: i32) -> i32
{
	val value = value * 2
	ret value
}

main: fun
{
	val x = 1
	{
		val x = "inner"
		printf("%s\n", x)
	}

	printf("%d %d\n", x, double(4))
}
```

```output
inner
1 8
```

A function's body is a block inside its parameters, so a variable in the body can reuse a parameter's name, as `double` does. The new variable's initial value still sees the old name, since the new one only starts after its declaration.

Two variables with the same name in the same block are an error, reported at both:

```cella error
~ mod example
~
main: fun
{
	var total = 1
	var total = 2
}
```

```errors
'total' is declared more than once in this scope
'total' is declared more than once in this scope
```

## Module-level variables and constants

Variables and constants can also be declared at the top of a file, outside any function. They are written like other declarations, with the name first: `name: var Type = value`, `name: val Type = value` or `name: const Type = value`. The type and the value are both required. Every function in the module can use them:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
maxPlayers: const i32 = 4
startingLives: val i32 = 3
joined: var i32 = 0

join: fun -> i32
{
	joined += 1
	ret joined
}

main: fun
{
	join()
	join()
	printf("%d of %d, %d lives\n", joined, maxPlayers, startingLives)
}
```

```output
2 of 4, 3 lives
```

- A `const` is a constant, as inside a function.
- A `val` is storage that can't be written.
- A `var` is storage that any function can change. It lives for the whole run of the program.

Their initial values are set before the program starts, so each one must be a constant, for a `var` and a `val` too:

```cella error
~ mod example
~
~ ext
~ {
~ 	rand: fun -> i32
~ }
~
seed: var i32 = rand()
lives: val i32 = 3
doubled: val i32 = lives * 2

main: fun
{
}
```

```errors
The initial value of 'seed' must be a constant
The initial value of 'doubled' must be a constant
```

Declaration order doesn't matter at module level. A constant can use one declared further down, as long as no constant depends on its own value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
doubled: const i32 = base * 2
base: const i32 = 3

main: fun
{
	printf("%d\n", doubled)
}
```

```output
6
```

```cella error
~ mod example
~
first: const i32 = second + 1
second: const i32 = first + 1

main: fun
{
}
```

```errors
'first' depends on its own value
'second' depends on its own value
```

A local variable may have the same name as a module-level one. Inside its scope, the name means the local variable.

Module-level declarations can be made visible to other modules or projects; [Modules and visibility](modules.md) covers that. Constants and variables declared inside a type belong to the type; [Methods and properties](methods.md) covers them.
