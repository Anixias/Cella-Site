# Trait objects

A trait object, written `dyn[Shape]`, is a value of some type that implements `Shape`, where the type is only known when the program runs. Calls through it look up the right member at run time. This chapter covers making trait objects, what can be called through them, testing which type one holds, and owning one through a pointer.

## From generics to trait objects

A function with a [trait bound](traits.md), like `report[T: Shape]`, is compiled once for each type it's called with, and each copy calls that type's members directly. That works when the type is known where the code is compiled. A trait object handles the other case: one compiled function that works on any `Shape`, whichever type it turns out to be.

A `dyn[Shape]` refers to a value that lives somewhere else, together with a table of that value's `Shape` members. A call like `shape.area()` reads the table to find the member to call:

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
	scale: fun(mut self, factor: f64)
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => 3.14159 * self.radius * self.radius
	name: fun(imm self) -> cstr => "circle"
	scale: fun(mut self, factor: f64) => self.radius *= factor
}

Square: rec impl Shape
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
	name: fun(imm self) -> cstr => "square"
	scale: fun(mut self, factor: f64) => self.side *= factor
}

report: fun(imm shape: dyn[Shape])
{
	printf("%s %.2f\n", shape.name(), shape.area())
}

double: fun(mut shape: dyn[Shape]) => shape.scale(2.0)

main: fun
{
	val circle = Circle(1.0)
	var square = Square(2.0)
	report(imm circle)
	report(imm square)
	double(mut square)
	report(imm square)
}
```

```output
circle 3.14
square 4.00
square 16.00
```

`report` and `double` are each compiled once. Since a trait object always refers to a value somewhere else, it's taken by a parameter with `imm` or `mut`, which borrows the value for the call, as described in [Parameter modes](parameter-modes.md). `double` changes `square` itself.

## Making a trait object

Passing a value to a `dyn[Shape]` parameter converts it, as above. The value must implement the trait, and the call site writes `imm` or `mut` as for any borrowed parameter. A temporary, such as `Circle(5.0)`, can be passed as it is.

`dyn[Shape](circle)` converts explicitly, and borrows `circle` read-only. `dyn[Shape](mut circle)` borrows it writably:

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
	scale: fun(mut self, factor: f64)
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius
	scale: fun(mut self, factor: f64) => self.radius *= factor
}

report: fun(imm shape: dyn[Shape]) -> f64 => shape.area()

main: fun
{
	var circle = Circle(1.0)
	val a = report(Circle(4.0))
	val b = report(imm circle)
	val c = report(dyn[Shape](circle))
	dyn[Shape](mut circle).scale(3.0)
	val d = dyn[Shape](circle).area()
	printf("%.1f %.1f %.1f %.1f\n", a, b, c, d)
}
```

```output
4.0 1.0 1.0 3.0
```

Built-in types can implement traits too, so a literal can become a trait object:

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

i32: impl Show
{
	show: fun(imm self) => printf("<%d>", self)
}

cstr: impl Show
{
	show: fun(imm self) => printf("<%s>", self)
}

display: fun(imm value: dyn[Show]) => value.show()

main: fun
{
	display(5)
	display(2 + 3)
	display("text")
	printf("\n")
}
```

```output
<5><5><text>
```

A type that doesn't implement the trait doesn't convert. A named value needs `imm` or `mut` at the call, a trait object made without `mut` is read-only, and one made from a temporary can't be kept and used after its statement ends:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
	scale: fun(mut self, factor: f64)
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius
	scale: fun(mut self, factor: f64) => self.radius *= factor
}

Point: rec
{
	x: f64
}

report: fun(imm shape: dyn[Shape]) -> f64 => shape.area()

wrongType: fun
{
	val point = Point(1.0)
	report(imm point)
}

implicit: fun
{
	val circle = Circle(1.0)
	report(circle)
}

readOnly: fun
{
	val circle = Circle(1.0)
	dyn[Shape](circle).scale(2.0)
}

unstored: fun
{
	val held = dyn[Shape](Circle(2.0))
	val area = held.area()
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot convert type 'imm[Point]' to 'dyn[Shape]'
Cannot borrow arguments implicitly
Cannot mutably borrow through read-only borrows
Cannot borrow unstored values
```

## What can be called through one

Through a `dyn[Shape]`, code can call the trait's methods and use its properties, default bodies included. A read-only trait object allows only members that take `imm self` or `self`, as with any read-only borrow. Some members can't go through the table at all: static functions, which have no value to look up; members that take or return `Self` in other places, since the type is unknown; generic methods, which have no single compiled copy; and members that take `own self`, since a trait object doesn't own its value:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
	label: fun -> i32
	same: fun(imm self, imm other: Self) -> bool
	map[T]: fun(imm self, own value: T) -> T
	take: fun(own self) -> i32
}

describe: fun(imm shape: dyn[Shape])
{
	shape.label()
	shape.same(shape)
	shape.map(1)
	shape.take()
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot use static functions through values
Cannot call 'same' through 'dyn[Shape]'
Cannot call 'map' through 'dyn[Shape]'
Cannot call 'take' through 'dyn[Shape]'
```

Members of a generic trait are called through `dyn[Write[i32]]` like any others, using the trait's own signature:

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

Console: rec impl Write[i32]
{
	count: i32

	write: fun(mut self, value: i32)
	{
		printf("%d\n", value)
		self.count += 1
	}
}

emit: fun(mut out: dyn[Write[i32]], value: i32) => out.write(imm value)

main: fun
{
	var console = Console(0)
	emit(mut console, 4)
	emit(mut console, 5)
	printf("%d\n", console.count)
}
```

```output
4
5
2
```

`Console.write` takes its value by copy, but `Write`'s requirement takes `imm value`, so the call through the trait object passes `imm value`.

## Trait objects aren't values

A `dyn[Shape]` has no fixed size, since the value it refers to can be any type. It can't be stored, returned, copied or put in an array by value. A borrow of one can: `imm[dyn[Shape]]` and `mut[dyn[Shape]]` work as locals, results and `ref rec` fields, as [Borrows](borrows.md) describes, and a value or borrow of a type that implements the trait converts to them:

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
	scale: fun(mut self, factor: f64)
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
	scale: fun(mut self, factor: f64) => self.radius *= factor
}

Square: rec impl Shape
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
	scale: fun(mut self, factor: f64) => self.side *= factor
}

Scene: ref rec
{
	focus: imm[dyn[Shape]]
}

larger: fun(imm a: Circle, imm b: Square) -> imm[dyn[Shape]]
{
	if a.area() > b.area()
		ret a

	ret b
}

main: fun
{
	var circle = Circle(1.0)
	val square = Square(2.0)
	val grow: mut[dyn[Shape]] = mut circle
	grow.scale(2.0)
	val view: imm[dyn[Shape]] = circle
	val scene = Scene(square)
	printf("%.1f %.1f %.1f\n", view.area(), scene.focus.area(), larger(imm circle, imm square).area())
}
```

```output
12.0 4.0 12.0
```

These borrows follow the usual rules: they can't outlive the value they refer to. Using `dyn[Shape]` itself as a value is an error, and so is using it in an `ext` signature, even behind a pointer:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
}

Scene: rec
{
	focus: dyn[Shape]
}

ext
{
	show: fun(shape: ptr[dyn[Shape]])
}

make: fun -> dyn[Shape] => make()

copy: fun(imm shape: dyn[Shape])
{
	val kept: dyn[Shape] = shape
	val n = sizeOf(dyn[Shape])
	val items = [shape]
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot use 'dyn[Shape]' by value
Cannot use 'dyn[Shape]' in 'ext' signatures
Cannot use 'dyn[Shape]' by value
Cannot use 'dyn[Shape]' by value
Cannot use 'dyn[Shape]' by value
Cannot use 'dyn[Shape]' by value
```

A generic function with a bound, like `measure[T: Shape]`, can pass its `T` on as a `dyn[Shape]`, but a `dyn[Shape]` can't be its `T`, since that would make `T` a type without a size:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
}

describe: fun(imm shape: dyn[Shape]) -> f64 => shape.area()

erase[T: Shape]: fun(imm value: T) -> f64 => describe(imm value)

measure[T: Shape]: fun(imm value: T) -> f64 => value.area()

again: fun(imm shape: dyn[Shape]) -> f64 => measure(imm shape)
~
~ main: fun
~ {
~ }
```

```errors
Cannot use 'dyn[Shape]' by value
```

## Required traits

When a trait requires another, as `Shape: trait req Named` does, a `dyn[Shape]` reaches `Named`'s members too, and converts to a `dyn[Named]`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Named: trait
{
	name: fun(imm self) -> cstr
}

Shape: trait req Named
{
	area: fun(imm self) -> f64
	label: fun(imm self) => printf("%s %.1f\n", self.name(), self.area())
}

Circle: rec impl Shape
{
	radius: f64

	name: fun(imm self) -> cstr => "circle"
	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
}

greet: fun(imm item: dyn[Named]) => printf("hello, %s\n", item.name())

show: fun(imm shape: dyn[Shape])
{
	shape.label()
	greet(dyn[Named](shape))
	greet(imm shape)
}

main: fun
{
	show(Circle(1.0))
}
```

```output
circle 3.0
hello, circle
hello, circle
```

The conversion only goes that way. A `dyn[Named]` might hold a type that isn't a `Shape`, so it doesn't convert to a `dyn[Shape]`:

```cella error
~ mod example
~
Named: trait
{
	name: fun(imm self) -> cstr
}

Shape: trait req Named
{
	area: fun(imm self) -> f64
}

narrow: fun(imm item: dyn[Named]) -> f64 => dyn[Shape](item).area()
~
~ main: fun
~ {
~ }
```

```errors
'dyn[Named]' doesn't implement 'Shape'
```

To find out what type a trait object holds, test for the type itself, as the next section shows.

## Testing the type

`is` and `match` test which type a trait object holds, and can bind the value as that type with a name after it. A test can look at fields as well, as `Circle(radius: > 10.0)` does. A `match` on a trait object needs an `else` arm, since any number of types can implement the trait. `match mut` and `if mut ... is` bind writable borrows, so the arm can change the value:

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
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
}

Square: rec impl Shape
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
}

Triangle: rec impl Shape
{
	base: f64
	height: f64

	area: fun(imm self) -> f64 => self.base * self.height / 2.0
}

kind: fun(imm shape: dyn[Shape]) -> cstr => match shape
{
	Circle(radius: > 10.0) => "big circle"
	Circle => "circle"
	Square => "square"
	else => "other"
}

describe: fun(imm shape: dyn[Shape])
{
	if shape is Circle c
		printf("circle of radius %.1f\n", c.radius)
	else
		printf("%s with area %.1f\n", kind(imm shape), shape.area())
}

stretch: fun(mut shape: dyn[Shape])
{
	match mut shape
	{
		Circle c => c.radius *= 2.0
		Square s => s.side += 1.0
		else => {}
	}
}

main: fun
{
	var circle = Circle(6.0)
	var square = Square(3.0)
	val triangle = Triangle(4.0, 2.0)
	describe(imm circle)
	describe(imm square)
	describe(imm triangle)
	stretch(mut circle)
	stretch(mut square)
	printf("%s %.1f %.1f\n", kind(imm circle), circle.radius, square.side)
}
```

```output
circle of radius 6.0
square with area 9.0
other with area 4.0
big circle 12.0 4.0
```

A tested type can be a generic instantiation, as in `shape is Box[Circle]`, or a type parameter, as in `shape is T`. Testing works through required traits too: a `dyn[Named]` made from a `Circle` is still a `Circle`. Patterns are covered in full in [Pattern matching](pattern-matching.md).

A type that doesn't implement the trait can never match, and a trait object can't be tested for another trait object type:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius
}

Point: rec
{
	x: f64
}

kind: fun(imm shape: dyn[Shape]) -> i32 => match shape
{
	Circle => 1
}

test: fun(imm shape: dyn[Shape]) -> bool => shape is Point

again: fun(imm shape: dyn[Shape]) -> bool => shape is dyn[Shape]
~
~ main: fun
~ {
~ }
```

```errors
This match doesn't handle every value of 'dyn[Shape]'
'Point' doesn't implement 'Shape'
Cannot test for 'dyn[Shape]'
```

## Pointers to trait objects

A `ptr[dyn[Shape]]` is a raw pointer to a value of any type that implements `Shape`, along with its table. A pointer to a `Circle` converts to one. Calls go through it with `.`, like other [pointers](pointers.md), and `sizeOf(*p)` and `alignOf(*p)` give the size and alignment of the value it points to, read from the table:

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
	scale: fun(mut self, factor: f64)
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
	scale: fun(mut self, factor: f64) => self.radius *= factor
}

Dot: rec impl Shape
{
	x: u8

	area: fun(imm self) -> f64 => 0.0
	scale: fun(mut self, factor: f64) => ret
}

main: fun
{
	var circle = Circle(1.0)
	var dot = Dot(3)
	var p: ptr[dyn[Shape]] = @circle
	p.scale(2.0)
	printf("%.1f %.1f %zu %zu\n", circle.radius, p.area(), sizeOf(*p), alignOf(*p))
	p = @dot
	printf("%.1f %zu %zu\n", (*p).area(), sizeOf(*p), alignOf(*p))
}
```

```output
2.0 12.0 8 8
0.0 1 1
```

As with any raw pointer, nothing checks that the value is still there. `*p` is still a `dyn[Shape]`, so it can't be moved out or stored by value, and since the size of each value is only known at run time, the pointer can't be indexed:

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius
}

main: fun
{
	var circle = Circle(1.0)
	val p: ptr[dyn[Shape]] = @circle
	val first = p[0]
	val moved = own *p
}
```

```errors
Cannot index into type 'ptr[dyn[Shape]]'
Cannot use 'dyn[Shape]' by value
```

## Owning a trait object

`drop *p` runs the destructor of the value a `ptr[dyn[Shape]]` points to, found through its table, and a `ptr[dyn[Shape]]` converts to a plain `ptr`, so it can be freed. With these, a record can own a trait object on the heap. `Boxed` below works for any trait: `K: trait` makes `K` a trait parameter, and `of[T: K]` takes any value whose type implements it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	malloc: fun(size: usize) -> ptr
~ 	free: fun(memory: ptr)
~ }
~
Boxed[K: trait]: rec
{
	object: pvt ptr[dyn[K]]

	of[T: K]: fun(own value: T) -> Boxed[K]
	{
		val memory = ptr[T](malloc(sizeOf(T)))
		own *memory = own value
		ret Boxed[K](memory)
	}

	*: op(imm self) -> imm[dyn[K]] => imm *self.object

	*: op(mut self) -> mut[dyn[K]] => mut *self.object

	drop: op
	{
		printf("freeing %zu bytes\n", sizeOf(*self.object))
		drop *self.object
		free(self.object)
	}
}

Shape: trait
{
	area: fun(imm self) -> f64
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
}

Label: rec
{
	id: i32

	drop: op
	{
		printf("label %d gone\n", self.id)
	}
}

Tagged: rec impl Shape
{
	label: Label
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
}

main: fun
{
	val shapes = [Boxed[Shape].of(Circle(1.0)), Boxed[Shape].of(Tagged(Label(7), 2.0))]
	for imm shape in shapes
		printf("%.1f\n", shape.area())
}
```

```output
3.0
4.0
freeing 16 bytes
label 7 gone
freeing 8 bytes
```

Each `Boxed[Shape]` has the same size whatever it holds, so values of different types fit in one array. `own *memory = own value` moves the value into memory that holds nothing yet, `*` lets `shape.area()` reach the object as a [dereference operator](operators.md), and the destructor drops the object, the `Tagged` one's `Label` included, before freeing its memory.

## Trait parameters

A type parameter declared `K: trait` takes a trait instead of a type. Inside the declaration, `dyn[K]` is a trait object of that trait, and `T: K` bounds another type parameter by it. A trait parameter can't be combined with other constraints, and its argument must be a trait:

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
}

Named: trait
{
	name: fun(imm self) -> cstr
}

Circle: rec impl Shape + Named
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius * self.radius * 3.0
	name: fun(imm self) -> cstr => "circle"
}

Square: rec impl Shape + Named
{
	side: f64

	area: fun(imm self) -> f64 => self.side * self.side
	name: fun(imm self) -> cstr => "square"
}

Pair[K: trait]: ref rec
{
	first: imm[dyn[K]]
	second: imm[dyn[K]]
}

holds[K: trait, T: K]: fun(imm item: dyn[K]) -> bool => item is T

main: fun
{
	val circle = Circle(1.0)
	val square = Square(2.0)
	val shapes = Pair[Shape](circle, square)
	val names = Pair[Named](circle, square)
	printf("%.1f %s\n", shapes.first.area() + shapes.second.area(), names.second.name())
	printf("%d %d\n", holds[Shape, Circle](imm circle), holds[Named, Circle](imm square))
}
```

```output
7.0 square
1 0
```

```cella error
~ mod example
~
Shape: trait
{
	area: fun(imm self) -> f64
}

Circle: rec impl Shape
{
	radius: f64

	area: fun(imm self) -> f64 => self.radius
}

Cell[K: trait]: rec
{
	object: ptr[dyn[K]]
}

first[K: trait + noref]: fun -> i32 => 0

second[T: dyn[Shape]]: fun(imm x: T) -> i32 => 0

main: fun
{
	val c: Cell[Circle] = undef
}
```

```errors
Cannot combine 'trait' with other constraints
Cannot combine 'trait' with other constraints
Cannot use 'dyn' types as constraints
'Circle' is not a trait
```

A bound is written with the trait itself, as `T: Shape`; `dyn[Shape]` is a type, not a constraint.
