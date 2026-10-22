# Parameter modes

A parameter's mode says how an argument gets into a function. There are three: no mode gives the function the value itself, `imm` lends it the caller's value to read, and `mut` lends it the caller's value to change. The mode is part of the function's signature, and the call site writes the borrowing modes too, so a call shows which arguments are lent and which can be changed.

| Mode | The function gets | The call writes | The function can change it | Types |
| --- | --- | --- | --- | --- |
| none | the value: a copy, or the value itself moved in | `f(x)` | yes, its own value | any |
| `imm` | the caller's value, read-only | `f(imm x)` | no | any |
| `mut` | the caller's value | `f(mut x)` | yes, and the caller sees it | any |

Examples that need a value that can't be copied use the `File` record from [Ownership](ownership.md), with its declaration hidden: one `id` field and a destructor that prints `close` and the id.

## Taking a value: no mode

A parameter without a mode takes its argument by value. For a type that copies, the function gets its own copy, and nothing it does affects the caller:

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

lengthSquared: fun(p: Point) -> i32 => p.x * p.x + p.y * p.y

countDown: fun(n: i32)
{
	while n > 0
	{
		printf("%d ", n)
		n -= 1
	}

	printf("\n")
}

main: fun
{
	val p = Point(3, 4)
	printf("%d\n", lengthSquared(p))
	val start = 3
	countDown(start)
	printf("start is still %d\n", start)
}
```

```output
25
3 2 1 
start is still 3
```

The parameter belongs to the function, so `countDown` can change `n` while the caller's `start` stays 3.

A type that can't be copied moves into the function instead. The function owns the value from then on: it can change it, move it somewhere else, or let it be destroyed when the function returns, and the caller can't use it afterwards:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
archive: fun(file: File)
{
	file.id += 100
	printf("archiving %d\n", file.id)
}

main: fun
{
	val file = File(1)
	archive(file)
	archive(File(2))
	printf("end of main\n")
}
```

```output
archiving 101
close 101
archiving 102
close 102
end of main
```

Neither call writes anything extra: the parameter already says the value is taken. [Ownership](ownership.md#moving-values) has the rules for moves and the errors for using a moved value.

## Borrowing with `imm`

An `imm` parameter borrows the argument read-only. The function reads the caller's own value, not a copy of it. The call site marks a named argument with `imm`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
describe: fun(imm file: File)
{
	printf("file %d\n", file.id)
}

main: fun
{
	val file = File(1)
	describe(imm file)
	describe(imm file)
	describe(File(2))
	printf("end of main\n")
}
```

```output
file 1
file 1
file 2
close 2
end of main
close 1
```

`main` still owns `file` after the calls, so it can lend it again, and the file is closed once, at the end of `main`. A temporary like `File(2)` needs no `imm`; it's lent for the call and destroyed at the end of the statement.

`imm` works with every type, including types that copy. An `imm i32` parameter reads the caller's variable instead of a copy of it.

Leaving out `imm` on a named argument is an error, so a borrow always shows at the call:

```cella error
~ mod example
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
describe: fun(imm file: File)
{
}

main: fun
{
	val file = File(1)
	describe(file)
}
```

```errors
Cannot borrow arguments implicitly
```

Writing `imm` on an argument whose parameter isn't `imm` is an error too, as it is for `mut`: the message names the parameter, as in "'p' isn't an 'imm' parameter".

The function can't change an `imm` parameter or move it away, since the value belongs to the caller:

```cella error
~ mod example
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
archive: fun(file: File)
{
}

rename: fun(imm file: File)
{
	file.id = 0
}

keep: fun(imm file: File)
{
	archive(file)
}

main: fun
{
}
```

```errors
Cannot reassign read-only parameters
Cannot move read-only parameters
```

## Changing the caller's value with `mut`

A `mut` parameter borrows the argument so the function can change it. Every change goes straight to the caller's value. The call site writes `mut`:

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

damage: fun(mut health: i32, amount: i32)
{
	health -= amount
}

shift: fun(mut p: Point, dx: i32)
{
	p.x += dx
	damage(mut p.y, 1)
}

main: fun
{
	var health = 10
	damage(mut health, 3)
	var p = Point(1, 5)
	shift(mut p, 10)
	var scores = [4, 5, 6]
	damage(mut scores[1], 2)
	printf("%d %d %d %d\n", health, p.x, p.y, scores[1])
}
```

```output
7 11 4 3
```

Any place that can be assigned can be passed to a `mut` parameter: a variable, a field, an array element, a value behind a [pointer](pointers.md) (`mut *p`), or another `mut` parameter, as `shift` does with `p.y`.

The caller's value must be changeable. These are errors:

```cella error
~ mod example
~
damage: fun(mut health: i32, amount: i32)
{
	health -= amount
}

implicit: fun
{
	var health = 10
	damage(health, 3)
}

fixed: fun
{
	val health = 10
	damage(mut health, 3)
}

unstored: fun
{
	damage(mut 10, 3)
}

converted: fun
{
	var health: i64 = 10
	damage(mut health, 3)
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot mutably borrow arguments implicitly
Cannot mutably borrow values
Cannot mutably borrow unstored values
Cannot mutably borrow 'i64' values as 'i32'
```

A `val` can't be changed, and a literal or the result of a call isn't stored anywhere the change could land. The argument must also have exactly the parameter's type: a value that would only convert to it can't be lent, since the function writes to it as the parameter's type.

### Replacing a `mut` parameter's value

Assigning to a `mut` parameter replaces the caller's value. As with any assignment, the old value is destroyed first:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
reopen: fun(mut file: File)
{
	file = File(file.id + 1)
}

main: fun
{
	var file = File(1)
	reopen(mut file)
	printf("now %d\n", file.id)
}
```

```output
close 1
now 2
close 2
```

A function may move a value out of a `mut` parameter, but the caller expects to get a value back, so the function must put one there again before it returns, on every path. A declaration like `val current = a` only looks at a `mut` parameter, so taking the value out is written `own a`. This `swap` moves both values around and leaves each parameter filled:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
swap: fun(mut a: File, mut b: File)
{
	val kept = own a
	a = b
	b = kept
}

main: fun
{
	var first = File(1)
	var second = File(2)
	swap(mut first, mut second)
	printf("%d %d\n", first.id, second.id)
}
```

```output
2 1
close 1
close 2
```

Leaving the parameter moved is an error:

```cella error
~ mod example
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
archive: fun(file: File)
{
}

close: fun(mut file: File)
{
	archive(file)
}

main: fun
{
}
```

```errors
Cannot leave 'mut' parameters moved
```

The same holds for a field moved out of a `mut` parameter, which gives "Cannot leave 'mut' parameters partly moved".

## Receivers

A method's receiver, `self`, takes one of the same three modes: `self` for the value itself, `imm self` and `mut self`. The call `x.m()` doesn't repeat the mode; the method's declaration shows it. [Methods](methods.md) covers methods in full; the mode rules are the same as for parameters:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Account: own rec
{
	id: i32
	balance: i32

	drop: op
	{
		printf("close %d\n", self.id)
	}

	report: fun(imm self) => printf("account %d has %d\n", self.id, self.balance)

	deposit: fun(mut self, amount: i32)
	{
		self.balance += amount
	}

	finish: fun(self) -> i32
	{
		printf("finishing %d\n", self.id)
		ret self.balance
	}
}

main: fun
{
	var account = Account(1, 10)
	account.deposit(5)
	account.report()
	val left = account.finish()
	printf("left %d\n", left)
}
```

```output
account 1 has 15
finishing 1
close 1
left 15
```

`account.finish()` moves `account` into the method, and `account` can't be used after it. For a type that copies, a `self` method gets a copy instead. A `mut self` method needs a receiver that can be changed, so calling one on a `val` or on a temporary is an error ("Cannot mutably borrow values", "Cannot mutably borrow unstored values").

## Modes in function types

A function type lists each parameter's mode along with its type: `fun[mut i32, i32]` takes an `i32` to change and an `i32` by value. A call through a function value writes the modes as a direct call does:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
damage: fun(mut health: i32, amount: i32)
{
	health -= amount
}

apply: fun(imm action: fun[mut i32, i32], mut target: i32)
{
	action(mut target, 4)
}

main: fun
{
	var health = 20
	val hurt = damage
	hurt(mut health, 3)
	apply(damage, mut health)
	printf("%d\n", health)
}
```

```output
13
```

A function converts to a function type only when the modes match:

```cella error
~ mod example
~
damage: fun(mut health: i32, amount: i32)
{
	health -= amount
}

main: fun
{
	val f: fun[i32, i32] = damage
}
```

```errors
Cannot convert type 'fun[mut i32, i32]' to 'fun[i32, i32]'
```

There is one exception: a function that takes a parameter by value can be used where the type says `imm`, as long as the parameter's type copies. The other direction is an error. [Function values and closures](closures.md) covers function types in full.

## Overloads and modes

Overloads can differ only in their parameter modes. The call's marks pick one: `f(x)` calls the overload that takes the value, `f(imm x)` the one that borrows it, and `f(mut x)` the one that changes it. A temporary has no mark and goes to the overload that takes the value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
describe: fun(file: File) => printf("taken %d\n", file.id)
describe: fun(imm file: File) => printf("lent %d\n", file.id)
describe: fun(mut file: File) => file.id += 10

main: fun
{
	var file = File(1)
	describe(mut file)
	describe(imm file)
	describe(File(2))
	describe(file)
	printf("end of main\n")
}
```

```output
lent 11
taken 2
close 2
taken 11
close 11
end of main
```

A function value picks an overload by the modes of the type it's given, as in `val look: fun[imm File] = describe`; without a type, naming an overloaded function this way is ambiguous.

Two overloads that a call could reach the same way are an error. Here a call with two temporaries would take the first argument by value under one overload and the second under the other, so neither is a better match:

```cella error
~ mod example
~
merge: fun(imm a: i32, b: i32)
{
}

merge: fun(a: i32, imm b: i32)
{
}

main: fun
{
}
```

```errors
'merge' overloads cannot accept the same arguments
'merge' overloads cannot accept the same arguments
```

Receivers and operator operands carry no marks at the call, so overloads can't differ only in the mode of `self` or of an operand:

```cella error
~ mod example
~
Point: rec
{
	x: i32

	length: fun(self) -> i32 => self.x
	length: fun(imm self) -> i32 => self.x
}

main: fun
{
}
```

```errors
'Point.length' overloads cannot differ only in parameter modes
'Point.length' overloads cannot differ only in parameter modes
```

When a [trait](traits.md) declares a member twice with different modes, a type implementing it must declare both, with exactly those modes.

## Aliasing isn't checked

The same variable can be passed to several parameters of one call, in any mix of modes. The compiler doesn't check this, and the function sees one value through each borrow. A change made through one is visible through the others at once, while a copy keeps the value from the time of the call:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
watch: fun(mut target: i32, imm seen: i32, copied: i32)
{
	target = 100
	printf("%d %d %d\n", target, seen, copied)
}

both: fun(mut a: i32, mut b: i32)
{
	a += 1
	b += 10
}

main: fun
{
	var n = 1
	watch(mut n, imm n, n)
	var m = 0
	both(mut m, mut m)
	printf("%d\n", m)
}
```

```output
100 100 1
11
```

A function that takes two `mut` parameters can't assume they're different values. Moves are still checked: a value can't be lent and moved in the same call.

```cella error
~ mod example
~
~ File: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
merge: fun(imm first: File, second: File)
{
}

main: fun
{
	val file = File(1)
	merge(imm file, file)
}
```

```errors
Cannot use moved values
```

## Evaluation order

Arguments are evaluated from left to right. An argument without a mode is read when its turn comes. A `mut` or `imm` argument runs its own expressions in that order, such as the index in `values[pick()]`, but the place itself is reached only when the call starts, after all the other arguments. A borrow is never held while other arguments run, so an argument that replaces the borrowed value doesn't leave the borrow pointing at the old one:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
pick: fun -> usize
{
	printf("pick\n")
	ret 1
}

reset: fun(mut values: array[i32, 3]) -> i32
{
	printf("reset\n")
	values = [7, 8, 9]
	ret 5
}

show: fun(value: i32, extra: i32)
{
	printf("copy %d\n", value)
}

add: fun(mut slot: i32, amount: i32)
{
	slot += amount
}

main: fun
{
	var values = [1, 2, 3]
	show(values[pick()], reset(mut values))
	values = [1, 2, 3]
	add(mut values[pick()], reset(mut values))
	printf("%d %d %d\n", values[0], values[1], values[2])
}
```

```output
pick
reset
copy 2
pick
reset
7 13 9
```

The copy reads `values[1]` before `reset` runs and sees 2. The `mut` argument evaluates `pick()` first too, but reaches `values[1]` only after `reset` has replaced the array, so `add` changes the new array's element.
