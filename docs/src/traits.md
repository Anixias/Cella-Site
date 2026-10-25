# Traits

A trait names a set of members that several types can provide: methods, properties, static functions, operators, constructors and constants. A type implements a trait by saying so and supplying those members. Generic code can then require the trait and use its members on any type that implements it.

## What a trait is

A [generic](generics.md) function can't call methods on a `T`, since most types don't have them. A trait solves this. It lists what a type must have, here an `area` method and a `name` method:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: trait
{
	area: fun(imm self) -> f64
	name: fun(imm self) -> cstr
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => 3.14159 * self.radius * self.radius
	name: fun(imm self) -> cstr => "circle"
}

Square: rec impl Shape
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
	name: fun(imm self) -> cstr => "square"
}

report[T: Shape]: fun(imm shape: T)
{
	printf("%s %.2f\n", shape.name(), shape.area())
}

main: fun
{
	report(Circle(1.0))
	report(Square(2.0))
}
```

```output
circle 3.14
square 4.00
```

`Circle: rec impl Shape` declares that `Circle` implements `Shape`, and its body supplies the members `Shape` requires. `[T: Shape]` is a trait bound: `report` accepts any type that implements `Shape`, and its body can call `Shape`'s members on a `T`. Each type `report` is called with gets its own compiled copy, so the calls go straight to `Circle.area` and `Square.area`, with no lookup at run time. When the type is only known at run time, use a [trait object](trait-objects.md) instead.

A type implements a trait only by saying so. Having methods with the right names isn't enough:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: trait
{
	area: fun(imm self) -> f64
}

Point: rec
{
	x: f64

	area: fun(imm self) -> f64 => 0.0
}

report[T: Shape]: fun(imm shape: T) => printf("%.2f\n", shape.area())

main: fun
{
	report(Point(1.0))
	report(5)
}
```

```errors
'report' requires 'T: Shape'
'report' requires 'T: Shape'
```

## Requirements

A trait's body lists its requirements, written like the members of a record without their bodies. `Self` stands for the implementing type. Besides methods, a trait can require properties, static functions, operators, constructors and constants.

### Properties and static functions

A property requirement is a standalone `get` or a `prop` with both accessors. A function without a receiver is a static function; generic code calls it through the type parameter, as in `T.start()`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Counter: trait
{
	count: get(imm self) -> i32
	limit: prop i32
	{
		get(imm self)
		set(mut self, value)
	}
	start: fun -> Self
	bump: fun(mut self)
}

Clicks: rec impl Counter
{
	clicks: i32
	cap: i32

	count: get(imm self) -> i32 => self.clicks
	limit: prop i32
	{
		get(imm self) => self.cap
		set(mut self, value)
		{
			self.cap = value
		}
	}

	start: fun -> Clicks => Clicks(0, 3)

	bump: fun(mut self)
	{
		if self.clicks < self.cap
			self.clicks += 1
	}
}

run[T: Counter]: fun(times: i32) -> T
{
	var counter = T.start()
	counter.limit += 2
	for i in 0..times
		counter.bump()

	ret counter
}

main: fun
{
	val result = run[Clicks](10)
	printf("%d %d\n", result.count, result.limit)
}
```

```output
5 5
```

`Self` exists only inside traits. An implementation writes its own type's name, as `start: fun -> Clicks` does:

```cella error
~ mod example
~
Counter: trait
{
	start: fun -> Self
}

Clicks: rec impl Counter
{
	clicks: i32

	start: fun -> Self => Clicks(0)
}
~
~ main: fun
~ {
~ }
```

```errors
'start' doesn't match 'Counter.start'
Type 'Self' not found in this scope
```

### Operators

Operator requirements are written like [operator members](operators.md). Built-in types meet them with their built-in operators, so `i32: impl Sum` only has to add `empty`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Sum: trait
{
	+: op(imm a: Self, imm b: Self) -> Self
	empty: fun -> Self
}

i32: impl Sum
{
	empty: fun -> i32 => 0
}

f64: impl Sum
{
	empty: fun -> f64 => 0.0
}

Money: rec impl Sum
{
	cents: i64

	+: op(a: Money, b: Money) -> Money => Money(a.cents + b.cents)
	empty: fun -> Money => Money(0)
}

total[T: Sum + noref, const length: usize]: fun(imm values: array[T, length]) -> T
{
	var sum = T.empty()
	for imm value in values
		sum = sum + value

	ret sum
}

main: fun
{
	val prices = [Money(250), Money(199)]
	printf("%d %.2f %lld\n", total([1, 2, 3]), total([0.5, 0.25]), total(imm prices).cents)
}
```

```output
6 0.75 449
```

The `noref` bound matters here: for a `T` that could hold borrows, `sum + value` could borrow from `sum`, and `sum` couldn't then be reassigned with it. See [Generics](generics.md#noref).

A built-in operator also takes the place of a default body the trait gives for it. An implementation can't declare an operator a type already has built in:

```cella error
~ mod example
~
Sum: trait
{
	+: op(imm a: Self, imm b: Self) -> Self
}

i32: impl Sum
{
	+: op(a: i32, b: i32) -> i32 => a + b
}
~
~ main: fun
~ {
~ }
```

```errors
Operator '+' between 'i32' and 'i32' is built in
```

### Constructors

A constructor requirement lets generic code build a `T` with `T(...)`. A type meets it the way it meets a [`new(...)` constraint](generics.md#new): with a declared constructor that takes the same parameters, or, when it declares none, with its field-by-field constructor. Built-in conversions count, so `u64` meets `new: op(capacity: usize)` with its conversion from `usize`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Sized: trait
{
	new: op(capacity: usize)
}

Buffer: rec impl Sized
{
	size: usize

	new: op(capacity: usize)
	{
		self.size = capacity * 2
	}
}

Slot: rec impl Sized
{
	capacity: usize
}

u64: impl Sized

make[T: Sized]: fun -> T => T(64)

main: fun
{
	printf("%zu %zu %llu\n", make[Buffer]().size, make[Slot]().capacity, make[u64]())
}
```

```output
128 64 64
```

Constants are covered in [Trait constants](#trait-constants) below.

## Default bodies

A requirement can have a body. Types that implement the trait get it as it is, or replace it with their own. A trait can also have `pvt` members, helpers with bodies that only the trait's own bodies can use:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Greeter: trait
{
	name: fun(imm self) -> cstr
	greet: fun(imm self) => printf("hello, %s%s\n", self.name(), mark())
	mark: pvt fun -> cstr => "!"
}

Dog: rec impl Greeter
{
	age: i32

	name: fun(imm self) -> cstr => "dog"
}

Robot: rec impl Greeter
{
	serial: i32

	name: fun(imm self) -> cstr => "robot"
	greet: fun(imm self) => printf("GREETINGS, %s %d\n", self.name(), self.serial)
}

main: fun
{
	Dog(3).greet()
	Robot(42).greet()
}
```

```output
hello, dog!
GREETINGS, robot 42
```

```cella error
~ mod example
~
Greeter: trait
{
	name: fun(imm self) -> cstr
	mark: pvt fun -> cstr => "!"
	loud: pvt fun(imm self) -> cstr => self.name()
}

Dog: rec impl Greeter
{
	age: i32

	name: fun(imm self) -> cstr => "dog"
}

main: fun
{
	val d = Dog(3)
	val m = Greeter(Dog).mark()
	val l = d.loud()
}
```

```errors
'mark' is private to its trait
'loud' is private to its trait
```

A `pvt` member needs a body, and a trait can't hold fields, static fields or destructors.

## Implementing a trait

A type implements a trait in one of two places: in its own declaration, as in `Circle: rec impl Shape` or `Color: enum impl Show`, or in a separate `impl` block, as in `Point: impl Show`. Several traits are joined with `+`, as in `rec impl Hash + Show`. An `impl` block can name any type, built-in types included:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Show: trait
{
	show: fun(imm self)
}

Color: enum impl Show
{
	red
	green

	show: fun(imm self)
	{
		match self
		{
			red => printf("red\n")
			green => printf("green\n")
		}
	}
}

Point: rec
{
	x: i32
	y: i32
}

Point: impl Show
{
	show: fun(imm self) => printf("(%d, %d)\n", self.x, self.y)
}

i32: impl Show
{
	show: fun(imm self) => printf("%d\n", self)
}

print[T: Show]: fun(imm value: T) => value.show()

main: fun
{
	print(Color.green)
	print(Point(1, 2))
	print(7)
}
```

```output
green
(1, 2)
7
```

The trait's members become members of the type, so `Point(1, 2).show()` works outside generic code too. An `impl` block holds only the trait's members and `pvt` helpers, which only that block can use. It can't add fields, static fields, constructors or destructors.

Members the type already has count toward the requirements, and an `impl` block only supplies the rest. A member that takes `self` by copy meets a requirement that takes `imm self`, when the type can be copied:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: trait
{
	area: fun(imm self) -> f64
	sides: fun(imm self) -> i32
}

Square: rec
{
	side: f64

	area: fun(self) -> f64 => self.side * self.side
}

Square: impl Shape
{
	sides: fun(imm self) -> i32 => 4
}

measure[T: Shape]: fun(imm shape: T) -> f64 => shape.area() * f64(shape.sides())

main: fun
{
	printf("%.1f\n", measure(Square(2.0)))
}
```

```output
16.0
```

A missing member, a member whose signature differs from the requirement, a trait implemented twice, and a member the trait doesn't have are all errors:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
	sides: fun(imm self) -> i32
}

Missing: rec impl Shape
{
	x: f64

	area: fun(imm self) -> f64 => self.x
}

Wrong: rec impl Shape
{
	x: f64

	area: fun(imm self) -> i32 => 0
	sides: fun(imm self) -> i32 => 0
}

Twice: rec impl Shape + Shape
{
	x: f64

	area: fun(imm self) -> f64 => self.x
	sides: fun(imm self) -> i32 => 0
}

Point: rec
{
	x: f64
}

Point: impl Shape
{
	area: fun(imm self) -> f64 => 0.0
	sides: fun(imm self) -> i32 => 0
	extra: fun(imm self) -> i32 => 1
	y: f64
}
~
~ main: fun
~ {
~ }
```

```errors
'Missing' needs 'Shape.sides'
'area' doesn't match 'Shape.area'
'Twice' implements 'Shape' more than once
'Twice' implements 'Shape' more than once
'extra' isn't a member of 'Shape'
Cannot declare fields in impl blocks
```

A generic type can implement a trait for every instantiation, as in `Box[T]: impl Show`, for those that meet extra bounds, as in `Box[T: Show]: impl Show`, or for one instantiation, as in `Box[i32]: impl Show`. Two of these that cover the same type, like `Box[T]` and `Box[i32]`, implement the trait twice.

### Where an implementation can go

An implementation must be in the project that declares the trait or the project that declares the type. A program can implement its own traits for a library's types and a library's traits for its own types, but not a library's trait for a library's type:

```celp group=orphans
OutputType = "Executable"
SystemLinkPreference = "Dynamic"

[[ProjectReferences]]
Path = "shapes/shapes.celp"
```

```celp group=orphans file=shapes/shapes.celp
OutputType = "SharedLibrary"
SystemLinkPreference = "Dynamic"
```

```cella group=orphans file=shapes/shapes.ce
mod shapes

Shape: pub trait
{
	area: fun(imm self) -> f64
}
```

```cella error group=orphans
mod example

use shapes.Shape

Square: rec impl Shape
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
}

f64: impl Shape
{
	area: fun(imm self) -> f64 => self
}

main: fun
{
}
```

```errors group=orphans
'Shape' and 'f64' are both declared in other projects
```

Library projects are covered in [Modules and visibility](modules.md).

## Using traits in generic code

A bound gives generic code every member of the trait: methods and properties on values, static functions and constants on the type parameter, operators, and constructors as `T(...)`. Several bounds are joined with `+`, and they mix with the other [constraints](generics.md#constraints), as in `[T: Sum + noref]`. Records and enums take bounds on their type parameters too, as in `Set[T: Hash + noref]: rec`.

Inside generic code, a type parameter meets a bound only if its own bounds include that trait or a trait that requires it (see [Traits that require other traits](#traits-that-require-other-traits)), or a [blanket implementation](#blanket-implementations) covers it.

A member declared `const`, an `impl const` implementation and a `T: const Trait` bound let generic code call a trait's members while compiling; see [Constant traits](constant-functions.md#constant-traits).

## Picking a trait's member

When a type implements two traits with members of the same name, a call by that name is ambiguous. Naming the trait picks its member: `Area(s).size()` calls `Area`'s method on `s`, and `Area(Square).unit()` calls `Area`'s static function for `Square`. Generic code picks the same way:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Area: trait
{
	size: fun(imm self) -> f64
	unit: fun -> cstr
}

Perimeter: trait
{
	size: fun(imm self) -> f64
	unit: fun -> cstr
}

Square: rec
{
	side: f64
}

Square: impl Area
{
	size: fun(imm self) -> f64 => self.side * self.side
	unit: fun -> cstr => "m2"
}

Square: impl Perimeter
{
	size: fun(imm self) -> f64 => self.side * 4.0
	unit: fun -> cstr => "m"
}

both[T: Area + Perimeter]: fun(imm shape: T) -> f64 => Area(shape).size() + Perimeter(shape).size()

main: fun
{
	val s = Square(3.0)
	printf("%.1f %s\n", Area(s).size(), Area(Square).unit())
	printf("%.1f %s\n", Perimeter(s).size(), Perimeter(Square).unit())
	printf("%.1f\n", both(imm s))
}
```

```output
9.0 m2
12.0 m
21.0
```

The pick works for properties too: with a property `count` in both traits, `Area(s).count = 5` calls `Area`'s setter. A trait on its own isn't a value:

```cella error
~ mod example
~
Area: trait
{
	size: fun(imm self) -> f64
}

Perimeter: trait
{
	size: fun(imm self) -> f64
}

Square: rec
{
	side: f64
}

Square: impl Area
{
	size: fun(imm self) -> f64 => self.side * self.side
}

Square: impl Perimeter
{
	size: fun(imm self) -> f64 => self.side * 4.0
}

main: fun
{
	val s = Square(3.0)
	val size = s.size()
	val t = Area
}
```

```errors
Call to 'size' is ambiguous
Cannot use traits as values
```

## Generic traits

A trait can take type parameters, declared on its name like other generics. An implementation names its arguments, as in `impl Iterator[i32]`, and a bound does too, as in `[I: Iterator[i32]]`. A bound can leave an argument to a type parameter, as `count` does with `T`; the compiler infers `T` from the type's implementation:

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
}

Iterator[T]: trait
{
	next: fun(mut self) -> Option[T]
}

Countdown: rec impl Iterator[i32]
{
	left: i32

	next: fun(mut self) -> Option[i32]
	{
		if self.left == 0
			ret none

		self.left -= 1
		ret some(self.left + 1)
	}
}

Repeat[T: copy]: rec impl Iterator[T]
{
	value: T
	times: i32

	next: fun(mut self) -> Option[T]
	{
		if self.times == 0
			ret none

		self.times -= 1
		ret some(self.value)
	}
}

total[I: Iterator[i32]]: fun(mut items: I) -> i32
{
	var sum = 0
	while items.next() is some(val value)
		sum += value

	ret sum
}

count[T, I: Iterator[T]]: fun(mut items: I) -> i32
{
	var n = 0
	while items.next() is some(_)
		n += 1

	ret n
}

main: fun
{
	var steps = Countdown(4)
	var more = Countdown(3)
	var words = Repeat[cstr]("hi", 5)
	printf("%d %d %d\n", total(mut steps), count(mut more), count(mut words))
}
```

```output
10 3 5
```

A parameter like `count`'s `T` can also be declared inside the bound. A name in a bound's brackets that doesn't name anything else declares a new parameter, so `[I: Iterator[T]]` declares `T`, and `[I: Iterator[T: copy]]` declares it with constraints. Records, enums and traits declare parameters the same way. The new parameter also gets the constraints the trait puts on that position: for `Ranked[T: copy]`, `[R: Ranked[T]]` can copy a `T`. The parameter is inferred from the type it's attached to: first from the arguments, then from that type's implementation. So `Skipping[Countdown]` needs no second argument:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Option[T]: enum
~ {
~ 	none
~ 	some(value: T)
~ }
~
~ Iterator[T]: trait
~ {
~ 	next: fun(mut self) -> Option[T]
~ }
~
~ Countdown: rec impl Iterator[i32]
~ {
~ 	left: i32
~
~ 	next: fun(mut self) -> Option[i32]
~ 	{
~ 		if self.left == 0
~ 			ret none
~
~ 		self.left -= 1
~ 		ret some(self.left + 1)
~ 	}
~ }
~
first[I: Iterator[T]]: fun(mut items: I) -> Option[T] => items.next()

Skipping[I: Iterator[T]]: rec impl Iterator[T]
{
	items: I

	next: fun(mut self) -> Option[T]
	{
		val _ = self.items.next()
		ret self.items.next()
	}
}

main: fun
{
	var steps = Countdown(3)
	if first(mut steps) is some(val value)
		printf("%d\n", value)

	var skipping: Skipping[Countdown] = Skipping(Countdown(6))
	while skipping.next() is some(val value)
		printf("%d\n", value)
}
```

```output
3
5
3
1
```

When a type implements the trait more than once, as `Console` does below, the parameter can't be inferred from the type alone. A call can still pick it from its other arguments; otherwise it's an error: "Cannot infer 'T' for 'first'".

A type can implement several instantiations of one trait, each with its own members:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Write[T]: trait
{
	write: fun(mut self, imm value: T)
}

Console: rec impl Write[cstr] + Write[i32]
{
	written: i32

	write: fun(mut self, value: cstr)
	{
		printf("%s", value)
		self.written += 1
	}

	write: fun(mut self, value: i32)
	{
		printf("%d", value)
		self.written += 1
	}
}

report[W: Write[cstr] + Write[i32]]: fun(mut out: W, score: i32)
{
	out.write("score: ")
	out.write(imm score)
	out.write("\n")
}

main: fun
{
	var console = Console(0)
	report(mut console, 42)
	printf("%d writes\n", console.written)
}
```

```output
score: 42
3 writes
```

A trait's type parameters can have [defaults](generics.md#default-arguments). A default can use `Self`, which stands for the type the trait is applied to: the implementing type in an implementation, and the type parameter in a bound. Here `Combine` with no argument means "combine with another value of the same type", while `Offset` names a different right-hand type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Combine[Rhs = Self]: trait
{
	combine: fun(self, other: Rhs) -> Self
}

i32: impl Combine
{
	combine: fun(self, other: i32) -> i32 => self + other
}

Meters: rec impl Combine
{
	value: i32

	combine: fun(self, other: Meters) -> Meters => Meters(self.value + other.value)
}

Offset: rec impl Combine[i32]
{
	value: i32

	combine: fun(self, other: i32) -> Offset => Offset(self.value + other)
}

sum[T: Combine + copy]: fun(a: T, b: T) -> T => a.combine(b)

main: fun
{
	val meters = sum(Meters(2), Meters(3))
	val offset = Offset(1).combine(9)
	printf("%d %d %d\n", sum(3, 4), meters.value, offset.value)
}
```

```output
7 5 10
```

`T: Combine` is `T: Combine[T]`, and `i32: impl Combine` implements `Combine[i32]`. Where there's no type for `Self` to stand for, as in a `dyn` type, the argument has to be written:

```cella error
~ mod example
~
Combine[Rhs = Self]: trait
{
	combine: fun(self, other: Rhs) -> Self
}

describe: fun(imm value: dyn[Combine]) -> i32 => 0
~
~ main: fun
~ {
~ }
```

```errors
'Combine' needs an argument for 'Rhs'
```

## Traits that require other traits

`Ord: trait req Eq` says that every type that implements `Ord` implements `Eq` as well. `Ord`'s default bodies can then use `Eq`'s members, and a bound `[T: Ord]` gives generic code both traits' members and meets `[T: Eq]` bounds:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Ord: trait req Eq
{
	<: op(imm a: Self, imm b: Self) -> bool
	<=: op(imm a: Self, imm b: Self) -> bool => a < b || a == b
}

Version: rec impl Ord
{
	major: i32
	minor: i32

	==: op(a: Version, b: Version) -> bool => a.major == b.major && a.minor == b.minor
	<: op(a: Version, b: Version) -> bool => a.major < b.major || a.major == b.major && a.minor < b.minor
}

i32: impl Ord

same[T: Eq]: fun(imm a: T, imm b: T) -> bool => a == b

within[T: Ord]: fun(imm value: T, imm low: T, imm high: T) -> bool => low <= value && value <= high

isEdge[T: Ord]: fun(imm value: T, imm low: T, imm high: T) -> bool => same(imm value, imm low) || value == high

main: fun
{
	val low = Version(1, 0)
	val high = Version(2, 0)
	val current = Version(1, 5)
	printf("%d %d\n", within(imm current, imm low, imm high), within(12, 1, 9))
	printf("%d %d\n", isEdge(imm low, imm low, imm high), same(imm current, imm low))
}
```

```output
1 0
1 0
```

Implementing `Ord` implements `Eq` too, when the type doesn't have it yet, so `Version: rec impl Ord` is enough, and the same declaration or block holds the members of both. Naming `Eq` as well, as in `rec impl Ord + Eq`, gets the hint "Redundant 'Eq'". Requirements chain: a trait that requires `Ord` requires `Eq` too. A trait can require several, as in `req Eq + Hash`, and a trait can't require itself, directly or through others:

```cella error
~ mod example
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Ord: trait req Eq
{
	<: op(imm a: Self, imm b: Self) -> bool
}

Plain: rec impl Ord
{
	n: i32

	<: op(a: Plain, b: Plain) -> bool => a.n < b.n
}

Even: trait req Odd
Odd: trait req Even
~
~ main: fun
~ {
~ }
```

```errors
'Plain' needs 'Eq.=='
'Even' requires itself
'Odd' requires itself
```

A trait with nothing of its own to require, like `Even` here, needs no body.

### Defaults from a requiring trait

A trait can give a default body to a member of a trait it requires, by declaring the member again, with the same signature, and a body. Types that implement it get that body unless they write their own:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Ranked: trait req Eq
{
	rank: fun(imm self) -> i32

	==: op(imm a: Self, imm b: Self) -> bool => a.rank() == b.rank()
}

Card: rec impl Ranked
{
	value: i32

	rank: fun(imm self) -> i32 => self.value
}

Tile: rec impl Ranked
{
	value: i32
	color: i32

	rank: fun(imm self) -> i32 => self.value
	==: op(a: Tile, b: Tile) -> bool => a.value == b.value && a.color == b.color
}

same[T: Eq]: fun(imm a: T, imm b: T) -> bool => a == b

main: fun
{
	printf("%d %d\n", Card(3) == Card(3), same(Card(3), Card(4)))
	printf("%d\n", Tile(3, 1) == Tile(3, 2))
}
```

```output
1 0
0
```

The redeclared member is still `Eq`'s `==`, not a second one, so `same` and every other use of `Eq` get `Card`'s `==` from `Ranked`. When several traits on the way give a default, the one from the trait that requires the others wins. Two unrelated traits that both give one are an error for a type that implements both:

```cella error
~ mod example
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Ranked: trait req Eq
{
	rank: fun(imm self) -> i32

	==: op(imm a: Self, imm b: Self) -> bool => a.rank() == b.rank()
}

Sized: trait req Eq
{
	size: fun(imm self) -> i32

	==: op(imm a: Self, imm b: Self) -> bool => a.size() == b.size()
}

Crate: rec impl Ranked + Sized
{
	value: i32

	rank: fun(imm self) -> i32 => self.value
	size: fun(imm self) -> i32 => self.value
}
~
~ main: fun
~ {
~ }
```

```errors
'Eq.==' has defaults in both 'Ranked' and 'Sized'
```

Declaring the member again without a body changes nothing, and it gets the hint "Redundant '=='", with a note naming the trait that declares it.

### Removing a default

`req` before `fun` or `op` in such a redeclaration removes the default the required trait gives, so types that implement the trait must write the member themselves:

```cella error
~ mod example
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
	!=: op(imm a: Self, imm b: Self) -> bool => !(a == b)
}

Fast: trait req Eq
{
	!=: req op(imm a: Self, imm b: Self) -> bool
}

Point: rec impl Fast
{
	x: i32

	==: op(a: Point, b: Point) -> bool => a.x == b.x
}
~
~ main: fun
~ {
~ }
```

```errors
'Point' needs 'Eq.!='
```

The error's note says "Default removed by 'Fast'". A `req` on a member that has no default to remove gets the hint "Redundant 'req'". `req` can't have a body, and outside such a redeclaration a function or operator can't be `req` ("Cannot declare required functions"). For a type that implements two unrelated traits, one giving a default and the other removing it, the conflict is an error: "'Eq.!=' has a default in 'Loose' that 'Fast' removes".

## Constraints on Self

`req` takes the other [constraints](generics.md#constraints) as well, and applies them to every type that implements the trait. `Bounded: trait req copy` accepts only types that can be copied, so its constants can hold a `Self` and code with a `[T: Bounded]` bound can copy a `T`. `Built: trait req new(i32)` requires a constructor, which generic code calls as `T(7)`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bounded: trait req copy
{
	lowest: const Self
	highest: const Self
}

u8: impl Bounded
{
	lowest: const u8 = 0
	highest: const u8 = 255
}

i16: impl Bounded
{
	lowest: const i16 = -32768
	highest: const i16 = 32767
}

limits[T: Bounded]: fun -> array[T, 2] => [T.lowest, T.highest]

twice[T: Bounded]: fun(value: T) -> array[T, 2] => [value, value]

Built: trait req new(i32)

Meters: rec impl Built
{
	centimeters: i32

	new: op(value: i32)
	{
		self.centimeters = value * 100
	}
}

build[T: Built]: fun -> T => T(7)

main: fun
{
	val bytes = limits[u8]()
	val shorts = limits[i16]()
	printf("%d %d %d %d\n", bytes[0], bytes[1], shorts[0], shorts[1])
	printf("%d %d\n", twice[u8](9)[1], build[Meters]().centimeters)
}
```

```output
0 255 -32768 32767
9 700
```

A type that doesn't meet the trait's constraints can't implement it:

```cella error
~ mod example
~
Bounded: trait req copy
{
	highest: const Self
}

Built: trait req new(i32)

Handle: own rec
{
	id: i32

	drop: op
	{
	}
}

Handle: impl Bounded

Point: rec impl Built
{
	x: i32
	y: i32
}
~
~ main: fun
~ {
~ }
```

```errors
'Handle' needs 'Bounded.highest'
'Bounded' requires 'Self: copy'
'Built' requires 'Self: new(i32)'
```

Constraints and traits mix in one list, as in `req copy + Ord`. Writing `[T: Bounded + copy]` repeats what `Bounded` already requires and gets the hint "Redundant 'copy'".

A trait can require an [enum](generics.md#enum) whose tag is one of the trait's parameters, as in `req enum(T)`. An implementation can then leave that argument out, since the enum's tag decides it. Here `Access: ext enum(u32) impl Flags` implements `Flags[u32]`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Integral: trait req copy
{
	|: op(a: Self, b: Self) -> Self
}

u32: impl Integral

Flags[T: Integral]: trait req ext + enum(T)
{
	|: op(a: Self, b: Self) -> Self => Self(T(a) | T(b))
}

Access: ext enum(u32) impl Flags
{
	none = 0
	read = 1
	write = 2
}

main: fun
{
	val both = Access.read | Access.write
	printf("%u\n", u32(both))
}
```

```output
3
```

The argument can still be written, and one that doesn't match the tag type is an error. A type that isn't an enum without payloads gets "'Flags' requires 'Self: enum(T)'". Bounds and `dyn` types always need the argument, as in `[E: Flags[T]]`, where `T` gets `Flags`'s `T: Integral` as well. With `const` operators and an `impl const Integral`, `Access.read | Access.write` also works in constants ([Constant functions](constant-functions.md)).

## Blanket implementations

A blanket implementation implements a trait for every type at once. It's written with a type parameter and no type name, as `[T]: impl Describe`, and can be narrowed by constraints, as `[T: Eq]: impl Describe`. A type's own implementation always wins over a blanket one. Between blankets, the more constrained one wins for the types it covers:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Describe: trait
{
	describe: fun(imm self) -> cstr
}

Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

[T]: impl Describe
{
	describe: fun(imm self) -> cstr => "something"
}

[T: Eq]: impl Describe
{
	describe: fun(imm self) -> cstr => "comparable"
}

i32: impl Eq

Plain: rec
{
	value: i32
}

Named: rec impl Describe
{
	value: i32

	describe: fun(imm self) -> cstr => "named"
}

show[T]: fun(imm value: T) => printf("%s\n", value.describe())

main: fun
{
	val number: i32 = 1
	val ratio = 2.5
	show(imm number)
	show(Plain(2))
	show(Named(3))
	printf("%s\n", ratio.describe())
}
```

```output
comparable
something
named
something
```

`show` has no bound at all, yet it can call `describe`, because `[T]: impl Describe` covers every `T`. A type parameter gets a blanket's trait when its bounds meet the blanket's constraints.

A blanket body is checked once, like any generic body, so it can only use what its constraints allow: the body of a plain `[T]: impl` can use `sizeOf(T)` but no members of `self`. Two blankets that can't be ranked, because neither one's constraints include the other's, are both errors, and a blanket takes exactly one type parameter:

```cella error
~ mod example
~
Eq: trait
{
	==: op(imm a: Self, imm b: Self) -> bool
}

Show: trait
{
	show: fun(imm self) -> cstr
}

Describe: trait
{
	describe: fun(imm self) -> cstr
}

[T: Eq]: impl Describe
{
	describe: fun(imm self) -> cstr => "comparable"
}

[T: Show]: impl Describe
{
	describe: fun(imm self) -> cstr => "shown"
}

[T, U]: impl Show
{
	show: fun(imm self) -> cstr => "two"
}
~
~ main: fun
~ {
~ }
```

```errors
'T' implements 'Describe' more than once
'T' implements 'Describe' more than once
Blanket impls take one type parameter
```

Only the project that declares a trait can give it a blanket implementation; anywhere else, `[T]: impl Shape` is "'Shape' is declared in another project".

## Extension methods

An `impl` block with no trait adds members to a type declared somewhere else: a built-in type, a type from another module, or every type at once with `[T]`. These are extension methods. They can be methods, static functions, properties, operators and constants, but not fields, constructors or destructors:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
i32: impl
{
	clamp: fun(imm self, low: i32, high: i32) -> i32
	{
		if self < low
			ret low
		else if self > high
			ret high

		ret self
	}

	isEven: get(imm self) -> bool => self % 2 == 0
	parse: fun(digit: u8) -> i32 => i32(digit) - 48
}

[T]: impl
{
	byteSize: fun(imm self) -> usize => sizeOf(T)
}

main: fun
{
	val x: i32 = 50
	val ratio = 2.5
	printf("%d %d %d\n", x.clamp(0, 10), x.isEven, i32.parse('7'u8))
	printf("%zu %zu\n", x.byteSize(), ratio.byteSize())
}
```

```output
10 1 7
4 8
```

Extensions apply only in the module that declares them and in files that import that module, with `use` or the project's `Imports` list. Here `measure` extends `geometry.Point`, and `main.ce` uses the extension because it says `use measure`:

```cella group=extensions file=geometry.ce
mod geometry

Point: rec
{
	x: i32
	y: i32
}
```

```cella group=extensions file=measure.ce
mod measure

use geometry.Point

Point: impl
{
	lengthSquared: fun(imm self) -> i32 => self.x * self.x + self.y * self.y
	+: op(a: Point, b: Point) -> Point => Point(a.x + b.x, a.y + b.y)
}
```

```cella group=extensions
~ mod example
~
use geometry.Point
use measure
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }

main: fun
{
	val moved = Point(3, 4) + Point(1, 1)
	printf("%d %d\n", moved.x, moved.lengthSquared())
}
```

```output group=extensions
4 41
```

A file that doesn't import the module doesn't see its extensions:

```cella group=unimported file=mathx.ce
mod mathx

i32: impl
{
	doubled: fun(imm self) -> i32 => self * 2
}
```

```cella error group=unimported
mod example

twice: fun(x: i32) -> i32 => x.doubled()
~
~ main: fun
~ {
~ }
```

```errors group=unimported
Type 'i32' has no member 'doubled'
```

Each member follows the visibility rules for top-level declarations: `pvt` keeps it to its file, `mod` to its module, no keyword to the project, and `pub` exports it from a library (see [Modules and visibility](modules.md)). A word before `impl`, as in `i32: mod impl { ... }`, applies to every member of the block.

When a type's own member and an extension have the same signature, the type's member is used; extensions with other signatures overload it. Two imported extensions with the same signature make a call ambiguous, so a file can avoid a clash by not importing one of them.

In the type's own module, an `impl` block without a trait isn't an extension: it adds members under extra bounds, as [Generics](generics.md) describes, and a block that adds no bounds is an error.

## Trait constants

A trait can require constants. `bits: const u32` is a requirement every implementation must give a value, and `bytes: const u32 = bits / 8` is a default that an implementation may replace. A constant is read through a type, as in `i32.bits` or `T.bits`, or by its bare name inside the trait and its implementations. It folds to a constant for each type, so `T.bytes` can size an array:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Integer: trait
{
	bits: const u32
	bytes: const u32 = bits / 8
	isSigned: const bool = false
}

i32: impl Integer
{
	bits: const u32 = 32
	isSigned: const bool = true
}

u8: impl Integer
{
	bits: const u32 = 8
}

Wide: rec impl Integer
{
	low: u64
	high: u64

	bits: const u32 = 128
}

describe[T: Integer]: fun => printf("%u bits, %u bytes, signed %d\n", T.bits, T.bytes, T.isSigned)

toBytes[T: Integer]: fun(seed: u8) -> array[u8, T.bytes]
{
	var result: array[u8, T.bytes]
	for i in 0..result.length
		result[i] = seed + u8(i)

	ret result
}

main: fun
{
	describe[i32]()
	describe[u8]()
	describe[Wide]()
	val four = toBytes[i32](10)
	printf("%u %zu %zu\n", i32.bytes, four.length, toBytes[Wide](0).length)
}
```

```output
32 bits, 4 bytes, signed 1
8 bits, 1 bytes, signed 0
128 bits, 16 bytes, signed 0
4 4 16
```

Trait constants are always `const`, and an implementation's constant must have the requirement's type. In a generic argument, `T.bytes` must stand alone, like a [value parameter](generics.md#value-parameters):

```cella error
~ mod example
~
Integer: trait
{
	bits: const u32
	bytes: const u32 = bits / 8
}

Flags: trait
{
	value: val u32 = 1
}

u16: impl Integer

i64: impl Integer
{
	bits: const i32 = 64
}

unbounded[T]: fun -> u32 => T.bits

doubled[T: Integer]: fun -> array[u8, T.bytes * 2] => undef
~
~ main: fun
~ {
~ }
```

```errors
Cannot declare static fields in traits
'u16' needs 'Integer.bits'
'bits' doesn't match 'Integer.bits'
Type 'T' has no member 'bits'
Cannot use arithmetic on value parameters in generic arguments
```

Extension blocks and blanket implementations can declare constants too:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
i32: impl
{
	digits: const i32 = 10
	width: const i32 = digits + 1
}

u8: impl
{
	digits: const i32 = 3
}

[T]: impl
{
	size: const usize = sizeOf(T)
}

Pair: rec
{
	a: i64
	b: i64
}

columns: const i32 = i32.width * 4

main: fun
{
	printf("%d %d %d %d\n", i32.digits, i32.width, u8.digits, columns)
	printf("%zu %zu\n", u16.size, Pair.size)
}
```

```output
10 11 3 44
2 16
```
