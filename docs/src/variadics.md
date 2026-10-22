# Variadic functions

A variadic function takes any number of arguments in its last position. Cella has two kinds. C variadics, written `...` in an `ext` declaration, follow C's calling convention, as `printf` does. Typed variadics, written `...name: T`, convert every extra argument to one element type, and the function receives them all as one value.

## C variadics

An `ext` function whose parameter list ends in `...` takes any number of extra arguments after its fixed ones:

```cella
mod example

ext
{
	printf: fun(format: cstr, ...) -> i32
}

main: fun
{
	val count = 3
	val ratio = 0.75
	printf("%d items, %.2f full\n", count, ratio)
	printf("no extra arguments\n")
}
```

```output
3 items, 0.75 full
no extra arguments
```

The C function finds out how many arguments it got and what types they have from its fixed arguments, here the format string. Nothing checks that the format matches the arguments, as in C.

A bare `...` needs at least one parameter before it:

```cella error
mod example

ext
{
	report: fun(...) -> i32
}

main: fun
{
}
```

```errors
Expected a parameter before '...'
```

### Promotions

Extra arguments follow C's default promotions. Integers narrower than 32 bits and `bool` are widened to a 32-bit `int`, and `f32` is widened to `f64`. Every other integer up to 64 bits, `f64`, `char`, pointers and `cstr` are passed as they are. An integer literal that fits in an `i32` is passed as one, and a float literal as an `f64`.

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
	val small: u8 = 250
	val negative: i16 = -1000
	val half: f32 = 0.5
	val big: i64 = 5000000000
	printf("%d %d %d %.1f %lld\n", small, negative, true, half, big)
}
```

```output
250 -1000 1 0.5 5000000000
```

So `%d` reads a `u8`, `i16` or `bool`, and `%f` reads an `f32`, as in C.

Values of `ext enum` types are passed as their integer values, and `ext fun` values as function pointers; [Calling C](calling-c.md) covers both.

### What can't be passed

Other types can't go through `...`: `i128` and `u128`, `str`, records, arrays, enums that aren't `ext`, and Cella function values are errors.

```cella error
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
	val name: str = "Cella"
	val point = Point(1, 2)
	val huge: i128 = 1
	printf("%s %d %d\n", name, point, huge)
}
```

```errors
Cannot pass 'str' values to variadic functions
Cannot pass 'Point' values to variadic functions
Cannot pass 'i128' values to variadic functions
```

Pass the parts C understands instead. A `str` goes to `%.*s` as its length and its data pointer, and a record goes field by field:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Point: rec
~ {
~ 	x: i32
~ 	y: i32
~ }
~
main: fun
{
	val name: str = "Cella"
	val point = Point(1, 2)
	printf("%.*s (%d, %d)\n", i32(name.byteLength), name.data, point.x, point.y)
}
```

```output
Cella (1, 2)
```

### Only in `ext` declarations

A bare `...` belongs to C functions declared in `ext` blocks. A Cella function can't take one, and neither can an `ext fun` written in Cella for C to call:

```cella error
~ mod example
~
log: fun(format: cstr, ...)
{
}

callback: ext fun(format: cstr, ...) -> i32 => 0

main: fun
{
}
```

```errors
Expected a parameter name
Expected a parameter name
```

Cella functions take typed variadics instead.

## Typed variadics

A typed variadic parameter is written with `...` before its name, as the last parameter. Its type collects the extra arguments:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
View[T]: ref rec
{
	data: ptr[T]
	length: usize

	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
}

sum: fun(...values: View[i32]) -> i32
{
	var total = 0
	for i in 0..values.length
		total += values[i]

	ret total
}

main: fun
{
	printf("%d %d %d\n", sum(), sum(5), sum(1, 2, 3, 4))
}
```

```output
0 5 10
```

At each call, the compiler stores the extra arguments in a temporary array and builds the parameter from the array's address and its length. The parameter's type can be any type with a constructor that takes a `ptr[T]` and a `usize`, the constraint `new(ptr[T], usize)` from [Generics](generics.md); its `T` is the element type. Cella has no built-in type for this, so the program declares one. `View` here is a record holding a pointer and a count. Its field-by-field constructor takes exactly those two values, and its `[]` [operator](operators.md) reads one element. Declaring it as a `ref rec` makes the compiler check that a `View` never outlives the arguments it points to; [Borrows](borrows.md) explains how. The examples below use this `View` without showing it again.

The type must meet that constraint exactly once:

```cella error
~ mod example
~
Bytes: rec
{
	new: op(data: ptr[u8], length: usize)
	{
	}

	new: op(data: ptr[i8], length: usize)
	{
	}
}

plain: fun(...values: i32)
{
}

bytes: fun(...values: Bytes)
{
}

main: fun
{
}
```

```errors
'i32' doesn't meet 'new(ptr[T], usize)'
'Bytes' meets 'new(ptr[T], usize)' more than once
```

### Arguments

Each extra argument is converted to the element type, the way the elements of an array literal are. A literal that doesn't fit is an error:

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
bytes: fun(...values: View[u8])
{
}

main: fun
{
	bytes(200, 50, 5)
	bytes(1, 300)
}
```

```errors
'300' doesn't fit in 'u8'
```

Since every argument has the element type, a lambda argument gets its parameter types from it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~
~ 	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
~ }
~
apply: fun(start: i32, ...steps: View[fun[i32 -> i32]]) -> i32
{
	var value = start
	for i in 0..steps.length
		value = steps[i](value)

	ret value
}

main: fun
{
	printf("%d\n", apply(3, fun(x) => x + 1, fun(x) => x * 10))
}
```

```output
40
```

`apply` also shows fixed parameters before the variadic one. They're filled first, and the rest of the arguments go to the variadic parameter. A fixed parameter with a default value can be left out as usual.

Arguments are evaluated left to right, as in any call:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~
~ 	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
~ }
~
say: fun(n: i32) -> i32
{
	printf("%d ", n)
	ret n
}

show: fun(first: i32, ...rest: View[i32])
{
	printf("| %d", first)
	for i in 0..rest.length
		printf(" %d", rest[i])

	printf("\n")
}

main: fun
{
	show(say(1), say(2), say(3))
}
```

```output
1 2 3 | 1 2 3
```

A variadic argument is passed like a parameter without a mode, so writing `mut` at the call is an error, and so is passing a value of the parameter's own type. To pass one, spread it, as the next section shows.

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
all: fun(...values: View[i32])
{
}

main: fun
{
	var n = 1
	all(mut n)
	val v = View[i32](null, 0)
	all(v)
}
```

```errors
'values' isn't a 'mut' parameter
Cannot convert type 'View[i32]' to 'i32'
```

### Mixed argument types

All arguments share one element type, but an enum with implicit [conversions](conversions.md) into it accepts values of several types. Each argument converts to the enum through its `as` member:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~
~ 	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
~ }
~
Arg: ref enum
{
	int(value: i32)
	text(value: str)

	as: op(value: i32) -> Arg => int(value)
	as: op(value: str) -> Arg => text(value)
}

print: fun(label: str, ...args: View[Arg])
{
	printf("%.*s:", i32(label.byteLength), label.data)
	for i in 0..args.length
	{
		match args[i]
		{
			int(val value) => printf(" %d", value)
			text(val value) => printf(" %.*s", i32(value.byteLength), value.data)
		}
	}

	printf("\n")
}

main: fun
{
	val name = "Ada"
	print("player", name, 30, "hp")
	print("empty")
}
```

```output
player: Ada 30 hp
empty:
```

`Arg` is a `ref enum` because its `text` case holds a `str`, which borrows its bytes.

### Values with destructors

The temporary array lives until the end of the statement that made the call. Arguments with [destructors](ownership.md) are moved into it, and the array drops its elements, last first, when the statement ends:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
Name: own rec
{
	id: i32

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

count: fun(...names: View[Name]) -> usize => names.length

main: fun
{
	val first = Name(1)
	printf("%zu\n", count(Name(2), Name(3)))
	printf("%zu\n", count(first))
	printf("done\n")
}
```

```output
2
drop 3
drop 2
1
drop 1
done
```

A named argument moves into the array too, so it can't be used after the call:

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
count: fun(...names: View[Name]) -> usize => names.length

main: fun
{
	val first = Name(1)
	count(first)
	count(first)
}
```

```errors
Cannot use moved values
```

Because the array is gone after the statement, a function can return its variadic parameter, but the caller can't keep the result:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
first: fun(...values: View[i32]) -> View[i32] => values

main: fun
{
	val kept = first(1, 2)
	printf("%zu\n", kept.length)
}
```

```errors
Cannot borrow unstored values
```

### Declaration rules

The variadic parameter comes last, a function has at most one, and it takes no mode:

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
after: fun(...values: View[i32], last: i32)
{
}

writes: fun(mut ...values: View[i32])
{
}

main: fun
{
}
```

```errors
Cannot take parameters after variadic parameters
Cannot take 'mut' variadic parameters
```

Operators can't be variadic, and neither can `ext` functions, whether written in Cella or declared in `ext` blocks, which take C's `...` instead:

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
callback: ext fun(...values: View[i32]) -> i32 => 0

Total: rec
{
	value: i32

	+: op(a: Total, ...rest: View[i32]) -> Total => a
}

ext
{
	format: fun(text: cstr, ...values: View[i32]) -> i32
}

main: fun
{
}
```

```errors
Cannot take variadic parameters in 'ext' functions
Cannot take variadic parameters in operators
Cannot take typed variadic parameters in 'ext' functions
```

### Methods, constructors and generics

Methods, static functions and constructors take variadic parameters too, and generic functions infer their type arguments from the variadic arguments:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~
~ 	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
~ }
~
Totals: rec
{
	sum: i32

	new: op(...values: View[i32])
	{
		for i in 0..values.length
			self.sum += values[i]
	}

	add: fun(mut self, ...values: View[i32])
	{
		for i in 0..values.length
			self.sum += values[i]
	}
}

last[T: copy]: fun(first: T, ...rest: View[T]) -> T
{
	if rest.length == 0
		ret first

	ret rest[rest.length - 1]
}

main: fun
{
	var totals = Totals(1, 2, 3)
	totals.add(10, 20)
	printf("%d %d\n", totals.sum, Totals().sum)
	printf("%d %.1f %d\n", last(3, 9, 2), last(1.5, 0.5), last(7))
}
```

```output
36 0
2 0.5 7
```

A [trait](traits.md) can require a variadic method or constructor. The implementation must be variadic too, and calls through a bound or a `dyn` value pass their arguments the same way.

### Overloads

A variadic function can be overloaded like any other. Since a variadic parameter takes any number of arguments, an overload that accepts the same arguments conflicts with it:

```cella error
~ mod example
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
pick: fun(x: i32)
{
}

pick: fun(...xs: View[i32])
{
}

main: fun
{
}
```

```errors
'pick' overloads cannot accept the same arguments
'pick' overloads cannot accept the same arguments
```

An overload taking a different type is fine, and so is one that takes the parameter's type directly, which only a value of that type reaches:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
same: fun(xs: View[i32]) => printf("view of %zu\n", xs.length)
same: fun(...xs: View[i32]) => printf("%zu arguments\n", xs.length)
same: fun(x: str) => printf("text\n")

main: fun
{
	val numbers = [1, 2, 3]
	val v = View[i32](@numbers[0], 3)
	same(v)
	same(1, 2)
	same()
	same("x")
}
```

```output
view of 3
2 arguments
0 arguments
text
```

## Spreading

`...` before an argument spreads it into the variadic part of a call. The spread value has the variadic parameter's own type and is passed as it is, so its elements become the arguments. This is how one variadic function forwards its arguments to another. A value that converts to the parameter's type spreads too; here `View` gets an `as` member that converts any array of `T` into a view of its elements, so arrays can be spread:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
View[T]: ref rec
{
	data: ptr[T]
	length: usize

	as[count: const usize]: op(imm values: array[T, count]) -> View[T] => View(@values[0], count)

	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
}

sum: fun(...values: View[i32]) -> i32
{
	var total = 0
	for i in 0..values.length
		total += values[i]

	ret total
}

twice: fun(...values: View[i32]) -> i32 => sum(...values) * 2

main: fun
{
	val three = [1, 2, 3]
	printf("%d %d %d\n", sum(...three), sum(...[4, 5]), twice(1, 2))
}
```

```output
6 9 6
```

A spread is the whole variadic part of a call: it can't be mixed with other variadic arguments, it doesn't fill fixed parameters, and it only goes into a typed variadic parameter.

```cella error
~ mod example
~
~ ext
~ {
~ 	strlen: fun(text: cstr) -> usize
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
all: fun(...values: View[i32])
{
}

fixed: fun(first: i32, ...rest: View[i32])
{
}

main: fun
{
	val a = [1, 2]
	all(1, ...a)
	fixed(...a)
	strlen(...a)
	printf("%d\n", ...a)
}
```

```errors
Cannot combine spread arguments with other variadic arguments
'fixed' doesn't accept these arguments
Cannot spread arguments into calls without variadic parameters
Cannot spread arguments into 'ext' functions
```

## Variadic function types

Variadic functions are values like other functions, and their [function types](closures.md) keep the `...`. A C variadic type ends in a bare `...` after at least one parameter, and a typed one writes `...` before the parameter type. Calls through a value work as calls through the name do, spreads included:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~
~ 	as[count: const usize]: op(imm values: array[T, count]) -> View[T] => View(@values[0], count)
~
~ 	[]: op(self, i: usize) -> imm[T] => imm self.data[i]
~ }
~
sum: fun(...values: View[i32]) -> i32
{
	var total = 0
	for i in 0..values.length
		total += values[i]

	ret total
}

main: fun
{
	val out: ext fun[cstr, ... -> i32] = printf
	out("%d %.1f\n", 5, f32(1.5))

	val total: fun[...View[i32] -> i32] = sum
	val numbers = [4, 5]
	printf("%d %d %d\n", total(1, 2, 3), total(), total(...numbers))
}
```

```output
5 1.5
6 0 9
```

A lambda takes the `...` from the type it's given, like its parameter types and modes. Its parameter receives the built value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
main: fun
{
	val count: fun[str, ...View[i32]] = fun(label, values) => printf("%zu\n", values.length)
	count("x", 1, 2, 3)
}
```

```output
3
```

The `...` is part of the type, so a variadic function type and the same type without it don't convert either way:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ View[T]: ref rec
~ {
~ 	data: ptr[T]
~ 	length: usize
~ }
~
sum: fun(...values: View[i32]) -> i32 => 0
plain: fun(values: View[i32]) -> i32 => 0

main: fun
{
	val packed: fun[View[i32] -> i32] = sum
	val unpacked: fun[...View[i32] -> i32] = plain
	val fixed: ext fun[cstr -> i32] = printf
}
```

```errors
Cannot convert type 'fun[...View[i32] -> i32]' to 'fun[View[i32] -> i32]'
Cannot convert type 'fun[View[i32] -> i32]' to 'fun[...View[i32] -> i32]'
Cannot convert type 'ext fun[cstr, ... -> i32]' to 'ext fun[cstr -> i32]'
```

The rules for declarations apply to types as well: the `...` comes last, takes no mode, and a typed one can't appear in an `ext fun` type.
