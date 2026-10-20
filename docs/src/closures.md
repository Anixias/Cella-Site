# Function values and closures

Functions are values in Cella: they can be stored in variables and fields, passed to other functions and returned from them. A *lambda* writes a function in the middle of an expression, and a lambda that uses the variables around it is a *closure*.

## Function types

A function type lists the parameter types and the result type between brackets, with `->` before the result:

| Type | A function that |
| --- | --- |
| `fun[i32, i32 -> i32]` | takes two `i32`s and returns an `i32` |
| `fun[str]` | takes a `str` and returns nothing |
| `fun[-> bool]` | takes nothing and returns a `bool` |
| `fun[]` | takes nothing and returns nothing |

A parameter can have a mode, as in a declaration: `fun[mut i32, i32]` takes its first argument as a writable borrow, and `fun[own Text -> i32]` takes over its argument (see [Parameter modes](parameter-modes.md)).

## Functions as values

A function's name, without a call, is a value of its function type:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
double: fun(x: i32) -> i32 => x * 2
triple: fun(x: i32) -> i32 => x * 3

apply: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

pick: fun(big: bool) -> fun[i32 -> i32]
{
	if big
		ret triple

	ret double
}

main: fun
{
	var f = double
	printf("%d %d\n", f(5), apply(triple, 5))
	f = pick(true)
	printf("%d %d\n", f(5), pick(false)(7))

	val table = [double, triple]
	for g in table
		printf("%d ", g(10))

	printf("\n")
}
```

```output
10 15
15 14
20 30 
```

`var f = double` gives `f` the type `fun[i32 -> i32]`. Calling a function value looks like calling a function. Function values go anywhere other values do, such as arrays, record fields and module variables:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Handler: rec
{
	name: cstr
	run: fun[i32 -> i32]
}

negate: fun(x: i32) -> i32 => -x

current: var fun[i32 -> i32] = negate

main: fun
{
	val handler = Handler("negate", negate)
	printf("%s %d %d\n", handler.name, handler.run(4), current(5))
	printf("%zu\n", sizeOf(fun[i32 -> i32]))
}
```

```output
negate -4 -5
16
```

`handler.run(4)` calls the function stored in the field. A function value is 16 bytes: the address of the code and a pointer to the data a closure carries, which is null for a plain function.

A function value always holds a function, so it can't be `null`. Function values also can't be compared, can't be passed to C's variadic functions, and a declared function can't be assigned to:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
double: fun(x: i32) -> i32 => x * 2

main: fun
{
	var f: fun[i32 -> i32] = null
	val same = double == double
	printf("%d\n", double)
	double = double
}
```

```errors
Cannot convert type 'null' to 'fun[i32 -> i32]'
No operation defined for '==' between 'fun[i32 -> i32]' and 'fun[i32 -> i32]'
Cannot pass 'fun[i32 -> i32]' values to variadic functions
Cannot reassign functions
```

### Overloaded functions

The name of an overloaded function stands for the overload whose type is expected. A local without a type waits for its uses to decide (see [Variables and constants](variables.md)):

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
half: fun(x: i32) -> i32 => x / 2
half: fun(x: f64) -> f64 => x / 2.0

apply: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

main: fun
{
	val exact: fun[f64 -> f64] = half
	val g = half
	printf("%.1f %d %d\n", exact(5.0), apply(half, 9), apply(g, 7))
}
```

```output
2.5 4 3
```

When nothing settles it, or no overload has the expected type, the name is an error:

```cella error
~ mod example
~
half: fun(x: i32) -> i32 => x / 2
half: fun(x: f64) -> f64 => x / 2.0

main: fun
{
	val g = half
	val wide: fun[i32 -> i64] = half
}
```

```errors
Reference to 'half' is ambiguous
No overload of 'half' matches 'fun[i32 -> i64]'
```

### Modes in function types

A function value with mode parameters is called the way the function is, with `mut` or `own` written at the call:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
damage: fun(mut hp: i32, amount: i32)
{
	hp -= amount
}

apply: fun(action: fun[mut i32, i32], mut target: i32)
{
	action(mut target, 4)
}

main: fun
{
	var hp = 20
	val hurt = damage
	hurt(mut hp, 3)
	apply(damage, mut hp)
	printf("%d\n", hp)
}
```

```output
13
```

The modes are part of the type: `damage` is a `fun[mut i32, i32]`, and it doesn't fit a `fun[i32, i32]`.

## `ext fun` types

`ext fun[A -> R]` is a C function pointer: the address of a function that uses C's calling convention, 8 bytes, with no closure data. It's the type for callbacks that C code calls, like `qsort`'s comparison. A function declared with `ext fun`, a function from an `ext` block and any Cella function named directly all give `ext fun` values:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	abs: fun(value: i32) -> i32
~ }
~
twice: ext fun(x: i32) -> i32 => x * 2
double: fun(x: i32) -> i32 => x * 2

applyExt: fun(f: ext fun[i32 -> i32], x: i32) -> i32 => f(x)
applyFun: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

main: fun
{
	val native: ext fun[i32 -> i32] = double
	printf("%d %d %d\n", applyExt(twice, 3), applyExt(abs, -4), native(5))
	printf("%d %d\n", applyFun(twice, 6), applyFun(abs, -7))
	printf("%zu\n", sizeOf(ext fun[i32 -> i32]))
}
```

```output
6 4 10
12 7
8
```

An `ext fun` value converts to the matching `fun` type, as `applyFun(abs, -7)` shows. The other way, a `fun` value can't become an `ext fun`, since it may be a closure:

```cella error
~ mod example
~
double: fun(x: i32) -> i32 => x * 2

main: fun
{
	val f = double
	val native: ext fun[i32 -> i32] = f
}
```

```errors
Cannot convert type 'fun[i32 -> i32]' to 'ext fun[i32 -> i32]'
```

[Calling C](calling-c.md) covers callbacks in C APIs.

## Lambdas

A lambda is a function without a name, written where it's used: `fun`, the parameters, and then `=>` and an expression or a block:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
apply: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

call: fun(f: fun[-> i32]) -> i32 => f()

run: fun(f: fun[]) => f()

main: fun
{
	printf("%d %d\n", apply(fun(x) => x * 2, 5), apply(fun(x) { ret x * x }, 5))
	printf("%d %d\n", call(fun => 42), call(fun { ret 43 }))
	run(fun { printf("ran\n") })
	run(fun => printf("ran again\n"))
}
```

```output
10 25
42 43
ran
ran again
```

A lambda with no parameters leaves out the parentheses: `fun => 42`, `fun { ... }`. A block body returns with `ret`, like a function's.

### Types come from the expected function type

A lambda passed where a function type is expected, or stored in a variable of a function type, takes its parameter types, their modes and its result type from that type. They can also be written out, as long as they match:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
bumpAll: fun(mut values: array[i32, 3], bump: fun[mut i32])
{
	for mut value in values
		bump(mut value)
}

main: fun
{
	var values = [3, 1, 2]
	bumpAll(mut values, fun(value) { value += 10 })
	bumpAll(mut values, fun(mut value: i32) { value *= 2 })
	printf("%d %d %d\n", values[0], values[1], values[2])

	val triple: fun[i32 -> i32] = fun(x) => x * 3
	val add: fun[i32, i32 -> i32] = fun(a: i32, b: i32) -> i32 => a + b
	printf("%d %d\n", triple(4), add(2, 3))
}
```

```output
26 22 24
12 5
```

In the first call, `value` is a `mut i32` because `bump` is a `fun[mut i32]`, so `value += 10` changes the array's element.

A lambda that doesn't fit the expected type is an error:

```cella error
~ mod example
~
apply: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

main: fun
{
	apply(fun(a, b) => a, 1)
	apply(fun(x: i64) => x, 1)
	apply(fun(x) => x > 0, 1)
}
```

```errors
'fun[i32 -> i32]' takes one parameter
Cannot convert type 'fun[i64]' to 'ref fun[i32 -> i32]'
Cannot convert type 'bool' to 'i32'
```

A lambda whose written parameter types don't match keeps its own type, and without `-> R` that type returns nothing, so the second error calls it a `fun[i64]`. The `ref fun` in that message is covered under [Closure types](#closure-types).

### Lambdas without an expected type

A lambda stored in a local without a type has nothing to learn its types from, other than the local's later uses. Its parameters take their types from those uses or from the lambda itself, and without `-> R` it returns nothing:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
apply: fun(f: fun[i32 -> i32], x: i32) -> i32 => f(x)

main: fun
{
	val square = fun(x: i32) -> i32 => x * x
	val greet = fun(name: cstr) => printf("hi %s\n", name)
	val triple = fun(x) => x * 3
	greet("there")
	printf("%d %d\n", square(5), apply(triple, 2))
}
```

```output
hi there
25 6
```

`triple` gets its type from `apply`, the one place it's used. When nothing gives a parameter its type, or a lambda without `-> R` has a value as its body, that's an error:

```cella error
~ mod example
~
loose: fun
{
	val identity = fun(x) => x
}

valued: fun
{
	val add = fun(x: i32) => x + 1
}

main: fun
{
}
```

```errors
Cannot infer the type of 'x'
Cannot use values as statements
```

### Lambdas and generic functions

In a call to a generic function, the other arguments settle the type parameters first, and a lambda with an expression body supplies the rest from what it returns:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
transform[T: copy, U]: fun(value: T, f: fun[T -> U]) -> U => f(value)

main: fun
{
	val next = transform(20, fun(x) => x + 1)
	val half = transform(3, fun(x) => f64(x) / 2.0)
	val wide = transform(3, fun(x) -> i64 => x)
	printf("%d %.1f %lld\n", next, half, wide)
}
```

```output
21 1.5 3
```

A block body's result isn't used for inference, so it needs `-> R`:

```cella error
~ mod example
~
transform[T: copy, U]: fun(value: T, f: fun[T -> U]) -> U => f(value)

main: fun
{
	val r = transform(2, fun(x) { ret x * 2 })
}
```

```errors
Cannot infer the return type
```

## Captures

A lambda can use the local variables and parameters of the function around it. It *captures* them, which makes it a closure:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
each: fun(values: array[i32, 3], visit: fun[i32])
{
	for value in values
		visit(value)
}

main: fun
{
	val bonus = 10
	var total = 0
	each([1, 2, 3], fun(value) { total += value + bonus })
	printf("%d\n", total)
}
```

```output
36
```

A closure captures by reference: it refers to the variable itself, not a copy. It sees the variable as it is when the closure is called, and when the variable is a `var`, it can change it, as `total += ...` does above:

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
	var scale = 2
	val scaled = fun(x: i32) -> i32 => x * scale
	scale = 3
	printf("%d\n", scaled(5))

	var count = 0
	val tick = fun
	{
		count += 1
	}

	tick()
	tick()
	printf("%d\n", count)
}
```

```output
15
2
```

A lambda inside a method can capture `self` the same way.

A closure can change only what its function could change: a `var`, a `mut` parameter, or something reached through them. It can't move a captured variable out, since the variable stays with the function that owns it:

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

call: fun(f: fun[-> i32]) -> i32 => f()

consume: fun(own text: Text)
{
}

watch: fun(limit: i32) -> i32 => call(fun -> i32
{
	limit = 2
	ret limit
})

change: fun
{
	val base = 10
	call(fun -> i32
	{
		base = 5
		ret 0
	})
}

take: fun
{
	val text = Text(1)
	call(fun -> i32
	{
		consume(own text)
		ret 0
	})
}

main: fun
{
}
```

```errors
Cannot reassign read-only parameters
Cannot reassign values
Cannot move captured variables
```

### Closure types

A closure borrows the variables it captures, so it's a borrow itself, and a local that holds one has the type `ref fun[A -> R]`. A plain function fits a `ref fun` too. A `ref fun` follows the rules for borrows: it can be held in locals and in the fields of a `ref rec` (see [Borrows](borrows.md)), but not in a plain record or a module variable, and it doesn't convert to `fun`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Ticker: ref rec
{
	next: ref fun[-> i32]
}

triple: fun(x: i32) -> i32 => x * 3

main: fun
{
	var count = 0
	val ticker = Ticker(fun -> i32
	{
		count += 1
		ret count
	})

	ticker.next()
	val widened: ref fun[i32 -> i32] = triple
	val base = 4
	val steps: array[ref fun[-> i32], 2] = [fun => base, fun => count]
	printf("%d %d %d %d\n", ticker.next(), widened(2), steps[0](), steps[1]())
}
```

```output
2 6 4 2
```

A lambda that captures nothing is a plain function, of type `fun[...]`.

```cella error
~ mod example
~
Plain: rec
{
	run: ref fun[]
}

saved: var ref fun[] = fun { }

main: fun
{
	val base = 1
	val closure = fun -> i32 => base
	val plain: fun[-> i32] = closure
}
```

```errors
Cannot store borrows in records that aren't 'ref'
Cannot store borrows in module variables
Cannot convert type 'ref fun[-> i32]' to 'fun[-> i32]'
```

Parameters are never written as `ref fun`. Unlike other parameters without a mode, which take a copy (see [Parameter modes](parameter-modes.md)), a `fun[...]` parameter without a mode borrows its argument for the call, as `imm` does. That's why it accepts closures, and why the function can call it but can't keep it:

```cella error
~ mod example
~
zero: fun -> i32 => 0

saved: var fun[-> i32] = zero

visit: fun(f: ref fun[i32])
{
}

keep: fun(f: fun[-> i32])
{
	saved = f
}

main: fun
{
}
```

```errors
Cannot use borrow types for parameters
Cannot move read-only parameters
```

### Where closures can go

Since a closure borrows its captures, it can't outlive them. It can't be returned from the function that made it, or stored anywhere that lasts longer than its captures, and it can't be used after a captured variable is moved away:

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

Holder: ref rec
{
	run: ref fun[]
}

consume: fun(own text: Text)
{
}

make: fun -> ref fun[-> i32]
{
	val base = 1
	ret fun => base
}

store: fun(mut holder: Holder)
{
	val base = 1
	holder.run = fun { val copy = base }
}

main: fun
{
	val text = Text(1)
	val show = fun -> i32 => text.id
	consume(own text)
	show()
}
```

```errors
Cannot return closures that capture variables
Cannot store new borrows in 'mut' parameters
Cannot use borrows of moved values
```

A parameter with `own` keeps what it's given, so it accepts plain functions but no closures that capture. Neither does an `ext fun`, which has no room for captured data:

```cella error
~ mod example
~
~ ext
~ {
~ 	qsort: fun(base: ptr, count: usize, size: usize, compare: ext fun[ptr[i32], ptr[i32] -> i32])
~ }
~
store: fun(own f: fun[i32 -> i32])
{
}

main: fun
{
	val base = 10
	store(fun(x) => x + base)
	var values = [3, 1, 2]
	qsort(@values, 3, 4, fun(a, b) => (*a - *b) * base)
}
```

```errors
Cannot capture 'base' in 'fun[i32 -> i32]'
Cannot capture 'base' in 'ext fun[ptr[i32], ptr[i32] -> i32]'
```

The same lambdas without `base` work in both places. To keep a closure past the function that made it, make it an owned closure, below.

## Closures in loops

A closure made in a loop's body can capture the loop's variable, and can be used during that pass:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
apply: fun(f: fun[-> i32]) -> i32 => f()

main: fun
{
	val values = [10, 20, 30]
	var total = 0
	for v in values
	{
		val get = fun -> i32 => v
		total += get() + apply(fun -> i32 => v)
	}

	printf("%d\n", total)
}
```

```output
120
```

Each pass has its own variables, which end with the pass, so a closure from one pass can't be used in a later one or after the loop:

```cella error
~ mod example
~
main: fun -> i32
{
	var later: ref fun[-> i32] = fun => 0
	for i in 0..3
		later = fun => i

	ret later()
}
```

```errors
Cannot use closures from an earlier loop iteration
```

## Owned closures

`own fun` makes a closure that holds its captures itself instead of borrowing them, so it can live on after the variables it used are gone. It takes each capture in by its kind:

- a `val` or a parameter is copied;
- a value with a destructor is moved in, and dropped with the closure;
- a `var` is taken over: the closure owns it from then on, and the function can't use it again until it assigns a new value.

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
	var step = 3
	val add = own fun(x: i32) -> i32 => x + step
	step = 100
	printf("%d %d\n", add(1), step)

	var count = 10
	val next = own fun -> i32
	{
		count += 1
		ret count
	}

	next()
	printf("%d\n", next())
}
```

```output
4 100
12
```

`add` has its own `step`, still 3, and the function's `step` is a new value. `next` keeps its `count` between calls. Using `count` in `main` after the closure took it is an error:

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
	var total = 0
	val add = own fun(value: i32) { total += value }
	add(5)
	printf("%d\n", total)
}
```

```errors
Cannot use moved values
```

A captured value with a destructor lives as long as the closure:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Texture: rec
{
	id: i32

	drop: op
	{
		printf("free texture %d\n", self.id)
	}
}

main: fun
{
	val grass = Texture(7)
	val show = own fun { printf("texture %d\n", grass.id) }
	show()
	val moved = own show
	moved()
	printf("end\n")
}
```

```output
texture 7
texture 7
end
free texture 7
```

An owned closure is moved like any value with a destructor, with `own`. Its type has no name: each `own fun` lambda has a type of its own, so two of them can't be stored in the same variable, and one doesn't convert to `fun`. It can be passed to a `fun[...]` parameter, which borrows it for the call:

```cella error
~ mod example
~
main: fun
{
	val base = 1
	val other = 2
	var pick = own fun -> i32 => base
	pick = own fun -> i32 => other
	val plain: fun[-> i32] = pick
}
```

```errors
Cannot convert between 'own fun' closures
Cannot convert type 'own fun[-> i32]' to 'fun[-> i32]'
```

An owned closure copies or takes in its captures, so it can't change a captured `val`, and it can't capture a read-only parameter whose type can't be copied:

```cella error
~ mod example
~
Texture: rec
{
	id: i32

	drop: op
	{
	}
}

show: fun(imm texture: Texture)
{
	val shown = own fun { val id = texture.id }
}

main: fun
{
	val base = 1
	val step = own fun -> i32
	{
		base = 3
		ret base
	}
}
```

```errors
Cannot move read-only parameters
Cannot reassign values
```

## Function types as constraints

A function type also works as a constraint on a type parameter. `[F: fun[i32 -> i32]]` accepts any value that can be called that way: a function, an `ext fun`, a borrowing closure or an owned one. Generic code can call it, and keep it in a field:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	abs: fun(value: i32) -> i32
~ }
~
twice[F: fun[i32 -> i32]]: fun(imm f: F, x: i32) -> i32 => f(f(x))

Counter[F: fun[-> i32]]: rec
{
	next: F

	take: fun(imm self) -> i32 => self.next() * 10
}

double: fun(x: i32) -> i32 => x * 2

main: fun
{
	val step = 3
	printf("%d %d %d ", twice(double, 1), twice(abs, -5), twice(fun(x) => x + step, 1))
	printf("%d\n", twice(own fun(x: i32) -> i32 => x * step, 1))

	var count = 0
	val counter = Counter(own fun -> i32
	{
		count += 1
		ret count
	})

	counter.next()
	printf("%d %d\n", counter.next(), counter.take())
}
```

```output
4 5 7 9
2 30
```

`Counter` holds an owned closure without knowing its type, which is how a record keeps one. [Generics](generics.md) covers constraints in general.

A value that doesn't fit the function type is an error at the call:

```cella error
~ mod example
~
twice[F: fun[i32 -> i32]]: fun(imm f: F, x: i32) -> i32 => f(f(x))

main: fun
{
	val wrong = twice(5, 1)
	val fewer = twice(fun => 4, 1)
}
```

```errors
'twice' requires 'F: fun[i32 -> i32]'
'fun[i32 -> i32]' takes one parameter
```

## Calling through `*`

A call looks through a type's dereference operator (see [Operators](operators.md)). When `*v` gives a function, `v(...)` calls it, the same as `(*v)(...)`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Logged: rec
{
	callback: fun[i32 -> i32]

	*: op(imm self) -> imm[fun[i32 -> i32]]
	{
		printf("call ")
		ret imm self.callback
	}
}

double: fun(x: i32) -> i32 => x * 2

main: fun
{
	val f = Logged(double)
	printf("%d\n", f(5))
	printf("%d\n", (*f)(6))
}
```

```output
call 10
call 12
```

This is how a box type that owns a closure on the heap is called like the closure itself. A function type works as a trait, so `dyn[fun[-> i32]]` is a trait object for any function with that signature (see [Trait objects](trait-objects.md)), and a box of one can hold any owned closure. Returned from a function, it keeps the closure, and the variables the closure took over, alive:

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

	of[T: K + noref]: fun(own value: T) -> Boxed[K]
	{
		val memory = ptr[T](malloc(sizeOf(T)))
		own *memory = own value
		ret Boxed[K](memory)
	}

	*: op(imm self) -> imm[dyn[K]] => imm *self.object

	drop: op
	{
		drop *self.object
		free(self.object)
	}
}

makeCounter: fun(start: i32) -> Boxed[fun[-> i32]]
{
	var count = start
	ret Boxed[fun[-> i32]].of(own fun -> i32
	{
		count += 1
		ret count
	})
}

main: fun
{
	val next = makeCounter(10)
	next()
	val second = next()
	printf("%d %d\n", second, next())
}
```

```output
12 13
```

`Boxed.of` moves the closure into memory from `malloc`, and the destructor drops it there and frees the memory. A borrowing closure can't go into the box, because `of` requires `T: noref` and a `ref fun` holds borrows.
