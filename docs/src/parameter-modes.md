# Parameter modes

A parameter's mode says how an argument gets into a function. There are four: no mode gives the function its own copy, `imm` lends it the caller's value to read, `mut` lends it the caller's value to change, and `own` moves the value into the function. The mode is part of the function's signature, and the call site writes it too, so a call shows which arguments can be changed or taken away.

| Mode | The function gets | The call writes | The function can change it | Types |
| --- | --- | --- | --- | --- |
| none | a copy | `f(x)` | no | types that copy |
| `imm` | the caller's value, read-only | `f(imm x)` | no | any |
| `mut` | the caller's value | `f(mut x)` | yes, and the caller sees it | any |
| `own` | the value itself, to keep | `f(own x)` | yes | any |

Examples that need a value that can't be copied use the `File` record from [Ownership](ownership.md), with its declaration hidden: one `id` field and a destructor that prints `close` and the id.

## Copies: no mode

A parameter without a mode receives a copy of the argument. The function reads its copy, and nothing it does affects the caller:

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

main: fun
{
	val p = Point(3, 4)
	printf("%d\n", lengthSquared(p))
}
```

```output
25
```

The copy is read-only. Writing to it, or to any part of it, is an error:

```cella error
~ mod example
~
Point: rec
{
	x: i32
	y: i32
}

normalize: fun(p: Point)
{
	p.x = 0
}

main: fun
{
}
```

```errors
Cannot reassign read-only parameters
```

To get a copy the function can change, declare the parameter `own`, as described [below](#taking-ownership-with-own).

Only a type that copies can be passed this way ([Ownership](ownership.md#copying-and-moving) lists which types copy). A parameter without a mode whose type doesn't copy is an error in the declaration itself:

```cella error
~ mod example
~
~ File: rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
describe: fun(file: File)
{
}

main: fun
{
}
```

```errors
Cannot copy 'File'
```

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
~ File: rec
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
~ File: rec
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

Writing `imm` on an argument whose parameter isn't `imm` is an error too, as it is for each mode: the message names the parameter, as in "'p' isn't an 'imm' parameter".

The function can't change an `imm` parameter or move it away, since the value belongs to the caller:

```cella error
~ mod example
~
~ File: rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
archive: fun(own file: File)
{
}

rename: fun(imm file: File)
{
	file.id = 0
}

keep: fun(imm file: File)
{
	archive(own file)
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
~ File: rec
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

A function may move a value out of a `mut` parameter, but the caller expects to get a value back, so the function must put one there again before it returns, on every path. This `swap` moves both values around and leaves each parameter filled:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: rec
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
	a = own b
	b = own kept
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
~ File: rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
archive: fun(own file: File)
{
}

close: fun(mut file: File)
{
	archive(own file)
}

main: fun
{
}
```

```errors
Cannot leave 'mut' parameters moved
```

The same holds for a field moved out of a `mut` parameter, which gives "Cannot leave 'mut' parameters partly moved".

## Taking ownership with `own`

An `own` parameter moves the argument into the function. The function owns it from then on: it can change it, move it somewhere else, or let it be destroyed when the function returns. The caller writes `own` for a named value, and can't use it afterwards:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ File: rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("close %d\n", self.id)
~ 	}
~ }
~
archive: fun(own file: File)
{
	file.id += 100
	printf("archiving %d\n", file.id)
}

main: fun
{
	val file = File(1)
	archive(own file)
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

A temporary like `File(2)` moves in without `own`. [Ownership](ownership.md#moving-with-own) has the rules for moves and the errors for using a moved value.

For a type that copies, an `own` parameter is a copy that the function is allowed to change. The call site needs no `own`, and the caller's variable is unaffected:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
countDown: fun(own n: i32)
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
	val start = 3
	countDown(start)
	printf("start is still %d\n", start)
}
```

```output
3 2 1 
start is still 3
```

Writing `own` at the call is still allowed there, and then marks the variable as moved, as `own` does everywhere.

`own` can't stand in for another mode. An `own` argument to a parameter that isn't `own` is an error:

```cella error
~ mod example
~
~ File: rec
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
	describe(own file)
}
```

```errors
'file' isn't an 'own' parameter
```

## Receivers

A method's receiver, `self`, takes one of the same four modes: `self` for a copy, `imm self`, `mut self` and `own self`. The call `x.m()` doesn't repeat the mode; the method's declaration shows it. [Methods](methods.md) covers methods in full; the mode rules are the same as for parameters:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Account: rec
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

	finish: fun(own self) -> i32
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

`account.finish()` moves `account` into the method, though the call doesn't say `own`, and `account` can't be used after it. A `mut self` method needs a receiver that can be changed, so calling one on a `val` or on a temporary is an error ("Cannot mutably borrow values", "Cannot mutably borrow unstored values"). A copied `self` works only for types that copy.

## Modes in function types

A function type lists each parameter's mode along with its type: `fun[mut i32, i32]` takes an `i32` to change and an `i32` to copy. A call through a function value writes the modes as a direct call does:

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

apply: fun(action: fun[mut i32, i32], mut target: i32)
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
	val f: fun[own i32, i32] = damage
}
```

```errors
Cannot convert type 'fun[mut i32, i32]' to 'fun[own i32, i32]'
```

There is one exception: a function that takes a copy can be used where the type says `imm`, as long as the parameter's type copies. The other direction is an error. [Function values and closures](closures.md) covers function types in full.

## Overloads and modes

Two overloads can't differ only in their parameter modes:

```cella error
~ mod example
~
reset: fun(mut value: i32)
{
	value = 0
}

reset: fun(value: i32)
{
}

main: fun
{
}
```

```errors
'reset' overloads cannot differ only in parameter modes
'reset' overloads cannot differ only in parameter modes
```

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
~ File: rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
merge: fun(imm first: File, own second: File)
{
}

main: fun
{
	val file = File(1)
	merge(imm file, own file)
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
