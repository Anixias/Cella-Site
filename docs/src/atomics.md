# Atomics

An atomic operation reads or changes a value in memory as one indivisible step. When several threads use the same value, an atomic operation never sees half of another thread's write and never loses another thread's update. Cella has no atomic types. Instead, the `atomic` keyword goes in front of a pointer dereference, and turns that one access into an atomic load, store, update or compare-and-swap. Atomic types such as a counter or a flag are ordinary records built on top of it.

The examples in this chapter run on one thread, so their output is the same every time. The operations behave the same way when other threads use the memory at the same time.

## Loads and stores

`atomic *p` reads the value `p` points to atomically, and `atomic *p = v` writes it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ready: var bool = false
total: var i32 = 0

main: fun
{
	atomic *@total = 42
	atomic *@ready = true
	if atomic *@ready
		printf("total %d\n", atomic *@total)
}
```

```output
total 42
```

The pointer can be any `ptr[T]` value, such as `@total` for a global or a local, or a pointer held in a variable or a field. The keyword covers only the dereference after it, so `atomic *p * 2` loads `*p` atomically and then multiplies the result as usual.

An atomic store is a statement and has no value. Something other than a dereference after `atomic` is an error:

```cella error
~ mod example
~
main: fun
{
	var count = 1
	val copy = atomic count
}
```

```errors
Expected '*'
```

The pointer has to be a typed `ptr[T]`. A borrow, a library pointer type with its own `*` operator and an untyped `ptr` can't be dereferenced atomically:

```cella error
~ mod example
~
main: fun
{
	var count = 1
	val view = imm count
	val a = atomic *view
	val raw: ptr = ptr(@count)
	val b = atomic *raw
}
```

```errors
Cannot access values atomically through 'imm[i32]'
Cannot access values atomically through 'ptr'
```

## Updates

A compound assignment after `atomic` reads the value, combines it and writes the result back in one step. Its value is the new value:

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
	var count = 10
	val p = @count
	val a = atomic *p += 5
	val b = atomic *p -= 3
	val c = atomic *p &= 0b1100
	val d = atomic *p |= 0b0001
	val e = atomic *p ^= 0b1000
	printf("%d %d %d %d %d\n", a, b, c, d, e)
}
```

```output
15 12 12 13 5
```

The operators that can be atomic are `+=`, `-=`, `&=`, `|=`, `^=` and the wrapping `+%=` and `-%=`. Others, such as `*=` and `<<=`, are errors:

```cella error
~ mod example
~
main: fun
{
	var count = 3
	val p = @count
	atomic *p *= 2
	atomic *p <<= 1
}
```

```errors
Cannot use '*=' atomically
Cannot use '<<=' atomically
```

Which operators work depends on the type:

| Type | Atomic operators |
| --- | --- |
| integers | `+=`, `-=`, `&=`, `|=`, `^=`, `+%=`, `-%=` |
| `f32`, `f64` | `+=`, `-=` |
| `bool` | `&=`, `|=`, `^=` |
| `char` | `+=` and `-=` with an `i32` |

```cella error
~ mod example
~
main: fun
{
	var flag = true
	atomic *@flag += true
	var scale = 1.5
	atomic *@scale &= 2.0
}
```

```errors
Cannot use '+=' atomically on 'bool'
Cannot use '&=' atomically on 'f64'
```

Atomic `+=` and `-=` on integers and `char` are checked for overflow like the plain operators, and `+%=` and `-%=` wrap. [Checks and panics](panics.md#turning-checks-on-and-off) covers when overflow checks run:

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
	var small: u8 = 250
	val p = @small
	printf("%d\n", atomic *p +%= 10)
	var letter = 'a'
	atomic *@letter += 2
	printf("%c\n", atomic *@letter)
	printf("%d\n", atomic *p -= 5)
}
```

```output
4
c
Panic at main.ce:16:17: subtraction overflow
```

## Compare and swap

`atomic *p == expected = desired` stores `desired` only if the value is `expected` at that moment. Its value is a `bool` that says whether it stored:

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
	var owner = 0
	val p = @owner
	val first = atomic *p == 0 = 7
	val second = atomic *p == 0 = 9
	printf("%d %d %d\n", i32(first), i32(second), owner)
}
```

```output
1 0 7
```

The first swap finds `0` and stores `7`. The second finds `7`, so it leaves the value alone and gives `false`.

The usual pattern for an update that has no atomic operator is a loop: load the value, compute the new one, and try to swap it in. If another thread changed the value in between, the swap fails and the loop tries again:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
largest: var i32 = 0

record: fun(value: i32)
{
	loop
	{
		val seen = atomic relaxed *@largest
		if value <= seen
			ret
		if atomic *@largest == seen = value
			ret
	}
}

main: fun
{
	record(4)
	record(9)
	record(2)
	printf("%d\n", largest)
}
```

```output
9
```

Compare-and-swap compares bit patterns, not values, so for floats a NaN matches the same NaN, and `-0.0` doesn't match `0.0`:

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
	var negative = -0.0
	val swapped = atomic *@negative == 0.0 = 1.0
	printf("%d %.1f\n", i32(swapped), negative)
}
```

```output
0 -0.0
```

Without `= desired`, `==` is an ordinary comparison: `atomic *p == 7` loads `*p` atomically and compares it with `7`. Parentheses end the atomic expression, so `(atomic *p) = 5` isn't a store but an assignment to the loaded value, which is an error:

```cella error
~ mod example
~
target: var i32 = 1

main: fun
{
	val p = @target
	(atomic *p) = 5
}
```

```errors
Cannot assign to unstored values
```

## Memory orderings

On its own, an atomic operation only guarantees that the access itself is indivisible. A memory ordering also says how the operation orders the thread's other reads and writes, which is what makes a value written by one thread safe to read in another. The ordering goes between `atomic` and the dereference:

| Ordering | Meaning |
| --- | --- |
| none | Sequentially consistent: every thread sees all such operations in one order. |
| `relaxed` | Only the access itself is atomic; nothing else is ordered. |
| `acquire` | Reads and writes after the operation can't move before it. |
| `release` | Reads and writes before the operation can't move after it. |
| `acquire release` | Both. |

The typical pair is a `release` store that publishes data and an `acquire` load that sees it. A thread that reads `ready` as `true` with an acquire load also sees every write the other thread made before its release store:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
message: var i32 = 0
ready: var bool = false

publish: fun(value: i32)
{
	message = value
	atomic release *@ready = true
}

consume: fun -> i32
{
	if atomic acquire *@ready
		ret message
	ret -1
}

main: fun
{
	printf("%d\n", consume())
	publish(25)
	printf("%d\n", consume())
}
```

```output
-1
25
```

Loads take `relaxed` or `acquire`, stores take `relaxed` or `release`, and updates and compare-and-swap take any of them. With no ordering, every operation is sequentially consistent, the strongest and safest choice. Other combinations are errors:

```cella error
~ mod example
~
main: fun
{
	var count = 1
	val p = @count
	val a = atomic release *p
	atomic acquire *p = 2
	atomic acquire release *p = 3
}
```

```errors
Cannot use 'release' on atomic loads
Cannot use 'acquire' on atomic stores
Cannot use 'acquire release' on atomic stores
```

`acquire release` is always written in that order; `release acquire` is a syntax error.

## Fences

`atomic` with an ordering and nothing after it is a fence: it orders the thread's memory accesses around it without accessing anything itself. `atomic` alone is a sequentially consistent fence:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
data: var i32 = 0
flag: var bool = false

main: fun
{
	data = 7
	atomic release
	atomic relaxed *@flag = true
	if atomic relaxed *@flag
	{
		atomic acquire
		printf("%d\n", data)
	}

	atomic acquire release
	atomic
}
```

```output
7
```

A fence is a statement. `relaxed` orders nothing, so it can't be a fence:

```cella error
~ mod example
~
main: fun
{
	atomic relaxed
	val fence = atomic acquire
}
```

```errors
Cannot use 'relaxed' on fences
'atomic acquire' doesn't return a value
```

## Which types can be atomic

These types can be accessed atomically:

- integers up to 64 bits, `bool` and `char`
- `f32` and `f64`
- typed and untyped pointers, other than pointers to trait objects
- `cstr` and `ext fun` values
- enums without payloads, unless their tag is `i128` or `u128`
- tagless enums (`enum match`) over one of the types above

Records, `str`, `i128`, `u128`, enums with payloads, pointers to trait objects and `fun` values can't be:

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
	var point = Point(1, 2)
	val a = atomic *@point
	var text = "hi"
	val b = atomic *@text
	var big: i128 = 1
	val c = atomic *@big
}
```

```errors
Cannot access 'Point' values atomically
Cannot access 'str' values atomically
Cannot access 'i128' values atomically
```

Loads, stores and compare-and-swap work on every type in the list. Pointers swap like any other value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Phase: enum
{
	idle
	running
	done
}

main: fun
{
	var phase = Phase.idle
	val started = atomic *@phase == Phase.idle = Phase.running
	printf("%d %d\n", i32(started), i32(atomic *@phase))

	var first = 1
	var second = 2
	var current = @first
	atomic *@current == @first = @second
	printf("%d\n", *current)
}
```

```output
1 1
2
```

## Generic code and `T: atomic`

In a generic function or type, `atomic` works on a `T` only when `T` has the `atomic` constraint. Without it, the body is rejected:

```cella error
~ mod example
~
Slot[T]: rec
{
	value: T

	load: fun(imm self) -> T => atomic *@self.value
}

main: fun
{
}
```

```errors
Cannot access 'T' values atomically
```

With `T: atomic`, every type argument must be a type that can be accessed atomically:

```cella error
~ mod example
~
Slot[T: atomic]: rec
{
	value: T

	load: fun(imm self) -> T => atomic acquire *@self.value
}

Point: rec
{
	x: i32
}

main: fun
{
	val points = Slot[Point](Point(1))
	val wide = Slot[i128](1)
}
```

```errors
'Slot' requires 'T: atomic'
'Slot' requires 'T: atomic'
```

Each error has a note that says why, such as "'Point' can't be accessed atomically".

`T: atomic` allows loads, stores and compare-and-swap. Updates depend on the type, so they're checked where the function is used with a concrete type. A call that would apply an update to a type that doesn't support it is an error at the call:

```cella error
~ mod example
~
bump[T: atomic]: fun(target: ptr[T], amount: T) -> T => atomic *target += amount

main: fun
{
	var count = 1
	bump(@count, 2)
	var flag = false
	bump(@flag, true)
}
```

```errors
Cannot use '+=' atomically on 'bool'
```

A value that can be accessed atomically can always be copied, so `T: atomic` can't be combined with `drop`:

```cella error
~ mod example
~
keep[T: atomic + drop]: fun(own value: T)
{
}

main: fun
{
}
```

```errors
Cannot combine 'atomic' and 'drop'
Cannot combine 'atomic' and 'drop'
```

## An atomic counter type

Atomic types are records that hold the value and do every access to it through `atomic`. Methods take `imm self`, because many threads share one counter and none of them owns it exclusively; the write goes through the pointer `@self.value`, which the borrow doesn't restrict:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Atomic[T: atomic]: rec
{
	value: pvt T

	new: op(value: T)
	{
		self.value = value
	}

	load: fun(imm self) -> T => atomic acquire *@self.value

	store: fun(imm self, value: T)
	{
		atomic release *@self.value = value
	}

	add: fun(imm self, amount: T) -> T => atomic *@self.value += amount

	compareSwap: fun(imm self, expected: T, desired: T) -> bool => atomic *@self.value == expected = desired

	swap: fun(imm self, value: T) -> T
	{
		loop
		{
			val seen = atomic relaxed *@self.value
			if atomic *@self.value == seen = value
				ret seen
		}
	}
}

main: fun
{
	val hits = Atomic[u64](0)
	hits.add(3)
	hits.add(4)
	printf("%llu\n", hits.load())

	val busy = Atomic[bool](false)
	printf("%d %d\n", i32(busy.compareSwap(false, true)), i32(busy.compareSwap(false, true)))
	printf("%d %d\n", i32(busy.swap(false)), i32(busy.load()))
}
```

```output
7
1 0
1 0
```

`hits` is a `val`, and `add` still changes it. That is the point of an atomic type: the value inside changes, but the record itself is shared, never reassigned or moved.

`Atomic[bool]` is fine as long as nothing calls its `add`, since updates are checked where they're used. Adding `busy.add(true)` to the program would be "Cannot use '+=' atomically on 'bool'".
