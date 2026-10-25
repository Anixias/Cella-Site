# Generics

A generic declaration takes types as parameters. One generic function or record works for every type you give it, and the compiler builds a separate copy of it for each type it's used with. This chapter covers generic functions, records and enums, the constraints that say which types a parameter accepts, value parameters, which take compile-time integers instead of types, and defaults for both.

## Generic functions

Type parameters go in brackets after the function's name. Inside the function, a type parameter is a type like any other:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
pick[T]: fun(useFirst: bool, a: T, b: T) -> T
{
	if useFirst
		ret a

	ret b
}

main: fun
{
	val number = pick(true, 1, 2)
	val ratio = pick(false, 1.5, 2.5)
	val text = pick[cstr](true, "yes", "no")
	printf("%d %.1f %s\n", number, ratio, text)
}
```

```output
1 2.5 yes
```

`pick` takes its values without a mode, so it gets them by value: a copy for a `T` that copies, and the value itself for one that has to move. Generic code that keeps using a `T` after passing it on needs every `T` to be copyable, which the type parameter says with `T: copy` (see [Constraints](#constraints)). See [Parameter modes](parameter-modes.md) for what `imm` and `mut` mean.

## Type arguments

A call can write its type arguments in brackets, as `pick[cstr]` does above. Usually it doesn't need to: the compiler infers them from the arguments, and when the arguments don't settle them, from the type the call's result is expected to have:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
identity[T]: fun(value: T) -> T => value

main: fun
{
	val a = identity(5)
	val b: i64 = identity(6)
	val c = identity[u8](7)
	printf("%zu %zu %zu\n", sizeOf(a), sizeOf(b), sizeOf(c))
}
```

```output
4 8 1
```

When several arguments share a type parameter, the type they all convert to wins. A literal fits whatever type the other arguments give it, and two integer types widen to the larger one:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ pick[T]: fun(useFirst: bool, a: T, b: T) -> T
~ {
~ 	if useFirst
~ 		ret a
~
~ 	ret b
~ }
~
main: fun
{
	val small: i32 = 3
	val large: i64 = 4000000000
	val wide = pick(false, small, large)
	val mixed = pick(true, 1, 2.5)
	printf("%lld %.1f\n", wide, mixed)
}
```

```output
4000000000 1.0
```

Here `wide` is an `i64` and `mixed` is an `f64`. When nothing settles a type parameter, or the arguments disagree, or the call writes the wrong number of type arguments, the call is an error:

```cella error
~ mod example
~
make[T]: fun -> usize => sizeOf(T)

same[T]: fun(a: T, b: T) -> i32 => 0

main: fun
{
	val a = make()
	val b = same(1, true)
	val c = make[i32, i64]()
}
```

```errors
Cannot infer 'T' for 'make'
Cannot convert type 'integer literal' to 'bool'
'make' takes one generic argument
```

## How generic bodies are checked

A generic body is checked once, where it's declared, against what every possible `T` allows, so its errors show up there and not at the calls. Without constraints, that means generic code can move a `T`, borrow it, store it in fields and arrays, point to it and ask for `sizeOf(T)`, but it can't call methods or operators on it:

```cella error
~ mod example
~
add[T]: fun(imm value: T) -> T => value + 1

main: fun
{
	val x = add(2)
}
```

```errors
No operation defined for '+' between 'T' and 'integer literal'
```

Calling `add(2)` with an `i32` doesn't help, since the body has to work for every type. To use operators and methods on a `T`, give it a [trait bound](traits.md).

Each type a generic is used with gets its own compiled copy, with its own layout and code. A generic function that calls itself with a bigger type each time would need endless copies, which is an error:

```cella error
~ mod example
~
Box[T]: rec
{
	value: T
}

nest[T]: fun(value: T, depth: i32) -> i32
{
	if depth == 0
		ret 0

	ret nest(Box(value), depth - 1)
}

main: fun
{
	val levels = nest(1, 3)
}
```

```errors
Instantiating 'nest' never ends
```

## Generic and plain overloads

A generic function can share its name with plain functions and other generic ones. A call goes to the plain overload when the argument already has the type its parameter takes. Otherwise the generic overload, which takes any type as it is, wins over a plain one that would need a conversion:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
describe: fun(value: i32) -> cstr => "plain"

describe[T]: fun(imm value: T) -> cstr => "generic"

main: fun
{
	val small: u8 = 4
	printf("%s %s %s\n", describe(5), describe(imm small), describe(true))
}
```

```output
plain generic generic
```

`describe(imm small)` passes the `u8` to the generic overload rather than converting it to an `i32`. Overloads follow the usual rules from [Functions](functions.md). Two generic overloads that differ only in the names of their type parameters have the same signature:

```cella error
~ mod example
~
same[T]: fun(imm x: T) -> i32 => 1
same[U]: fun(imm x: U) -> i32 => 2
~
~ main: fun
~ {
~ }
```

```errors
'same' is declared more than once with the same signature
'same' is declared more than once with the same signature
```

## Generic records

Records take type parameters the same way. Fields, constructors, methods and destructors can all use them. A type argument can be written, as in `Pair[u8, bool]`, or inferred from the constructor's arguments:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Pair[A, B]: rec
{
	first: A
	second: B

	swapped: fun(self) -> Pair[B, A] => Pair(self.second, self.first)
}

main: fun
{
	val p = Pair(1, 2.5)
	val q = Pair[u8, bool](7, true)
	val r = p.swapped()
	printf("%d %.1f | %d %d | %.1f %d\n", p.first, p.second, q.first, q.second, r.first, r.second)
	printf("%zu %zu\n", sizeOf(Pair[u8, bool]), sizeOf(Pair[i64, u8]))
}
```

```output
1 2.5 | 7 1 | 2.5 1
2 16
```

Each instantiation is its own type with its own layout, as the sizes show: a `Pair[u8, bool]` takes 2 bytes and a `Pair[i64, u8]` takes 16.

Static functions and static fields are reached through an instantiation, as in `Counted[i32].made`. Every instantiation has its own copy of each static field:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Counted[T]: rec
{
	value: T
	made: var i32 = 0

	new: op(value: T)
	{
		self.value = value
		made += 1
	}
}

main: fun
{
	Counted(1)
	Counted(2)
	Counted(true)
	printf("%d %d %d\n", Counted[i32].made, Counted[bool].made, Counted[f64].made)
}
```

```output
2 1 0
```

## Generic methods

A method or static function can take type parameters of its own, beside its type's. Here `map` turns a `Cell[T]` into a `Cell[U]`, with `U` inferred from the function it's given or written out:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Cell[T]: rec
{
	value: T

	map[U]: fun(self, imm change: fun[T -> U]) -> Cell[U] => Cell(change(self.value))
}

half: fun(value: i32) -> f64 => f64(value) / 2.0

main: fun
{
	val whole = Cell(5)
	val halved = whole.map(half)
	val tripled = whole.map[i64](fun(value) => value * 3)
	printf("%.1f %lld\n", halved.value, tripled.value)
}
```

```output
2.5 15
```

Function types and lambdas are covered in [Function values and closures](closures.md).

## Generic enums

Enums take type parameters too, which is how an optional value or a result can be written once for every type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Option[T]: enum
{
	none
	some(value: T)

	isSome: fun(imm self) -> bool => self is some(_)
}

find: fun(values: array[i32, 4], target: i32) -> Option[usize]
{
	for i in 0..values.length
	{
		if values[i] == target
			ret some(i)
	}

	ret none
}

main: fun
{
	val values = [4, 8, 15, 16]
	val found = find(values, 15)
	val missing = find(values, 3)
	if found is some(val index)
		printf("found at %zu\n", index)

	printf("%d %d\n", found.isSome(), missing.isSome())
	val explicit = Option[f64].some(0.5)
	val inferred = Option.some(true)
	printf("%zu %zu\n", sizeOf(explicit), sizeOf(inferred))
}
```

```output
found at 2
1 0
16 2
```

Where the enum type is known, as in `ret some(i)`, a bare case name is enough. A case can name its arguments, as in `Option[f64].some(0.5)`, or leave them to be inferred, as in `Option.some(true)`. Cases and matching are covered in [Enums](enums.md) and [Pattern matching](pattern-matching.md).

## Constraints

A constraint after a type parameter's name limits the types it accepts, and in return lets the generic code do more with it. `[T: copy]` accepts only types that can be copied, so the body can copy a `T`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Pair[T]: rec
{
	a: T
	b: T
}

Point: rec
{
	x: i32
	y: i32
}

twin[T: copy]: fun(value: T) -> Pair[T] => Pair(value, value)

main: fun
{
	val numbers = twin(7)
	val points = twin(Point(1, 2))
	printf("%d %d %d\n", numbers.a, numbers.b, points.b.y)
}
```

```output
7 7 2
```

A type argument that doesn't meet a constraint is an error where it's used. Inside other generic code, a type parameter meets a constraint only if its own constraints say so:

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

twin[T: copy]: fun(value: T) -> i32 => 1

forward[T]: fun(imm value: T) -> i32 => twin(value)

main: fun
{
	twin(Token(1))
}
```

```errors
'twin' requires 'T: copy'
'twin' requires 'T: copy'
```

Several constraints are joined with `+`, as in `[T: copy + noref]`. Each one can appear only once in a list, and some can't be combined:

```cella error
~ mod example
~
both[T: copy + drop]: fun -> i32 => 0

twice[T: copy + copy]: fun -> i32 => 0
~
~ main: fun
~ {
~ }
```

```errors
Cannot combine 'copy' and 'drop'
Cannot combine 'copy' and 'drop'
'copy' is required more than once
'copy' is required more than once
```

The constraints are:

| Constraint | Accepts |
| --- | --- |
| `copy` | types that can be copied |
| `noref` | types that hold no borrows |
| `drop` | types with a destructor |
| `default` | types whose all-zero value is valid |
| `new`, `new(...)` | types with a matching constructor |
| `null` | types that have a `null` value |
| `ext` | types that can cross into C |
| `atomic` | types the target can access atomically |
| a trait | types that implement the trait |
| `const` and a trait | types with an `impl const` of the trait |
| a function type | functions and closures of that type |

`ext` is covered in [Calling C](calling-c.md), `atomic` in [Atomics](atomics.md), trait bounds in [Traits](traits.md), `const` bounds in [Constant functions](constant-functions.md#constant-implementations-and-bounds) and function types as constraints in [Function values and closures](closures.md).

### copy

A type can be copied when it isn't declared `own` and everything it holds can be copied (see [Ownership and destructors](ownership.md)). `T: copy` lets a `val` copy a `T` and lets the code use a `T` after passing it on.

### noref

A type holds borrows when it is a borrow type like `imm[i32]`, a `str`, a `ref rec` or `ref enum`, or anything that contains one (see [Borrows](borrows.md#records-that-hold-borrows)). `T: noref` accepts only types that hold none, which a container that keeps its values needs. Without it, a type parameter may hold borrows, so it can't be passed on to something that requires `noref`:

```cella error
~ mod example
~
Holder[T: noref]: rec
{
	value: T
}

Wrapper[T]: rec
{
	inner: Holder[T]
}

main: fun
{
	val count = 5
	val a = Holder(count)
	val b = Holder(imm count)
}
```

```errors
'Holder' requires 'T: noref'
'Holder' requires 'T: noref'
```

`Holder(imm count)` would make a `Holder[imm[i32]]`, which holds a borrow.

### drop

`T: drop` accepts only types with a destructor, written or inherited from a field:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Text: own rec
{
	id: i32

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

Labeled: own rec
{
	text: Text
	count: i32
}

hold[T: drop]: fun(value: T)
{
	printf("holding\n")
}

main: fun
{
	hold(Text(1))
	hold(Labeled(Text(2), 5))
}
```

```output
holding
drop 1
holding
drop 2
```

```cella error
~ mod example
~
hold[T: drop]: fun(value: T)
{
}

main: fun
{
	hold(5)
}
```

```errors
'hold' requires 'T: drop'
```

### default

`T: default` accepts types that have a legal default: types whose all-zero memory is a valid value, as [Records](records.md) describes. The body can then declare a `T` without a value, which starts as zeros, and call `T()`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Vec2: rec
{
	x: f32
	y: f32
}

zeroed[T: default]: fun -> T
{
	var value: T
	ret value
}

main: fun
{
	printf("%d %.1f %d\n", zeroed[i32](), zeroed[Vec2]().y, zeroed[bool]())
}
```

```output
0 0.0 0
```

Without the constraint, a `T` declared without a value has to be assigned before it's read, and a type without a legal default doesn't meet it:

```cella error
~ mod example
~
Fixed: rec
{
	n: i32

	new: op(n: i32)
	{
		self.n = n
	}
}

zeroed[T: default]: fun -> T
{
	var value: T
	ret value
}

blank[T]: fun -> T
{
	var value: T
	ret value
}

main: fun
{
	val f = zeroed[Fixed]()
}
```

```errors
Cannot use uninitialized values
'zeroed' requires 'T: default'
```

### new

`T: new` asks for a constructor without parameters, and `T: new(usize)` for one that takes a `usize`; the generic code then calls it as `T()` or `T(64)`. A type meets it with a declared constructor that takes exactly those parameter types, or, when it declares no constructor, with its field-by-field constructor or, for `new`, with `T()`. Built-in conversions count too, so `f64` meets `new(usize)`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Buffer: rec
{
	size: usize

	new: op
	{
		self.size = 16
	}

	new: op(size: usize)
	{
		self.size = size
	}
}

Point: rec
{
	x: i32
	y: i32
}

make[T: new]: fun -> T => T()

sized[T: new(usize)]: fun -> T => T(64)

main: fun
{
	val a = make[Buffer]()
	val b = sized[Buffer]()
	val p = make[Point]()
	val c = sized[f64]()
	printf("%zu %zu %d %.1f\n", a.size, b.size, p.x, c)
}
```

```output
16 64 0 64.0
```

The parameter list can name several types and give each one a mode, as in `new(i32, i32)`, `new(imm T)` or `new(Text, mut i32)`. Calls pass arguments the way the modes say. A type that has no such constructor doesn't meet the constraint:

```cella error
~ mod example
~
Fixed: rec
{
	n: i32

	new: op(n: i32)
	{
		self.n = n
	}
}

make[T: new]: fun -> T => T()

sized[T: new(usize)]: fun -> T => T(64)

main: fun
{
	val a = make[Fixed]()
	val b = sized[bool]()
}
```

```errors
'make' requires 'T: new'
'sized' requires 'T: new(usize)'
```

`T: new` doesn't promise that zeros are a valid `T`. A generic body that declares a `T` without a value needs `T: default` instead.

### null

`T: null` accepts types that have a `null` value, such as pointers and `cstr`. The generic code can then use `null` as a `T` and compare a `T` with it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
empty[T: null]: fun -> T => null

isEmpty[T: null]: fun(imm value: T) -> bool => value == null

main: fun
{
	var x = 5
	val p: ptr[i32] = empty()
	val text = empty[cstr]()
	printf("%d %d %d\n", isEmpty(imm p), isEmpty(imm text), isEmpty(@x))
}
```

```output
1 1 0
```

```cella error
~ mod example
~
Nullable[T: null]: rec
{
	value: T
}

main: fun
{
	val n: Nullable[i32] = undef
}
```

```errors
'Nullable' requires 'T: null'
```

## Value parameters

A value parameter takes a compile-time integer instead of a type. It's declared with `const` before its name and an integer type after it, as in `const length: usize`, and inside the declaration it's a constant: it can size an array, appear in expressions, or be passed on as another generic's argument. Like a type parameter, it's inferred from the arguments or written out:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
sum[const length: usize]: fun(values: array[i32, length]) -> i32
{
	var total = 0
	for value in values
		total += value

	ret total
}

zeros[const length: usize]: fun -> array[i32, length]
{
	var result: array[i32, length]
	ret result
}

main: fun
{
	printf("%d %d\n", sum([1, 2, 3]), sum([10, 20, 30, 40, 50]))
	val four = zeros[4]()
	val two: array[i32, 2] = zeros()
	printf("%zu %zu\n", four.length, two.length)
}
```

```output
6 150
4 2
```

Each value gets its own compiled copy, as each type does. Records and enums take value parameters too, mixed with type parameters in any order. A value argument can be any constant expression, such as a named constant times 2:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
capacity: const usize = 4

Stack[T: noref, const size: usize]: rec
{
	items: array[T, size]
	count: usize

	push: fun(mut self, value: T)
	{
		self.items[self.count] = value
		self.count += 1
	}

	isFull: get(imm self) -> bool => self.count == size
}

main: fun
{
	var small = Stack[i32, 2]()
	small.push(1)
	small.push(2)
	var large = Stack[f64, capacity * 2]()
	large.push(0.5)
	printf("%d %d %zu\n", small.isFull, large.isFull, sizeOf(Stack[u8, 8]))
}
```

```output
1 0 16
```

A value parameter must have an integer type, and the value given must fit it. Inside a generic argument, a value parameter must stand alone: `array[i32, length]` works, but `array[i32, length + 1]` doesn't, while expressions of plain constants, like `capacity * 2`, still do. A value parameter isn't a type, and a type isn't a value:

```cella error
~ mod example
~
grow[const length: usize]: fun(values: array[i32, length]) -> array[i32, length + 1] => undef

Ratio[const scale: f64]: rec
{
	value: i32
}

Small[const count: u8]: rec
{
	items: array[i32, count]
}

misuse[const count: usize]: fun -> usize
{
	val x: count = 1
	ret count
}

main: fun
{
	val a = Small[300]()
	val b = Small[i32]()
}
```

```errors
Cannot use arithmetic on value parameters in generic arguments
Value parameters need an integer type
'count' is not a type
'300' doesn't fit in 'u8'
'i32' is not a constant
```

## Default arguments

A type or value parameter can name a default after `=`. Arguments left off the end of the list take their defaults, so a parameter that most uses don't change doesn't have to be written each time:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Pair[K, V = K]: rec
{
	key: K
	value: V
}

Buffer[T, const capacity: usize = 8]: rec
{
	items: array[T, capacity]
	count: usize
}

main: fun
{
	val same = Pair[i32](1, 2)
	val mixed = Pair[i32, bool](3, true)
	printf("%d %d %zu %zu\n", same.value, mixed.value, sizeOf(Buffer[u8]), sizeOf(Buffer[u8, 64]))
}
```

```output
2 1 16 72
```

`Pair[i32]` is `Pair[i32, i32]`: a default can use the parameters before it, but not itself or the ones after it. Parameters with defaults come last. A type whose parameters all have defaults is written by its name alone, so `Name` here is `Name[Utf8]`. `Name[]` means the same and gets a "Redundant '[]'" hint:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Ascii: rec

Utf8: rec

Name[Encoding = Utf8]: rec
{
	length: usize
}

measure: fun(name: Name) -> usize => name.length

main: fun
{
	val short = Name(4)
	val plain = Name[Ascii](6)
	printf("%zu %zu\n", measure(short), plain.length)
}
```

```output
4 6
```

Defaults work the same way for functions and methods. A method's default can use its type's parameters too. Inference comes first: a default only fills a parameter that neither the arguments nor the expected type settles. Here `Cell(5)` is a `Cell[i32]`, since the literal settles `T`, while the declared type of `written` makes it a `Cell[i64]`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Cell[T = i64]: rec
{
	value: T
}

parse[T: default = i64]: fun -> T
{
	var value: T
	ret value
}

main: fun
{
	val inferred = Cell(5)
	val written: Cell = Cell(5)
	val plain = parse()
	val chosen: i16 = parse()
	printf("%zu %zu %zu %zu\n", sizeOf(inferred), sizeOf(written), sizeOf(plain), sizeOf(chosen))
}
```

```output
4 8 8 2
```

A default must meet its parameter's constraints, which is checked where it's declared. Messages leave out trailing arguments that are the same as their defaults, as the last error shows:

```cella error
~ mod example
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Plain: rec
{
	value: i32
}

Late[T = i32, U]: rec
{
	a: T
	b: U
}

Forward[T = U, U = i32]: rec
{
	a: T
}

Checked[T: Eq = Plain]: rec
{
	a: T
}

Pair[K, V = K]: rec
{
	key: K
	value: V
}

main: fun
{
	val many: Pair[i32, i32, i32] = undef
	val pair: Pair[i32] = Pair[i32, bool](1, true)
}
```

```errors
Cannot take parameters without defaults after parameters with defaults
Cannot use 'U' in defaults of earlier parameters
'Checked' requires 'T: Eq'
'Pair' takes 1 or 2 generic arguments
Cannot convert type 'Pair[i32, bool]' to 'Pair[i32]'
```

Two overloads that a call can reach the same way, with or without the defaulted argument, are an error:

```cella error
~ mod example
~
first[T]: fun(value: T) -> i32 => 1
first[T, U = i32]: fun(value: T) -> i32 => 2
~
~ main: fun
~ {
~ }
```

```errors
'first' overloads cannot accept the same arguments
'first' overloads cannot accept the same arguments
```

## Types with the same name

Types can share a name when their parameter lists differ, either in how many arguments they take or in whether an argument is a type or a value. The same goes for traits. A type and a trait can't share a name.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Size: rec
{
	value: i32
}

Size[T]: rec
{
	value: T
}

Grid[T]: rec
{
	cell: T
}

Grid[const count: usize]: rec
{
	cells: array[i32, count]
}

main: fun
{
	val plain = Size(1)
	val typed = Size[u8](2)
	val cell = Grid[bool](true)
	val cells = Grid[3]([1, 2, 3])
	printf("%d %d %zu %zu\n", plain.value, i32(typed.value), sizeOf(cell), sizeOf(cells))
}
```

```output
1 2 1 12
```

The arguments pick the declaration: `Grid[bool]` is the one that takes a type and `Grid[3]` the one that takes a value. The name alone means the declaration that takes no arguments, counting one whose parameters all have defaults. With no such declaration, the name needs arguments, even where only one declaration could fit. An impl block picks its type the same way, so `Size: impl Shape` and `Size[T]: impl Shape` implement it for different types. Importing a name brings in every declaration with that name.

Two declarations that could take the same arguments are an error, whether they have the same parameters or only overlap through defaults:

```cella error
~ mod example
~
Pair[A]: rec
{
	first: A
}

Pair[A, B]: rec
{
	first: A
	second: B
}

Box[T]: rec

Box[T, Tag = i32]: rec

main: fun
{
	val one = Pair(1)
	val many = Pair[i32, i32, i32](1, 2, 3)
}
```

```errors
'Box' declarations cannot take the same generic arguments
'Box' declarations cannot take the same generic arguments
'Pair' needs generic arguments
No 'Pair' takes 3 generic arguments
```

## Adding members under bounds

An `impl` block on a generic type with stronger constraints adds members that exist only for the instantiations that meet them. A block can also name a concrete instantiation, so its members exist only for that one type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Pair[T]: rec
{
	a: T
	b: T
}

Pair[T: copy]: impl
{
	swapped: fun(self) -> Pair[T] => Pair(self.b, self.a)
}

Pair[i32]: impl
{
	sum: fun(self) -> i32 => self.a + self.b
}

main: fun
{
	val p = Pair(3, 4)
	val q = p.swapped()
	val r = Pair(1.5, 2.5).swapped()
	printf("%d %d %d %.1f\n", q.a, q.b, p.sum(), r.a)
}
```

```output
4 3 7 2.5
```

Inside `Pair[T: copy]: impl`, the body knows `T: copy`, so `self` can be copied. Using a member on an instantiation that doesn't meet the block's constraints is an error at the use. In the type's own module, a block that adds no constraints to the declaration's is an error, since those members belong in the type's own body:

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

Pair[T]: rec
{
	a: T
	b: T
}

Pair[T: copy]: impl
{
	swapped: fun(self) -> Pair[T] => Pair(self.b, self.a)
}

Pair[i32]: impl
{
	sum: fun(self) -> i32 => self.a + self.b
}

Pair[T]: impl
{
	first: fun(imm self) -> imm[T] => imm self.a
}

main: fun
{
	val tokens = Pair(Token(1), Token(2))
	val swapped = tokens.swapped()
	val total = Pair(1.5, 2.5).sum()
}
```

```errors
Cannot declare 'impl' blocks that add no bounds
'swapped' requires 'T: copy'
Type 'Pair[f64]' has no member 'sum'
```

A block in the type's own module can also declare constructors. Like its other members, they exist only for the instantiations that meet the block. This lets a type offer a shorter constructor where a parameter's value can start as zeros:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Tagged[T, Tag]: rec
{
	value: T
	tag: Tag

	new: op(value: T, tag: Tag)
	{
		self.value = value
		self.tag = tag
	}
}

Tagged[T, Tag: default]: impl
{
	new: op(value: T)
	{
		var tag: Tag
		self.value = value
		self.tag = tag
	}
}

main: fun
{
	val named = Tagged(5, 9)
	val plain = Tagged[i32, u8](6)
	printf("%d %d %d %d\n", named.value, named.tag, plain.value, plain.tag)
}
```

```output
5 9 6 0
```

A constructor in a block counts as declaring a constructor, so the type loses its built-in constructors for every instantiation, as [Records](records.md#constructors) describes. Calling a block's constructor on an instantiation that doesn't meet the block is an error at the call. A block names every parameter of its type, including the ones with defaults:

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

~ Tagged[T, Tag]: rec
~ {
~ 	value: T
~ 	tag: Tag
~
~ 	new: op(value: T, tag: Tag)
~ 	{
~ 		self.value = value
~ 		self.tag = tag
~ 	}
~ }
~
~ Tagged[T, Tag: default]: impl
~ {
~ 	new: op(value: T)
~ 	{
~ 		var tag: Tag
~ 		self.value = value
~ 		self.tag = tag
~ 	}
~ }
~
Pair[K, V = K]: rec
{
	key: K
	value: V
}

Pair[K: copy]: impl
{
	first: fun(self) -> K => self.key
}

main: fun
{
	val tagged = Tagged[i32, Token](6)
}
```

```errors
'Pair' takes 2 generic arguments
'new' requires 'Tag: default'
```

A block can also name a generic type inside its target and declare that type's parameters there. Its members then exist for every instantiation of that shape, and the body can use the inner parameters like any other:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Pair[T]: rec
~ {
~ 	a: T
~ 	b: T
~ }
~
Box[T]: rec
{
	value: T
}

Pair[Box[Item: copy]]: impl
{
	unboxed: fun(self) -> Pair[Item] => Pair(self.a.value, self.b.value)
}

main: fun
{
	val boxes = Pair(Box(3), Box(4))
	val numbers = boxes.unboxed()
	printf("%d %d\n", numbers.a, numbers.b)
}
```

```output
3 4
```

The inner parameters must meet the inner type's constraints, and like the block's other parameters they can't have defaults.

Blocks like these most often add members under a [trait bound](traits.md). Blocks that implement a trait, and blocks outside the type's own module, are covered in [Traits](traits.md).
