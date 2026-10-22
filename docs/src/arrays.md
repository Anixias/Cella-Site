# Arrays

An array is a fixed number of values of one type, stored one after another. Its type is `array[T, N]`: the element type `T` and the length `N`, which is part of the type and known when the program compiles. Arrays live wherever the variable holding them lives, on the stack or inside a record, and never allocate.

## Array literals

An array literal lists its elements between brackets. Its type comes from the elements:

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
	val primes = [2, 3, 5, 7]
	val scores = [1.5, 2, 4.25]
	printf("%d %f\n", primes[3], scores[1])
}
```

```output
7 2.000000
```

`primes` is an `array[i32, 4]`. The elements of `scores` are an integer and two floats, so all three become `f64` and the array is an `array[f64, 3]`. Integer literals that don't fit in an `i32` make the elements a wider type, as they would in arithmetic.

Elements that can't share one type are an error:

```cella error
~ mod example
~
main: fun
{
	val mixed = [1, "two"]
}
```

```errors
The elements of this array have incompatible types: 'i32', 'str'
```

### Writing the type

A type on the declaration gives the elements their type, and the literal must have exactly that many elements:

```cella error
~ mod example
~
main: fun
{
	val bytes: array[u8, 4] = [1, 2, 3, 4]
	val short: array[u8, 4] = [1, 2]
	val large: array[u8, 2] = [1, 300]
}
```

```errors
Cannot convert type 'array[u8, 2]' to 'array[u8, 4]'
'300' doesn't fit in 'u8'
```

An empty literal `[]` has no elements to take a type from, so it needs one from the declaration:

```cella error
~ mod example
~
main: fun
{
	val none: array[i32, 0] = []
	val unknown = []
}
```

```errors
Cannot infer the type of '[]'
```

## Indexing

`a[i]` is the element at index `i`, counting from 0. The index is a `usize`. Unsigned integers narrower than `usize` convert to it, but signed ones don't, so an `i32` index needs `usize(i)`:

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
	var counts = [0, 0, 0]
	val slot: u8 = 2
	val offset: i32 = 1
	counts[slot] = 30
	counts[usize(offset)] = 20
	counts[0] += 10
	printf("%d %d %d\n", counts[0], counts[1], counts[2])
}
```

```output
10 20 30
```

Writing to an element changes the array, so the array must be a `var`. A `val` array can't be changed through any of its elements:

```cella error
~ mod example
~
main: fun
{
	val counts = [0, 0, 0]
	counts[0] = 5
}
```

```errors
Cannot reassign values
```

### Bounds checks

An index that is a constant is checked when the program compiles:

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
	val primes = [2, 3, 5, 7]
	printf("%d\n", primes[4])
}
```

```errors
Index 4 is out of range for 'array[i32, 4]'
```

Any other index is checked when the program runs. An index past the end stops the program with a panic instead of reading memory outside the array:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
pick: fun(index: usize) -> i32
{
	val primes = [2, 3, 5, 7]
	ret primes[index]
}

main: fun
{
	printf("%d\n", pick(3))
	printf("%d\n", pick(4))
}
```

```output
7
Panic at main.ce:11:6: index out of bounds
```

The check runs in every build, release builds included. A project can turn it off with the `BoundsChecks` setting; [Checks and panics](panics.md) covers panics and that setting.

## Length

`a.length` is the number of elements, as a `usize`. Since the length is part of the type, it's the same for every value of that type:

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
	val primes = [2, 3, 5, 7]
	var sum = 0
	for i in 0..primes.length
		sum += primes[i]

	printf("%zu primes, sum %d\n", primes.length, sum)
}
```

```output
4 primes, sum 17
```

## Sizes from constants

The length in `array[T, N]` is a constant `usize`. It can be a literal, a named constant or any constant expression, including `sizeOf`. Here the arrays are fields of records, which group named values like a C `struct` ([Records](records.md) covers them):

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
slotCount: const usize = 4

Pair: rec
{
	a: i32
	b: i64
}

Inventory: rec
{
	slots: array[i32, slotCount]
	spare: array[i32, slotCount * 2]
	raw: array[u8, sizeOf(Pair)]
}

main: fun
{
	val inventory = Inventory()
	printf("%zu %zu %zu\n", inventory.slots.length, inventory.spare.length, inventory.raw.length)
}
```

```output
4 8 16
```

A variable can't be a length, even one that never changes. Constants of other integer types need a conversion:

```cella error
~ mod example
~
count: const i32 = 3

main: fun
{
	var length = 3
	var a: array[i32, length]
	var b: array[i32, count]
	var c: array[i32, usize(count)]
}
```

```errors
'length' is not a constant
Cannot convert type 'i32' to 'usize'
```

An array's size in memory is its length times its element's size, with no header or padding between elements:

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
	printf("%zu %zu %zu\n", sizeOf(array[i32, 4]), sizeOf(array[u8, 3]), sizeOf(array[i32, 0]))
}
```

```output
16 3 0
```

## Zeroed arrays

An array declared without a value starts with every element zeroed, when its element type allows it:

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
	var totals: array[f64, 3]
	totals[1] = 2.5
	printf("%.1f %.1f %.1f\n", totals[0], totals[1], totals[2])
}
```

```output
0.0 2.5 0.0
```

Numbers, `bool`, `char` and pointers start zeroed, and so do records whose fields all can, as long as they declare no constructor and no destructor. A record that declares a constructor, a `new: op` member, can't (see [Records](records.md)). An array of those starts uninitialized, and each element must be set before it's read:

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

	new: op(x: i32, y: i32)
	{
		self.x = x
		self.y = y
	}
}

main: fun
{
	var points: array[Point, 2]
	points[0] = Point(1, 2)
	printf("%d\n", points[1].x)
}
```

```errors
Cannot use uninitialized values
```

A loop that sets every element counts, as long as its bounds are constants:

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
~
~ 	new: op(x: i32, y: i32)
~ 	{
~ 		self.x = x
~ 		self.y = y
~ 	}
~ }
~
main: fun
{
	var points: array[Point, 3]
	for i in 0..3
		points[i] = Point(i32(i), i32(i) * 10)

	printf("%d %d\n", points[2].x, points[2].y)
}
```

```output
2 20
```

## The array builder

`array[T, N](make)` builds an array by calling `make` once for each index, in order from 0, and storing what it returns. `make` takes the index as a `usize` and returns a `T`. It's often a lambda (see [Function values and closures](closures.md)), and it can use the variables around it:

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
	val base = 100
	val values = array[i32, 4](fun(i) => base + i32(i) * 10)
	printf("%d %d %d %d\n", values[0], values[1], values[2], values[3])
}
```

```output
100 110 120 130
```

Any function that takes a `usize` and returns the element type works, named functions included. The builder works for every element type, including records that can't start zeroed:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Tile: rec
{
	id: i32

	new: op(id: i32)
	{
		printf("make %d\n", id)
		self.id = id
	}
}

makeTile: fun(index: usize) -> Tile => Tile(i32(index) + 1)

main: fun
{
	val tiles = array[Tile, 3](makeTile)
	printf("last %d\n", tiles[2].id)
}
```

```output
make 1
make 2
make 3
last 3
```

The function must have the right shape:

```cella error
~ mod example
~
main: fun
{
	val a = array[i32, 3](fun(i, j) => 0)
	val b = array[i32, 3](5)
}
```

```errors
'fun[usize -> i32]' takes one parameter
No constructor for 'array[i32, 3]' accepts argument of type 'integer literal'
```

## Nested arrays

An array's elements can be arrays. `array[array[i32, 3], 2]` is two rows of three, and `grid[r][c]` indexes the row, then the element in it:

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
	var grid = [[1, 2, 3], [4, 5, 6]]
	grid[1][2] = 60
	val table = array[array[i32, 3], 3](fun(r) => array[i32, 3](fun(c) => i32(r * c)))
	printf("%d %d %zu %zu\n", grid[1][2], table[2][2], grid.length, grid[0].length)
}
```

```output
60 4 2 3
```

The rows of a nested literal share one element type, so they must all have the same length. Their elements are typed together, so a float in one row makes every row `f64`:

```cella error
~ mod example
~
main: fun
{
	val ragged = [[1, 2], [3]]
}
```

```errors
The elements of this array have incompatible types: 'array[i32, 2]', 'array[i32, 1]'
```

## Copying and moving arrays

An array copies when its element type copies. Assigning it, passing it to a parameter without a mode, or returning it makes a new array with the same elements, and changing one leaves the other alone:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
doubled: fun(values: array[i32, 3]) -> array[i32, 3]
{
	var result = values
	for i in 0..3
		result[i] *= 2

	ret result
}

main: fun
{
	val original = [1, 2, 3]
	val twice = doubled(original)
	printf("%d %d\n", original[2], twice[2])
}
```

```output
3 6
```

A destructor is a `drop: op` member that runs when a value is dropped ([Ownership and destructors](ownership.md) covers them). An array of values with a destructor can't be copied, since each element has one owner. It moves instead, and its elements are dropped when the array is, last element first:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
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

keep: fun(names: array[Name, 3])
{
	printf("kept %d names\n", i32(names.length))
}

main: fun
{
	val names = [Name(1), Name(2), Name(3)]
	keep(names)
	printf("back in main\n")
}
```

```output
kept 3 names
drop 3
drop 2
drop 1
back in main
```

`keep` takes the array by value, so the array moves into it and is dropped when `keep` returns. A function that only reads the array takes it with `imm`.

A single element can be moved out, as in `keepOne(names[1])`, when the index is a constant. The moved element is dropped by its new owner, and the rest of the array is still dropped when it goes out of scope:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
keepOne: fun(name: Name)
{
	printf("kept %d\n", name.id)
}

main: fun
{
	val names = [Name(1), Name(2), Name(3)]
	keepOne(names[1])
	printf("back in main\n")
}
```

```output
kept 2
drop 2
back in main
drop 3
drop 1
```

The other elements can still be used, but the array as a whole can't, since part of it is gone. An index computed when the program runs can't be used to move an element out:

```cella error
~ mod example
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
keepOne: fun(name: Name)
{
}

keepAll: fun(names: array[Name, 3])
{
}

pick: fun(index: usize)
{
	val names = [Name(1), Name(2), Name(3)]
	keepOne(names[index])
}

main: fun
{
	val names = [Name(1), Name(2), Name(3)]
	keepOne(names[1])
	keepAll(names)
}
```

```errors
Cannot move array elements at computed indices
Cannot use partly moved values
```

[Ownership and destructors](ownership.md) covers moves and drops in general, and [Parameter modes](parameter-modes.md) covers `imm` and `mut` parameters, which let a function read or change an array without copying it.

## Looping over arrays

`for x in a` runs its body once for each element, from the first to the last. How the loop variable holds the element depends on the word before it:

| Loop | The variable | Needs |
| --- | --- | --- |
| `for x in a` | the element by value: a copy, or the element moved out of the array | `a` can be moved, for elements that don't copy |
| `for imm x in a` | a read-only borrow of the element | nothing |
| `for mut x in a` | a mutable borrow of the element | `a` can be changed |

A copy is enough for plain data. `mut` changes the elements in place:

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
	var values = [1, 2, 3]
	for mut v in values
		v *= 10

	var total = 0
	for v in values
		total += v

	var points = [Point(1, 2), Point(3, 4)]
	for mut p in points
		p.y += p.x

	printf("%d %d %d\n", total, points[0].y, points[1].y)
}
```

```output
60 3 7
```

Elements with a destructor can't be copied, so `for n in names` would move them out of the array. To look at them, the loop takes them with `imm`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
main: fun
{
	val names = [Name(4), Name(9), Name(2)]
	var best = 0
	for imm n in names
	{
		if n.id > best
			best = n.id
	}

	printf("best %d\n", best)
}
```

```output
best 9
drop 2
drop 9
drop 4
```

### Moving elements out

`for x in a` over elements that can't be copied moves each element out of the array into the loop variable. An element that the body doesn't move on is dropped at the end of its pass. If the loop ends early with `break`, the elements it didn't reach are dropped when the loop ends:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
keep: fun(n: Name)
{
	printf("keep %d\n", n.id)
}

main: fun
{
	val names = [Name(1), Name(2), Name(3), Name(4)]
	for n in names
	{
		if n.id == 3
			break

		if n.id == 1
			keep(n)
	}

	printf("after the loop\n")
}
```

```output
keep 1
drop 1
drop 2
drop 3
drop 4
after the loop
```

After the loop the array has been moved and can't be used. An array the function doesn't own, such as an `imm` parameter, can't be moved out of, so a plain `for x in a` over it borrows each element instead, as `for imm x in a` would.

### Loops over temporaries

The array can be any expression, such as a call. A temporary array lives until the loop ends, so `imm` elements stay valid for the whole loop:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
names: fun -> array[Name, 2] => [Name(7), Name(8)]

main: fun
{
	for imm n in names()
		printf("name %d\n", n.id)

	printf("done\n")
}
```

```output
name 7
name 8
drop 8
drop 7
done
```

### What the loop rejects

For an array, the word goes before the variable, never before the array:

```cella error
~ mod example
~
main: fun
{
	var counts = [1, 2, 3]
	for c in mut counts
	{
	}
}
```

```errors
Cannot use 'mut' on 'array[i32, 3]' loop sources
```

`for mut` changes the array, so the array must be a `var`:

```cella error
~ mod example
~
main: fun
{
	val fixed = [4, 5, 6]
	for mut c in fixed
		c += 1
}
```

```errors
Cannot mutably borrow values
```

Records can define their own `for` loops with loop operators; see [Operators](operators.md).
