# Pointers and raw memory

`ptr[T]` is a raw pointer to a `T`, like `T *` in C. Pointers are for the places borrows can't go: memory from an allocator, structures that point into themselves, and data shared with C. The compiler doesn't check what a pointer points to. A pointer can be null, can outlive its target, and can be freed twice, and what happens then is undefined, as in C.

## Addresses and dereferencing

`@place` gives the address of a place: a variable, a field, an array element, or a value behind another pointer. `*p` is the value `p` points to, which can be read, assigned or borrowed:

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
	var score = 10
	val p = @score
	*p += 5
	val copy = *p
	*p = 1
	printf("%d %d\n", score, copy)
}
```

```output
1 15
```

The type of `@score` is `ptr[i32]`. A pointer is plain data: it copies, it can be stored in any record or module variable, and it has no destructor.

Constants have no storage, so they have no address. Taking the address of a value that was moved away, or of a variable that hasn't been given a value, is an error too:

```cella error
~ mod example
~
Buffer: own rec
{
	id: i32

	drop: op
	{
	}
}

limit: const i32 = 4

constant: fun
{
	val p = @limit
}

moved: fun
{
	val b = Buffer(1)
	val c = own b
	val q = @b
}

unset: fun
{
	var later: Buffer
	val r = @later
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot take the address of constants
Cannot use moved values
Cannot use uninitialized values
```

[Filling `undef` storage](#filling-undef-storage) shows the one way to take the address of storage that has no value yet.

## Members through pointers

`.` looks through one pointer, like C's `->`. Fields, methods and properties of the target are reached directly, and they can be assigned, borrowed and have their address taken:

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

	sum: fun(imm self) -> i32 => self.x + self.y
}

shift: fun(p: ptr[Point], dx: i32)
{
	p.x += dx
}

grow: fun(mut n: i32) => n *= 2

main: fun
{
	var point = Point(1, 2)
	val p = @point
	shift(p, 3)
	grow(mut p.y)
	val y = @p.y
	*y += 1
	printf("%d %d %d\n", point.x, point.y, p.sum())
}
```

```output
4 5 9
```

Chains of pointers work the same way, one level per `.`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Node: rec
{
	value: i32
	next: ptr[Node]
}

main: fun
{
	val third = Node(4, null)
	val second = Node(2, @third)
	val head = Node(1, @second)
	printf("%d\n", head.value + head.next.value + head.next.next.value)
}
```

```output
7
```

`.` looks through exactly one pointer. A `ptr[ptr[Point]]` needs a `*` first, as in `(*pp).x`:

```cella error
~ mod example
~
Point: rec
{
	x: i32
}

main: fun
{
	var point = Point(1)
	val p = @point
	val pp = @p
	val x = pp.x
}
```

```errors
Type 'ptr[Point]' has no member 'x'
```

## Null

`null` is the pointer that points nowhere. It converts to every pointer type, and a pointer compares with it using `==` and `!=`. A pointer starts as null when its storage is zeroed, as in a `var` declared without a value or a record built with `T()`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Node: rec
{
	value: i32
	next: ptr[Node]
}

length: fun(head: ptr[Node]) -> i32
{
	var count = 0
	var node = head
	while node != null
	{
		count += 1
		node = node.next
	}

	ret count
}

main: fun
{
	var last: ptr[Node]
	val empty = Node()
	val second = Node(2, last)
	val first = Node(1, @second)
	printf("%d %d %d\n", length(@first), length(@empty), i32(empty.next == null))
}
```

```output
2 1 1
```

Nothing stops a null pointer from being dereferenced. Reading or writing through one is undefined and usually crashes the program, as in C.

## The untyped pointer `ptr`

`ptr` without a type argument is an untyped pointer, like C's `void *`. Every `ptr[T]` converts to `ptr` implicitly, and `ptr[T](raw)` converts back. An untyped pointer has no target type, so it can't be dereferenced, indexed or used with `.`:

```cella error
~ mod example
~
Point: rec
{
	x: i32
}

main: fun
{
	var point = Point(1)
	val raw: ptr = @point
	val value = *raw
	val x = raw.x
	val first = raw[0]
}
```

```errors
Cannot dereference untyped pointers
Type 'ptr' has no member 'x'
Cannot index into type 'ptr'
```

## Pointer arithmetic

Adding an integer to a `ptr[T]` moves it by that many elements, as in C, and subtracting one moves it back. `p[i]` is `*(p + i)`, and the index can be negative:

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
	var values = [10, 20, 30, 40]
	var p = @values[0]
	p[1] = 25
	val third = p + 2
	printf("%d %d %d %d\n", *third, third[-1], p[3], *(1 + p))
	p += 3
	p -= 1
	printf("%d\n", *p)
}
```

```output
30 25 40 25
30
```

The offset can be any integer type that converts to `isize` or `usize` without loss on every target: the integer types up to 32 bits, `isize` and `usize`. An `i64` or `u64` offset needs a conversion, as in `p + isize(n)`.

Subtracting two pointers of the same type gives the number of elements between them, as an `isize`:

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
	var values = [10, 20, 30, 40]
	val first = @values[0]
	val last = @values[3]
	val count = last - first
	printf("%lld %d %d\n", count, i32(first < last), i32(last == first + 3))
}
```

```output
3 1 1
```

Arithmetic on the untyped `ptr` counts bytes. A difference between pointers to a type of size zero has no answer, so it's an error where the size is known and a panic in generic code where it turns out to be zero:

```cella error
~ mod example
~
Empty: rec

main: fun
{
	var marks: array[Empty, 3]
	val gap = @marks[2] - @marks[0]
}
```

```errors
Cannot subtract pointers to zero-size type 'Empty'
```

## Comparing pointers

Pointers of the same type compare with `==`, `!=`, `<`, `<=`, `>` and `>=` by address. The untyped `ptr` compares with any pointer using `==` and `!=`. Pointers to different types don't compare or subtract:

```cella error
~ mod example
~
main: fun
{
	var wide: array[i64, 3]
	var small: array[i32, 3]
	val q = @wide[0]
	val p = @small[0]
	val gap = q - p
	val same = q == p
}
```

```errors
No operation defined for '-' between 'ptr[i64]' and 'ptr[i32]'
No operation defined for '==' between 'ptr[i64]' and 'ptr[i32]'
```

## Converting pointers

Conversions between pointer types are written out, except to `ptr`:

| From | To | Written |
| --- | --- | --- |
| `ptr[T]` | `ptr` | implicit, or `ptr(p)` |
| `ptr` | `ptr[T]` | `ptr[T](raw)` |
| `ptr[T]` | `ptr[U]` | `ptr[U](ptr(p))` |
| `ptr[T]` | `usize` or `isize` | `usize(p)` |
| `usize` or `isize` | `ptr[T]` | `ptr[T](address)` |
| `cstr` | `ptr[u8]` | `ptr[u8](text)` |
| `ptr[u8]` | `cstr` | `cstr(bytes)` |

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
	var value: u32 = 0x07070707
	val p = @value
	val bytes = ptr[u8](ptr(p))
	val address = usize(p)
	val again = ptr[u32](address)
	printf("%d %d\n", i32(bytes[0]), i32(*again == value))
	val text: cstr = "hello"
	val letters = ptr[u8](text)
	printf("%c\n", i32(letters[1]))
}
```

```output
7 1
e
```

Going from one typed pointer to another directly is an error:

```cella error
~ mod example
~
main: fun
{
	var value: u32 = 1
	val bytes = ptr[u8](@value)
}
```

```errors
No constructor for 'ptr[u8]' accepts argument of type 'ptr[u32]'
```

## Allocating memory

Cella has no allocator of its own. Programs call C's `malloc` and `free`, declared in an `ext` block (see [Calling C](calling-c.md)), and size the request with `sizeOf`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	malloc: fun(size: usize) -> ptr
	free: fun(memory: ptr)
}

main: fun
{
	val count: usize = 5
	val squares = ptr[i32](malloc(count * sizeOf(i32)))
	for i in 0..count
		squares[i] = i32(i * i)

	var total = 0
	for i in 0..count
		total += squares[i]

	printf("%d\n", total)
	free(squares)
}
```

```output
30
```

`squares` converts to `ptr` implicitly when it's passed to `free`.

## Values with destructors

Assigning through a pointer is an assignment like any other: `*p = v` drops the value that was there before storing the new one. Memory fresh from `malloc` holds no value yet, so dropping it would run a destructor on garbage. Four forms handle values with destructors in raw memory:

- `own *p = v` stores `v` without dropping anything first.
- `own *p` moves the value out, leaving the memory without one.
- `drop *p` runs the value's destructor in place.
- `*p = v` drops the old value, then stores `v`.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ ext
~ {
~ 	malloc: fun(size: usize) -> ptr
~ 	free: fun(memory: ptr)
~ }
~
Buffer: own rec
{
	id: i32

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

main: fun
{
	val p = ptr[Buffer](malloc(sizeOf(Buffer)))
	own *p = Buffer(1)
	*p = Buffer(2)
	val taken = own *p
	printf("took %d\n", taken.id)
	own *p = Buffer(3)
	drop *p
	free(p)
	printf("end\n")
}
```

```output
drop 1
took 2
drop 3
end
drop 2
```

The compiler doesn't track what the memory holds. After `own *p` or `drop *p`, reading `*p` again, or forgetting to destroy what's there before `free`, isn't an error.

The same forms work on fields and elements reached through a pointer, as in `own h.buffer = Buffer(4)` and `own items[0] = Buffer(5)`. `own` assignment only works through pointers, and never on compound assignments. Reading `*p` without `own` borrows the value, as a declaration does for any value the function doesn't own (see [Borrows](borrows.md)), so moving it needs `own`:

```cella error
~ mod example
~
~ ext
~ {
~ 	malloc: fun(size: usize) -> ptr
~ }
~
Buffer: own rec
{
	id: i32

	drop: op
	{
	}
}

take: fun(b: Buffer)
{
}

main: fun
{
	val p = ptr[Buffer](malloc(sizeOf(Buffer)))
	own *p = Buffer(1)
	val seen = *p
	take(*p)
	var b = Buffer(2)
	own b = Buffer(3)
	val q = ptr[i32](malloc(4))
	own *q += 1
}
```

```errors
Cannot move 'Buffer' values implicitly
Cannot assign with 'own' except through pointers
Cannot use 'own' on compound assignments
```

A generic function can do the same with a `ptr[T]` for any `T`, as in `drop *memory` on a `memory: ptr[T]` parameter. `drop *p` on a pointer to a trait object is covered in [Trait objects](trait-objects.md).

## Filling `undef` storage

A variable declared `= undef` has storage but no value (see [Variables and constants](variables.md)). Taking its address with `@` doesn't count as reading it. Once its address has been taken, the compiler treats the storage as filled, so C functions with out-parameters, like `memset`, and loops through a pointer can fill it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	memset: fun(target: ptr, value: i32, size: usize) -> ptr
}

fill: fun(target: ptr[i32]) => *target = 42

main: fun
{
	var cleared: array[i32, 4] = undef
	memset(@cleared, 0, sizeOf(array[i32, 4]))
	var counted: array[i32, 4] = undef
	val first = @counted[0]
	for i in 0..4
		first[i] = i32(i) * 3
	var answer: i32 = undef
	fill(@answer)
	printf("%d %d %d\n", cleared[3], counted[2], answer)
}
```

```output
0 6 42
```

The address of an element covers the whole array, and the address of a field covers only that field. Elements with destructors are stored with `own`, as in `own first[i] = Buffer(i32(i))`. Anything else that would read the storage before it's filled is still an error, including a `mut` borrow and a fill that happens on only some paths:

```cella error
~ mod example
~
fill: fun(target: ptr[i32]) => *target = 42

bump: fun(mut n: i32) => n += 1

Pair: rec
{
	left: i32
	right: i32
}

borrowed: fun -> i32
{
	var n: i32 = undef
	bump(mut n)
	ret 0
}

sometimes: fun(flag: bool) -> i32
{
	var x: i32 = undef
	if flag
		fill(@x)

	ret x
}

field: fun -> i32
{
	var pair: Pair = undef
	fill(@pair.left)
	ret pair.right
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot use uninitialized values
Cannot use uninitialized values
Cannot use uninitialized values
```

## `sizeOf` and `alignOf`

`sizeOf(X)` is the size of a type or of an expression's type in bytes, and `alignOf(X)` its alignment. Both are compile-time constants of type `usize`, so they can size arrays and module constants, and they print with `%zu`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Mixed: rec
{
	flag: bool
	count: u16
	total: f64
}

alignUp: fun(offset: usize, alignment: usize) -> usize => (offset + alignment - 1) / alignment * alignment

place[T]: fun(offset: usize) -> usize => alignUp(offset, alignOf(T))

main: fun
{
	val value: u16 = 7
	printf("%zu %zu %zu %zu\n", sizeOf(Mixed), alignOf(Mixed), sizeOf(value), alignOf(array[u16, 5]))
	printf("%zu %zu %zu\n", place[u8](3), place[i32](3), place[f64](3))
}
```

```output
16 8 2 2
3 4 8
```

`place` rounds an offset up to the alignment of `T`, which is what an allocator other than `malloc`, such as an arena, needs before handing out memory for a `T`. Since they're `usize`, storing them in a narrower type needs a conversion, as in `i32(sizeOf(Mixed))`. How records are laid out is covered in [Records](records.md).

## What isn't checked

The compiler doesn't follow pointers. This program compiles, and calling `dangle` returns the address of a variable that no longer exists:

```cella norun
~ mod example
~
dangle: fun -> ptr[i32]
{
	var local = 5
	ret @local
}

main: fun
{
	dangle()
}
```

None of these are errors, and all of them are undefined at run time, as in C:

- dereferencing a null or dangling pointer;
- reading or writing past the end of an allocation, through `*` or `[]`;
- freeing memory twice, or using it after `free`;
- writing through a pointer to storage that is read-only elsewhere;
- reinterpreting memory through a converted pointer.

Pointers also take no part in [ownership](ownership.md): a `ptr[T]` doesn't own its target, and nothing drops what it points to unless the code does it with `drop *p` or `own *p`. A borrow made through a pointer, like `imm *p`, counts as a borrow of a variable when `p` was taken from that variable with `@` in the same function, as in `val p = @b`. A borrow through a pointer that came back from a call, or from an allocator, is tied to nothing, so it stays usable after the memory is freed.

Structures that point into themselves, like circular lists, are built with pointers for this reason. A borrow could never point at its own record (see [Borrows](borrows.md)), but a pointer can:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Link: rec
{
	next: ptr[Link]
	prev: ptr[Link]
}

initialize: fun(mut head: Link)
{
	head.next = @head
	head.prev = @head
}

append: fun(mut head: Link, mut node: Link)
{
	node.next = @head
	node.prev = head.prev
	head.prev.next = @node
	head.prev = @node
}

length: fun(head: ptr[Link]) -> i32
{
	var total = 0
	var node = head.next
	while node != head
	{
		total += 1
		node = node.next
	}

	ret total
}

main: fun
{
	var head = Link()
	initialize(mut head)
	var first = Link()
	var second = Link()
	append(mut head, mut first)
	append(mut head, mut second)
	printf("%d\n", length(@head))
}
```

```output
2
```

The list stays correct only while `head`, `first` and `second` stay where they are. Moving any of them would leave the others pointing at the old place, and the compiler wouldn't notice.
