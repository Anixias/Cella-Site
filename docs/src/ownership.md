# Ownership and destructors

Cella has no garbage collector, and it doesn't make you free everything by hand either. Every value has exactly one owner, and when the owner goes away, so does the value. A type can declare a destructor, code that runs when one of its values goes away, so a record that holds memory or a handle can release it at the right moment without any call in the code that uses it. This chapter explains who owns a value, when destructors run, and how a value moves from one owner to another.

## One owner per value

A local variable owns the value stored in it. When the variable's scope ends, the value is destroyed. For a number that means nothing happens, but a record can say what destroying it does with a destructor, written `drop: op` in its body:

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
	id: i32

	drop: op
	{
		printf("close %d\n", self.id)
	}
}

main: fun
{
	val a = File(1)
	{
		val b = File(2)
		printf("inner block ends\n")
	}

	printf("main ends\n")
}
```

```output
inner block ends
close 2
main ends
close 1
```

`b` belongs to the inner block, so it's destroyed when that block ends. `a` lives until the end of `main`. No code calls the destructor; the compiler inserts each call where the owner's scope ends.

Most examples in this chapter use this `File` record. Later examples hide its declaration to stay short, but it's always the same: one `id` field and a destructor that prints `close` and the id.

## Destructors

A destructor is a member named `drop`, declared as `drop: op` with a body. It takes no parameters and returns nothing. Inside it, `self` is the value being destroyed, and the destructor can read and change its fields and pass it to other functions.

The usual job of a destructor is to give back something the value holds. This `Buffer` gets memory from C's `malloc` in its constructor and returns it with `free`:

```cella
~ mod example
~
ext
{
	printf: fun(format: cstr, ...) -> i32
	malloc: fun(size: usize) -> ptr
	free: fun(memory: ptr)
}

Buffer: rec
{
	data: ptr
	size: usize

	new: op(size: usize)
	{
		self.data = malloc(size)
		self.size = size
	}

	drop: op
	{
		printf("freeing %zu bytes\n", self.size)
		free(self.data)
	}
}

main: fun
{
	val small = Buffer(16)
	val large = Buffer(4096)
	printf("%zu %zu\n", small.size, large.size)
}
```

```output
16 4096
freeing 4096 bytes
freeing 16 bytes
```

A destructor can't take parameters:

```cella error
~ mod example
~
File: rec
{
	id: i32

	drop: op(force: bool)
	{
	}
}

main: fun
{
}
```

```errors
Destructors cannot take parameters
```

It can't replace `self` or move it away, since the value is being destroyed and has nowhere to go:

```cella error
~ mod example
~
Counter: rec
{
	count: i32

	drop: op
	{
		self = Counter(0)
	}
}

main: fun
{
}
```

```errors
Cannot reassign 'self' in destructors
```

```cella error
~ mod example
~
Counter: rec
{
	count: i32

	drop: op
	{
		keep(own self)
	}
}

keep: fun(own counter: Counter)
{
}

main: fun
{
}
```

```errors
Cannot move 'self' in destructors
```

Only records declare destructors, and only in the record's own body: enums, unions and `impl` blocks can't ("Cannot declare destructors in enums"). A constant can't hold a value whose type has a destructor ("Cannot store values with destructors in constants").

## When destructors run

### At the end of a scope

The values a scope owns are destroyed when it ends, in the reverse of the order they were declared. The last one created is the first one destroyed.

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
main: fun
{
	val first = File(1)
	val second = File(2)
	val third = File(3)
	printf("declared\n")
}
```

```output
declared
close 3
close 2
close 1
```

A scope can end in other ways than reaching its closing brace. `ret`, `break` and `cont` destroy every value owned by the scopes they leave, at the point where they jump:

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
find: fun(wanted: i32) -> i32
{
	val log = File(100)
	for i in 0..5
	{
		val f = File(i)
		if i == wanted
			ret i
	}

	ret -1
}

main: fun
{
	printf("found %d\n", find(1))
}
```

```output
close 0
close 1
close 100
found 1
```

Each pass through the loop body is a scope of its own, so `File(0)` is closed at the end of the first pass. The `ret` in the second pass closes `File(1)` and then `log`.

### Fields, elements and payloads

A value that contains other values destroys them along with itself. A record runs its own destructor first, while its fields are still intact, and then destroys its fields in the reverse of their declared order. An array destroys its elements from the last to the first, and an enum destroys the payload of the case it holds:

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
Log: rec
{
	primary: File
	backup: File

	drop: op
	{
		printf("log %d and %d\n", self.primary.id, self.backup.id)
	}
}

Slot: enum
{
	empty
	full(file: File)
}

main: fun
{
	val log = Log(File(1), File(2))
	val files = [File(3), File(4)]
	val slot = Slot.full(File(5))
}
```

```output
close 5
close 4
close 3
log 1 and 2
close 2
close 1
```

A record doesn't need a destructor of its own for this. A record without `drop: op` whose fields have destructors still destroys those fields when it's destroyed.

### Module variables

A module variable is owned by the program. Module variables are destroyed after `main` returns, in the reverse of the order they were declared:

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
config: val File = File(1)
output: var File = File(2)

main: fun
{
	printf("main %d %d\n", config.id, output.id)
}
```

```output
main 1 2
close 2
close 1
```

## Copying and moving

Some types copy and others move. A copy makes a second, independent value, and both the old and the new one keep working. A move hands the one value over to a new owner, and the old place can't be used anymore.

These types copy:

- Numbers, `bool` and `char`.
- `str`, `cstr` and pointers (`ptr[T]`). Copying a pointer copies the address, not what it points to.
- Function values with a plain function type, such as `fun[i32 -> i32]`.
- Records, arrays and enums whose fields, elements or payloads all copy, as long as the record has no destructor.

Everything else moves: a record with a destructor, any record, array or enum that holds a value with a destructor, and the records and enums declared `own rec` and `own enum`, which move although they have no destructor (see [Records](records.md)).

A record of plain data copies, so changing the copy leaves the original alone:

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
	val a = Point(1, 2)
	var b = a
	b.x = 5
	printf("%d %d\n", a.x, b.x)
}
```

```output
1 5
```

A value with a destructor can't be copied, since two copies would both run the destructor and, for the `Buffer` above, free the same memory twice. Cella moves it instead, and makes you say so.

## Moving with `own`

`own` in front of a named value moves it. A parameter declared `own` takes ownership of its argument, and the call site writes `own` too:

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
	printf("archiving %d\n", file.id)
}

main: fun
{
	val report = File(1)
	val notes = File(2)
	archive(own report)
	printf("back in main\n")
}
```

```output
archiving 1
close 1
back in main
close 2
```

`archive` owns the file once it's called, so the file is closed when `archive` returns, not at the end of `main`. `main` no longer owns it, so it doesn't close it a second time.

Leaving out `own` where a value with a destructor would move is an error. The move then shows in the code wherever it happens:

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

main: fun
{
	val report = File(1)
	archive(report)
}
```

```errors
Cannot move 'File' values implicitly
```

Every move out of a named place is written `own`: arguments to `own` parameters, arguments to constructors, enum payloads, elements of an array literal, the right side of an assignment, and a declaration that names its type. `val b = own a` moves `a` into a new variable `b`:

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
Pair: rec
{
	left: File
	right: File
}

main: fun
{
	val a = File(1)
	val b = File(2)
	val pair = Pair(own a, own b)
	var current = File(3)
	val next = File(4)
	current = own next
	val kept: File = own current
	printf("%d %d %d\n", pair.left.id, pair.right.id, kept.id)
}
```

```output
close 3
1 2 4
close 4
close 2
close 1
```

`current = own next` destroys `File(3)`, the value `current` held, before the new one is stored; [assignment](#assignment-destroys-the-old-value) is covered below.

A declaration without a type and without `own`, such as `val view = report`, doesn't move or copy a value with a destructor. It borrows it, which [Borrows](borrows.md) explains.

### Using a moved value

After a move, the old place holds nothing, and using it is an error. The message points to the move:

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

main: fun
{
	val report = File(1)
	archive(own report)
	archive(own report)
}
```

```errors
Cannot use moved values
```

A moved variable declared with `var` can be given a new value, and is usable again from there on:

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
	printf("archiving %d\n", file.id)
}

main: fun
{
	var current = File(1)
	archive(own current)
	current = File(2)
	printf("current %d\n", current.id)
}
```

```output
archiving 1
close 1
current 2
close 2
```

`own` also works on plain data. The value is copied as usual, and the source still counts as moved afterwards, so the same errors apply.

### What can't be moved

Only a stored value can be moved. `own` in front of a call, a literal or any other value that isn't stored anywhere is an error, since such a value has no owner to take it from; pass it without `own` instead:

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

main: fun
{
	archive(own File(1))
}
```

```errors
Cannot move unstored values
```

A module variable can't be moved out of either, since the program owns it until it exits:

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
current: var File = File(1)

archive: fun(own file: File)
{
}

main: fun
{
	archive(own current)
}
```

```errors
Cannot move module variables
```

## Returning values

`ret` moves the value it returns to the caller, without `own`. A function can create a value and hand it out:

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
open: fun(id: i32) -> File
{
	val file = File(id)
	printf("opened %d\n", id)
	ret file
}

main: fun
{
	val file = open(7)
	printf("using %d\n", file.id)
}
```

```output
opened 7
using 7
close 7
```

The file isn't closed when `open` returns, because `open` no longer owns it. Writing `ret own file` is accepted, but the compiler points out the `own` with the hint "Redundant 'own'".

Returning a field moves just that field. The rest of the value is destroyed when the function ends:

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
Pair: rec
{
	left: File
	right: File
}

leftOf: fun(own pair: Pair) -> File
{
	ret pair.left
}

main: fun
{
	val left = leftOf(Pair(File(1), File(2)))
	printf("kept %d\n", left.id)
}
```

```output
close 2
kept 1
close 1
```

## Temporaries

A value that isn't stored in a variable is a temporary: the result of a call used as an argument, a record built inline, or a call whose field is read, as in `open(1).id`. A temporary is destroyed at the end of the statement that made it, after everything else in the statement has run. Several temporaries in one statement are destroyed in the reverse of the order they were made:

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
open: fun(id: i32) -> File => File(id)

main: fun
{
	printf("ids %d %d\n", open(1).id, open(2).id)
	open(3)
	printf("end\n")
}
```

```output
ids 1 2
close 2
close 1
close 3
end
```

A call whose result is thrown away, like `open(3)` on its own line, destroys the result right away.

A temporary passed to an `own` parameter isn't destroyed at the end of the statement. It moves into the function, which then owns it.

A temporary in the condition of an `if`, `while` or `do ... while` is destroyed after the condition is checked, before the body runs. When an `is` pattern in the condition binds part of the temporary, it lives until the end of the body instead, so the binding stays valid:

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
Slot: enum
{
	empty
	full(file: File)
}

open: fun(id: i32) -> File => File(id)

main: fun
{
	if open(1).id > 0
		printf("checked\n")

	if Slot.full(File(2)) is full(val file)
		printf("bound %d\n", file.id)

	printf("end\n")
}
```

```output
close 1
checked
bound 2
close 2
end
```

## Assignment destroys the old value

Assigning to a place that already holds a value destroys the old value. The right side is computed first, then the old value is destroyed, then the new one is stored, so the right side can still read the old value:

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
Log: rec
{
	file: File
	lines: i32
}

main: fun
{
	var current = File(1)
	current = File(current.id + 1)
	printf("now %d\n", current.id)

	var log = Log(File(10), 0)
	log.file = File(11)
	printf("log %d\n", log.file.id)
}
```

```output
close 1
now 2
close 10
log 11
close 11
close 2
```

The same holds for fields, array elements and places reached through a `mut` parameter (see [Parameter modes](parameter-modes.md)). A place that holds nothing yet, such as a moved variable, has nothing to destroy, and the assignment only stores.

## Destroying a value early

`drop` destroys a value only through a pointer, as in `drop *p` (see [Pointers](pointers.md)). Variables are always destroyed by the compiler when their owner lets go of them, so `drop` on a variable is an error:

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
main: fun
{
	val file = File(1)
	drop file
}
```

```errors
Cannot use 'drop' except through pointers
```

To destroy a variable's value before the end of its scope, put the variable in a block of its own, assign it a new value, or move it into a function that takes it with `own`.

## Values moved on only some paths

A value can be moved on one path through a function and kept on another. The program then checks at run time whether to destroy it: if the move happened, the new owner destroys it, and if not, the scope's end does.

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
	printf("archiving %d\n", file.id)
}

handle: fun(important: bool)
{
	val file = File(1)
	if important
		archive(own file)

	printf("handled\n")
}

main: fun
{
	handle(true)
	handle(false)
}
```

```output
archiving 1
close 1
handled
handled
close 1
```

After the `if`, `file` might be moved, so the code after it can't use it. The error lists every move that might have happened:

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

handle: fun(important: bool) -> i32
{
	val file = File(1)
	if important
		archive(own file)

	ret file.id
}

main: fun
{
}
```

```errors
Cannot use moved values
```

In a loop, a move in one iteration leaves the value moved for the next one:

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

main: fun
{
	val file = File(1)
	for i in 0..3
		archive(own file)
}
```

```errors
Cannot use moved values
```

The message adds "Moved here in an earlier iteration". Giving the variable a new value before the next iteration fixes it:

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
	printf("archiving %d\n", file.id)
}

main: fun
{
	var file = File(1)
	for i in 2..4
	{
		archive(own file)
		file = File(i)
	}

	printf("end\n")
}
```

```output
archiving 1
close 1
archiving 2
close 2
end
close 3
```

## Moving fields out

A field can be moved out of a record on its own. The record is then partly moved: its other fields are still there and are destroyed as usual, but the record as a whole can't be used until the field is filled again:

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
Pair: rec
{
	left: File
	right: File
}

show: fun(imm pair: Pair)
{
	printf("pair %d %d\n", pair.left.id, pair.right.id)
}

main: fun
{
	var pair = Pair(File(1), File(2))
	val left = own pair.left
	printf("right is still %d\n", pair.right.id)
	pair.left = File(left.id + 10)
	show(imm pair)
}
```

```output
right is still 2
pair 11 2
close 1
close 2
close 11
```

`show` takes the pair with `imm`, which lends it to the function without moving it ([Parameter modes](parameter-modes.md) covers this). Using the whole record while a field is missing is an error:

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
Pair: rec
{
	left: File
	right: File
}

show: fun(imm pair: Pair)
{
}

main: fun
{
	val pair = Pair(File(1), File(2))
	val left = own pair.left
	show(imm pair)
}
```

```errors
Cannot use partly moved values
```

A field can't be moved out of a record that has its own destructor, because the destructor would then run on a record with a hole in it:

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
Log: rec
{
	file: File
	lines: i32

	drop: op
	{
	}
}

main: fun
{
	val log = Log(File(1), 0)
	val file = own log.file
}
```

```errors
Cannot move fields out of values with destructors
```

Array elements can be moved out the same way when the index is a constant. Moving one out at an index computed at run time is an error ([Arrays](arrays.md) covers this).

## Destructors that move fields

The one place where fields can be moved out of a record with a destructor is that destructor. The destructor can hand a field to another owner, and the fields it moves are skipped when the record's fields are destroyed afterwards:

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
	printf("archiving %d\n", file.id)
}

Log: rec
{
	file: File
	keep: bool

	drop: op
	{
		printf("log ends\n")
		if self.keep
			archive(own self.file)
	}
}

main: fun
{
	{
		val kept = Log(File(1), true)
	}

	{
		val discarded = Log(File(2), false)
	}
}
```

```output
log ends
archiving 1
close 1
log ends
close 2
```

The destructor may also put a new value into a field it moved; that value is then destroyed with the other fields. After moving a field, the destructor can't use the field, or `self` as a whole, until it's filled again ("Cannot use moved values", "Cannot use partly moved values").

## Definite initialization

A variable must hold a value before it's read. The compiler follows every path through the function, and reading a variable that might not have been given a value is an error:

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
open: fun(ready: bool) -> i32
{
	var file: File = undef
	if ready
		file = File(1)

	ret file.id
}

main: fun
{
}
```

```errors
Cannot use uninitialized values
```

A `val` declared without a value can be given one later, once on each path:

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
choose: fun(first: bool)
{
	val file: File
	if first
		file = File(1)
	else
		file = File(2)

	printf("chose %d\n", file.id)
}

main: fun
{
	choose(false)
}
```

```output
chose 2
close 2
```

A record can also be filled one field at a time. It counts as a whole value once every field is set; before that, the fields that are set can be used on their own, and the record as a whole can't:

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
Pair: rec
{
	left: File
	right: File
}

show: fun(imm pair: Pair)
{
}

main: fun
{
	var pair: Pair = undef
	pair.left = File(1)
	show(imm pair)
	pair.right = File(2)
}
```

```errors
Cannot use partly initialized values
```

The destructors follow the same tracking. Only what was given a value is destroyed, so a record left half filled when its scope ends destroys just the fields that were set:

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
Pair: rec
{
	left: File
	right: File
}

fill: fun(both: bool)
{
	var pair: Pair = undef
	pair.left = File(1)
	if both
		pair.right = File(2)

	printf("filled\n")
}

main: fun
{
	fill(true)
	fill(false)
}
```

```output
filled
close 2
close 1
filled
close 1
```

[Variables](variables.md) covers declarations without a value and `undef` in general. The rules for parameters, including what a function must do with a `mut` parameter it moves out of, are in [Parameter modes](parameter-modes.md).
