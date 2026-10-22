# Records

A record groups named values, its fields, into one type, like a `struct` in C. This chapter covers declaring records, making values of them, constructors and how records are laid out in memory. Functions that belong to a record are in [Methods and properties](methods.md), and destructors are in [Ownership and destructors](ownership.md).

## Declaring a record

A record is declared with `rec`, and its fields go between braces, one per line, each with a name and a type:

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
	var p = Point(3, 4)
	p.x += 10
	printf("%d %d\n", p.x, p.y)
}
```

```output
13 4
```

`p.x` reads or writes the field `x` of `p`. Fields can be numbers, pointers, arrays, enums, function types and other records. A field that holds a borrow, such as a `str`, needs a `ref rec`, covered in [Borrows](borrows.md).

Fields can also share one line, separated by commas, as in `Point: rec { x: i32, y: i32 }`. Either way works, but one body uses one style: [Lexical structure](lexical-structure.md) has the rules.

A field can't have an initial value of its own. Values come from constructors, described below:

```cella error
~ mod example
~
Settings: rec
{
	volume: i32 = 5
}

main: fun
{
}
```

```errors
Cannot give fields initial values
```

Records can be declared in any order in a file, and a record can use a type declared after it. A record can't contain itself, directly or through an array, because its size would have no end. A pointer to itself is fine:

```cella error
~ mod example
~
Node: rec
{
	value: i32
	next: Node
}

Linked: rec
{
	value: i32
	next: ptr[Linked]
}

main: fun
{
}
```

```errors
Field 'next' of type 'Node' causes a cycle in the memory layout
```

### Empty records

A record can have no fields. It is written either with empty braces or with no body at all, and its values take no space:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Marker: rec

Nothing: rec
{
}

main: fun
{
	val _ = Marker()
	printf("%zu %zu\n", sizeOf(Marker), sizeOf(Nothing))
}
```

```output
0 0
```

Without a body, the declaration must end its line.

## Creating values

A record with no declared constructors gets two ways to make a value. `Point(3, 4)` passes one argument for each field, in the order the fields are declared. `Point()` makes a value with every field zeroed:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Color: rec
{
	r: u8
	g: u8
	b: u8
	alpha: f32
}

main: fun
{
	val orange = Color(255, 128, 0, 0.5)
	val black = Color()
	printf("%d %d %d %.2f\n", orange.r, orange.g, orange.b, orange.alpha)
	printf("%d %d %d %.2f\n", black.r, black.g, black.b, black.alpha)
}
```

```output
255 128 0 0.50
0 0 0 0.00
```

The arguments convert to the field types as they would for a function's parameters, so `255` becomes a `u8` and `0.5` an `f32`. Any other number of arguments is an error, and the compiler lists the fields:

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
	val p = Point(1)
}
```

```errors
No constructor for 'Point' accepts these arguments
```

The error's note lists what `Point` takes: "'Point' takes no arguments, or one for each field: x, y".

Arguments are matched to fields by position only.

### Declarations without a value

A variable of a record type declared without a value is the same as one set to `T()`: every field starts zeroed. Fields can then be set one at a time:

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
	var p: Point
	printf("%d %d\n", p.x, p.y)
	p.y = 7
	printf("%d %d\n", p.x, p.y)
}
```

```output
0 0
0 7
```

### Legal defaults

A type has a *legal default* when all-zero memory is a valid value of it. Numbers, `bool`, `char`, pointers and `str` have one. A record has one when all of its fields have one, it declares no constructor and it has no destructor. Only types with a legal default get the built-in `T()` and start zeroed.

Some types have no legal default, such as function types. A record with a field like that has none either, so `T()` isn't available and only the field-by-field constructor is left:

```cella error
~ mod example
~
Handler: rec
{
	callback: fun[i32 -> i32]
	scale: i32
}

main: fun
{
	val h = Handler()
}
```

```errors
No constructor for 'Handler' accepts these arguments
```

A variable of such a type starts uninitialized instead of zeroed. Its fields that do have defaults are zeroed, and the others must be set before the whole value is used:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Handler: rec
~ {
~ 	callback: fun[i32 -> i32]
~ 	scale: i32
~ }
~
double: fun(n: i32) -> i32 => n * 2

main: fun
{
	var h: Handler
	h.callback = double
	printf("%d\n", h.callback(h.scale + 21))
}
```

```output
42
```

Using the value before then is an error. A field that isn't set yet makes the record *partly initialized*:

```cella error
~ mod example
~
~ Handler: rec
~ {
~ 	callback: fun[i32 -> i32]
~ 	scale: i32
~ }
~
describe: fun(h: Handler) -> i32 => h.scale

main: fun
{
	var h: Handler
	h.scale = 3
	val n = describe(h)
}
```

```errors
Cannot use partly initialized values
```

## Required fields

`req` before a field's type removes that field's default, even when its type has one. Every value of the record must then set it explicitly, which suits fields where zero is a mistake, such as a handle or an ID:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
File: rec
{
	handle: req i32
	flags: i32
}

main: fun
{
	val a = File(7, 1)
	var b: File
	b.handle = 5
	printf("%d %d %d\n", a.handle, b.handle, b.flags)
}
```

```output
7 5 0
```

Since the record no longer has a legal default, `File()` isn't available, and reading `b.handle` before it's set is an error:

```cella error
~ mod example
~
~ File: rec
~ {
~ 	handle: req i32
~ 	flags: i32
~ }
~
main: fun
{
	val a = File()
}
```

```errors
No constructor for 'File' accepts these arguments
```

```cella error
~ mod example
~
~ File: rec
~ {
~ 	handle: req i32
~ 	flags: i32
~ }
~
main: fun
{
	var b: File
	b.flags = 1
	val h = b.handle
}
```

```errors
Cannot use uninitialized values
```

When a required field is itself a record, writing any of its fields counts as setting it, and its other fields keep their own defaults. Fields whose type has no default, such as function types, are already required, and `req` on them gets the hint "Redundant 'req'".

## Constructors

A record can declare its own constructors. A constructor is a member named `new`, declared as `op` with parameters and a block body. It's called with the record's name, like the built-in ones:

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

	new: op(x: f32, y: f32)
	{
		self.x = x
		self.y = y
	}

	new: op(length: f32)
	{
		self.x = length
		self.y = 0
	}

	new: op
	{
		self.x = 1
		self.y = 1
	}
}

main: fun
{
	val a = Vec2(3, 4)
	val b = Vec2(2)
	val c = Vec2()
	printf("%.0f %.0f | %.0f %.0f | %.0f %.0f\n", a.x, a.y, b.x, b.y, c.x, c.y)
}
```

```output
3 4 | 2 0 | 1 1
```

A constructor with no parameters is written `new: op`, with no parentheses, as a function without parameters is.

Declaring any constructor replaces both built-in ones. The record no longer has a field-by-field constructor, `T()` exists only if a constructor without parameters is declared, and the record loses its legal default:

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
	val zero = Celsius()
}
```

```errors
No constructor for 'Celsius' accepts these arguments
```

A variable declared without a value starts uninitialized:

```cella error
~ mod example
~
~ Celsius: rec
~ {
~ 	degrees: f64
~
~ 	new: op(degrees: f64)
~ 	{
~ 		self.degrees = degrees
~ 	}
~ }
~
main: fun
{
	var t: Celsius
	val d = t.degrees
}
```

```errors
Cannot use uninitialized values
```

### What `self` is

Inside a constructor, `self` is the value being built. Its fields that have a default start zeroed, so the constructor only has to set the others:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Counter: rec
{
	count: i32
	step: i32

	new: op(step: i32)
	{
		printf("count starts at %d\n", self.count)
		self.step = step
	}
}

main: fun
{
	val c = Counter(5)
	printf("%d %d\n", c.count, c.step)
}
```

```output
count starts at 0
0 5
```

A constructor must set every field without a default before it ends, on every path through it. An `if` that sets a field on only one branch isn't enough:

```cella error
~ mod example
~
Account: rec
{
	id: req i32
	balance: i64

	new: op(id: i32, flag: bool)
	{
		if flag
			self.id = id
	}
}

main: fun
{
}
```

```errors
Cannot leave fields uninitialized
```

The error's note names the field: "'id' is uninitialized".

`self` can't be used as a whole, for example passed to a function or used to call a method, while some field is still unset. Once every field is set, it can:

```cella error
~ mod example
~
Account: rec
{
	id: req i32
	balance: i64

	new: op(id: i32)
	{
		self.balance = describe(self)
		self.id = id
	}
}

describe: fun(account: Account) -> i64 => account.balance

main: fun
{
}
```

```errors
Cannot use partly initialized values
```

A constructor can end early with a bare `ret`, as long as every field is set by then. It can't return a value:

```cella error
~ mod example
~
Score: rec
{
	value: i32

	new: op(value: i32) -> i32
	{
		self.value = value
	}
}

main: fun
{
}
```

```errors
Constructors cannot return values
```

A constructor's body is always a block; the `=>` form of functions isn't available for constructors.

### Assigning to `self`

A constructor can set `self` as a whole, for example to reuse another constructor or a function that builds the value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Range: rec
{
	low: i32
	high: i32

	new: op(low: i32, high: i32)
	{
		self.low = low
		self.high = high
	}

	new: op(high: i32)
	{
		self = Range(0, high)
	}
}

main: fun
{
	val r = Range(10)
	printf("%d..%d\n", r.low, r.high)
}
```

```output
0..10
```

Assigning to `self` replaces the value it held. If the record has a destructor and every field has a default, `self` starts as a whole all-zero value, so that value is dropped when it's replaced:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Slot: own rec
{
	id: i32

	new: op(id: i32)
	{
		self = Slot.make(id * 10)
	}

	drop: op
	{
		printf("drop %d\n", self.id)
	}

	make: fun(id: i32) -> Slot
	{
		var s: Slot = undef
		s.id = id
		ret s
	}
}

main: fun
{
	val s = Slot(4)
	printf("%d\n", s.id)
}
```

```output
drop 0
40
drop 40
```

`Slot.make` is a static function, covered in [Methods and properties](methods.md), and `undef` is covered in [Variables and constants](variables.md).

### Overloading constructors

A record can have any number of constructors, as long as no two can be called with the same arguments. The rules are the same as for overloaded functions (see [Functions](functions.md)): constructors that differ only in parameter modes conflict, and so do constructors that accept the same arguments through default parameter values:

```cella error
~ mod example
~
Meters: rec
{
	value: f64

	new: op(value: f64, scale: f64 = 1)
	{
		self.value = value * scale
	}

	new: op(value: f64)
	{
		self.value = value
	}
}

main: fun
{
}
```

```errors
'Meters.new' overloads cannot accept the same arguments
'Meters.new' overloads cannot accept the same arguments
```

A call picks the constructor whose parameters fit its arguments, as for functions.

### Restoring the default

`new: op = default` declares a constructor without parameters that zeroes every field, and gives the record its legal default back. With it, `T()` works and declarations without a value start zeroed, alongside the record's other constructors:

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

	new: op = default

	new: op(x: f32, y: f32)
	{
		self.x = x
		self.y = y
	}
}

main: fun
{
	var a: Vec2
	val b = Vec2()
	val c = Vec2(1, 2)
	var points: array[Vec2, 3]
	printf("%.0f %.0f %.0f %.0f\n", a.x, b.y, c.y, points[2].y)
}
```

```output
0 0 2 0
```

`= default` is allowed only on the constructor without parameters, and only when every field has a default:

```cella error
~ mod example
~
Callback: rec
{
	run: fun[-> i32]
	id: req i32

	new: op = default
}

Scaled: rec
{
	x: i32

	new: op(x: i32) = default
}

main: fun
{
}
```

```errors
Cannot use 'default' when fields have no default
Cannot use 'default' on constructors with parameters
```

The first error's notes list each field and why it has no default: "'run' has no default" and "'id' is required".

A record with a destructor has no legal default either. `new: op = default` is allowed there too, and gives it one.

## Nested records

A field can hold another record. A field chain such as `line.start.x` reaches inside, and nested values are made by passing records to the outer constructor:

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

Line: rec
{
	start: Point
	end: Point
}

main: fun
{
	val corner = Point(3, 4)
	var line = Line(Point(1, 2), corner)
	line.end.y = 40
	val blank = Line()
	printf("%d %d %d %d\n", line.start.y, line.end.x, line.end.y, blank.end.x)
}
```

```output
2 3 40 0
```

`Line()` and zeroed declarations work here because `Point` has a legal default. An outer record has one only when every record inside it does.

## Copying records

A record whose fields can all be copied is copied whenever it's assigned, passed to a parameter without a mode or returned. The copy is independent of the original:

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
moved: fun(p: Point, dx: i32) -> Point
{
	var result = p
	result.x += dx
	ret result
}

main: fun
{
	val a = Point(1, 2)
	val b = moved(a, 10)
	printf("%d %d\n", a.x, b.x)
}
```

```output
1 11
```

A record copies however large it is. A record with a destructor, or with a field that can't be copied, is declared `own rec` and isn't copied: it moves. [Ownership and destructors](ownership.md) covers moves, and [Parameter modes](parameter-modes.md) covers `imm` and `mut` parameters, which borrow a record instead of copying it.

### `own rec`

`own rec` declares a record whose values move instead of copying. A record with a destructor, or with a field that owns a value, must be declared `own rec` ([Ownership and destructors](ownership.md#owning-types)). It also works without a destructor, for values that stand for something that must have exactly one owner, such as a ticket or a handle owned by other code:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Ticket: own rec
{
	id: i32
}

redeem: fun(ticket: Ticket) -> i32 => ticket.id

main: fun
{
	val ticket = Ticket(7)
	printf("%d\n", redeem(ticket))
}
```

```output
7
```

`redeem` takes the ticket over, and `main` can't use it afterwards:

```cella error
~ mod example
~
Ticket: own rec
{
	id: i32
}

redeem: fun(ticket: Ticket) -> i32 => ticket.id

main: fun
{
	val ticket = Ticket(7)
	val first = redeem(ticket)
	val second = redeem(ticket)
}
```

```errors
Cannot use moved values
```

A record with an `own rec` field must be declared `own rec` too.

## Layout and size

A record's fields are laid out in memory in the order they're declared, the way a C compiler lays out a `struct`. Each field starts at a multiple of its alignment, with padding before it when needed, and the record's size is rounded up to a multiple of its largest alignment, so that records in an array stay aligned. `sizeOf(T)` gives a type's size in bytes and `alignOf(T)` its alignment; both are `usize`, and both also accept a value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Loose: rec
{
	tag: u8
	value: i64
	flag: bool
}

Tight: rec
{
	value: i64
	tag: u8
	flag: bool
}

main: fun
{
	val loose = Loose()
	printf("%zu %zu %zu\n", sizeOf(Loose), alignOf(Loose), sizeOf(loose))
	printf("%zu %zu\n", sizeOf(Tight), sizeOf(array[Tight, 4]))
}
```

```output
24 8 24
16 64
```

`Loose` has seven bytes of padding after `tag`, so that `value` starts at offset 8, and seven more after `flag`. `Tight` puts the large field first and needs only six bytes of padding at the end. The compiler never reorders fields, which is what lets a record match a C `struct` field for field; [Calling C](calling-c.md) covers passing records to C.
