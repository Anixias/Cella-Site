# Operators

Records and enums can declare their own operators. An operator member is a function written with `op` and named by its symbol, and `a + b` on that type calls it. The same form declares indexers (`v[i]`), the dereference operator (`*p`) and the operators that let `for` walk a type.

## Declaring an operator

A binary operator is a static member that takes both operands as parameters:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Vector: rec
{
	x: f64
	y: f64

	+: op(a: Vector, b: Vector) -> Vector => Vector(a.x + b.x, a.y + b.y)
	-: op(a: Vector, b: Vector) -> Vector => Vector(a.x - b.x, a.y - b.y)
}

main: fun
{
	val a = Vector(1.0, 2.0)
	val b = Vector(3.0, 5.0)
	val sum = a + b
	val difference = b - a
	printf("%.1f %.1f\n", sum.x, sum.y)
	printf("%.1f %.1f\n", difference.x, difference.y)
}
```

```output
4.0 7.0
2.0 3.0
```

The member's name is the operator, followed by a colon and `op`. The body is a block or `=>` and an expression, as for any function. Operators keep the precedence and associativity of the built-in ones (see [Operators and precedence](operator-reference.md)).

## Binary operators

These binary operators can be declared:

| Kind | Operators |
| --- | --- |
| Arithmetic | `+` `-` `*` `/` `%` |
| Wrapping | `+%` `-%` `*%` |
| Bitwise | `&` `\|` `^` |
| Shifts and rotations | `<<` `>>` `<<<` `>>>` |
| Comparisons | `==` `!=` `<` `<=` `>` `>=` |

A binary operator takes exactly two parameters, and at least one of them must have the declaring type. The other can be any type, and either one can come first, so a type can declare both `v * 2.0` and `2.0 * v`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Vector: rec
{
	x: f64
	y: f64

	*: op(v: Vector, scale: f64) -> Vector => Vector(v.x * scale, v.y * scale)
	*: op(scale: f64, v: Vector) -> Vector => Vector(v.x * scale, v.y * scale)
	==: op(a: Vector, b: Vector) -> bool => a.x == b.x && a.y == b.y
}

main: fun
{
	val v = Vector(1.0, 2.0)
	val right = v * 3.0
	val left = 3.0 * v
	val literal = v * 3
	printf("%.1f %.1f\n", right.x, right.y)
	printf("%d %d\n", i32(right == left), i32(left == literal))
}
```

```output
3.0 6.0
1 1
```

The literal `3` in `v * 3` becomes an `f64`, the type the parameter asks for, as a literal does for any call.

The rules on the parameters:

```cella error
~ mod example
~
Point: rec
{
	x: i32

	+: op(a: i32, b: i32) -> i32 => a + b
	/: op(self, other: Point) -> Point => other
	*: op(mut a: Point, b: Point) -> Point => b
	!=: op(a: Point) -> bool => true
}

main: fun
{
}
```

```errors
'+' operators need a 'Point' parameter
Cannot take 'self' in '/' operators
Cannot take 'mut' parameters in '*' operators
'!=' operators need two parameters
```

Declared comparisons chain like the built-in ones, so `a < b < c` means `a < b && b < c`, with `b` evaluated once:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Version: rec
{
	major: i32
	minor: i32

	<: op(a: Version, b: Version) -> bool => a.major < b.major || a.major == b.major && a.minor < b.minor
}

main: fun
{
	val low = Version(1, 2)
	val mid = Version(1, 10)
	val high = Version(2, 0)
	printf("%d %d\n", i32(low < mid < high), i32(mid < low < high))
}
```

```output
1 0
```

## Unary operators

`-`, `+` and `~` take one operand, which the operator receives as `self`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Flags: rec
{
	bits: u8

	~: op(self) -> Flags => Flags(~self.bits)
	-: op(self) -> Flags => Flags(0)
	-: op(a: Flags, b: Flags) -> Flags => Flags(a.bits & ~b.bits)
}

main: fun
{
	val f = Flags(0b1010)
	printf("%u %u %u\n", (~f).bits, (-f).bits, (f - Flags(0b0010)).bits)
}
```

```output
245 0 8
```

`-` and `+` can be declared both ways: with `self` as unary operators and with two parameters as binary ones. `~` is only unary. The receiver can be `self`, `imm self` or `own self`, but not `mut self`: a unary operator gives a new value and leaves its operand as it was.

Some operators can't be declared at all: `!`, `&&`, `||`, `=` and `.`.

```cella error
~ mod example
~
Point: rec
{
	x: i32

	~: op(a: Point, b: Point) -> Point => a
	-: op(mut self) -> Point => self
	!: op(self) -> Point => self
}

main: fun
{
}
```

```errors
Cannot declare '~' operators without 'self'
Cannot take 'mut self' in '-' operators
Cannot declare '!' operators
```

## Compound assignment

A compound assignment such as `+=` changes its left side in place. It takes `mut self` and one parameter, and returns nothing:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Score: rec
{
	points: i32
	bonus: i32

	+=: op(mut self, points: i32)
	{
		self.points += points
		if points >= 10
			self.bonus += 1
	}
}

main: fun
{
	var score = Score(0, 0)
	score += 5
	score += 12
	printf("%d %d\n", score.points, score.bonus)
}
```

```output
17 1
```

Every compound form of the binary operators can be declared: `+=`, `-=`, `*=`, `/=`, `%=`, `+%=`, `-%=`, `*%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`, `<<<=` and `>>>=`. Since the operator borrows its left side mutably, that side must be something that can change, such as a `var`:

```cella error
~ mod example
~
Score: rec
{
	points: i32

	+=: op(mut self, points: i32) => self.points += points
	-=: op(self, points: i32) => ret
	*=: op(mut self) => ret
	/=: op(mut self, divisor: i32) -> Score => self
}

main: fun
{
	val score = Score(0)
	score += 5
}
```

```errors
Cannot take 'self' in '-=' operators
'*=' operators need one parameter
Cannot return values from '/=' operators
Cannot mutably borrow values
```

## Nothing is derived

Each operator stands alone. Declaring `+` doesn't give `+=`, `==` doesn't give `!=`, and `<` doesn't give `>`, `<=` or `>=`. Each one a type supports has to be declared:

```cella error
~ mod example
~
Point: rec
{
	x: i32

	+: op(a: Point, b: Point) -> Point => Point(a.x + b.x)
	==: op(a: Point, b: Point) -> bool => a.x == b.x
	<: op(a: Point, b: Point) -> bool => a.x < b.x
}

main: fun
{
	var a = Point(1)
	a += Point(2)
	val different = a != Point(3)
	val greater = a > Point(0)
}
```

```errors
No operation defined for '+=' between 'Point' and 'Point'
No operation defined for '!=' between 'Point' and 'Point'
No operation defined for '>' between 'Point' and 'Point'
```

A record has no operators of its own, not even `==`. An enum whose cases have no payloads compares with `==` and `!=` already; one with payloads has neither until it declares them. Enums declare operators the same way records do:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: enum
{
	rect(width: i32, height: i32)
	square(side: i32)

	==: op(a: Shape, b: Shape) -> bool => area(a) == area(b)
	!=: op(a: Shape, b: Shape) -> bool => area(a) != area(b)
}

area: fun(shape: Shape) -> i32 => match shape
{
	rect(val w, val h) => w * h
	square(val side) => side * side
}

main: fun
{
	val a = Shape.rect(2, 8)
	val b = Shape.square(6)
	val c = Shape.square(4)
	printf("%d %d\n", i32(a == c), i32(a != b))
}
```

```output
1 1
```

## Operands and parameter modes

An operand without a mode is a copy, as for any parameter (see [Parameter modes](parameter-modes.md)). A type that can't be copied, because it has a destructor, takes its operands with `imm` to borrow them or `own` to take them over. An operand passed to an `own` parameter is written with `own` when it's a named variable, and a temporary moves in by itself:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Text: rec
{
	id: i32

	+: op(imm a: Text, imm b: Text) -> Text => Text(a.id * 10 + b.id)
	-: op(own a: Text, imm b: Text) -> Text => Text(a.id - b.id)

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

main: fun
{
	val a = Text(1)
	val b = Text(2)
	val c = a + b
	val d = own c - b
	printf("result %d\n", d.id)
}
```

```output
drop 12
result 10
drop 10
drop 2
drop 1
```

`own c` hands `c` to the operator, which drops it when it returns. A compound assignment's parameter takes modes the same way, except `mut`.

## Calling an operator through its type

`Type.op(...)` calls an operator like a static function. The operands are the arguments, receiver first, and a compound assignment's left side is passed with `mut`:

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

	-: op(self) -> Point => Point(-self.x)
	-: op(a: Point, b: Point) -> Point => Point(a.x - b.x)

	+=: op(mut self, other: Point)
	{
		self.x += other.x
	}
}

main: fun
{
	var p = Point(3)
	val negated = Point.-(p)
	val difference = Point.-(p, Point(1))
	Point.+=(mut p, Point(10))
	printf("%d %d %d\n", negated.x, difference.x, p.x)
}
```

```output
-3 2 13
```

Built-in types work the same way, so `i32.+(1, 2)` adds two `i32`s and `f64.*(1.5, 2.0)` multiplies two `f64`s:

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
	val small: i8 = 100
	var total = 7
	i32.+=(mut total, 3)
	printf("%d %d %d %.1f\n", i32.+(1, 2), i32.+(small, small), total, f64.*(1.5, 2.0))
}
```

```output
3 200 10 3.0
```

`i32.+(small, small)` converts both `i8`s to `i32` first, so the sum doesn't overflow. An operator can't be called through a value:

```cella error
~ mod example
~
Point: rec
{
	x: i32

	-: op(self) -> Point => Point(-self.x)
}

main: fun
{
	val p = Point(1)
	val negated = p.-()
}
```

```errors
Cannot call '-' through a value
```

## Ambiguous operators

Both operand types can declare an operator for the same pair. Using it is then an error, because neither declaration wins:

```cella error
~ mod example
~
Matrix: rec
{
	scale: i32

	*: op(m: Matrix, v: Vector) -> Vector => Vector(v.x * m.scale)
}

Vector: rec
{
	x: i32

	*: op(m: Matrix, v: Vector) -> Vector => Vector(v.x * m.scale + 1)
}

main: fun
{
	val product = Matrix(3) * Vector(5)
}
```

```errors
Operation '*' between 'Matrix' and 'Vector' is ambiguous
```

Calling the operator through one of the types picks its declaration:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Matrix: rec
~ {
~ 	scale: i32
~
~ 	*: op(m: Matrix, v: Vector) -> Vector => Vector(v.x * m.scale)
~ }
~
~ Vector: rec
~ {
~ 	x: i32
~
~ 	*: op(m: Matrix, v: Vector) -> Vector => Vector(v.x * m.scale + 1)
~ }
~
main: fun
{
	val a = Matrix.*(Matrix(3), Vector(5))
	val b = Vector.*(Matrix(3), Vector(5))
	printf("%d %d\n", a.x, b.x)
}
```

```output
15 16
```

Two declarations in the same type with the same parameter types conflict, and both are reported:

```cella error
~ mod example
~
Point: rec
{
	x: i32

	<: op(a: Point, b: Point) -> bool => a.x < b.x
	<: op(a: Point, b: Point) -> bool => a.x > b.x
}

main: fun
{
}
```

```errors
'Point.<' is declared more than once with the same signature
'Point.<' is declared more than once with the same signature
```

## Visibility

An operator is visible wherever its type is. `pvt` limits it to the type's own members, like any other member (see [Methods and properties](methods.md)):

```cella error
~ mod example
~
Point: rec
{
	x: i32

	*: pvt op(a: Point, b: Point) -> Point => Point(a.x * b.x)

	square: fun(self) -> Point => self * self
}

main: fun
{
	val p = Point(3)
	val squared = p.square()
	val product = p * p
}
```

```errors
'*' is private to its type
```

## Generic operators

An operator can have type parameters, written after its symbol. They must be inferable from the operands:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Box[T]: rec
{
	value: T
}

Counter: rec
{
	n: i32

	+[T: copy]: op(a: Counter, b: Box[T]) -> Counter => Counter(a.n + 1)
}

main: fun
{
	val c = Counter(0) + Box(2.5) + Box('x')
	printf("%d\n", c.n)
}
```

```output
2
```

A type parameter that only appears in the result can't be inferred, since an operator use has no place to write type arguments:

```cella error
~ mod example
~
Counter: rec
{
	n: i32

	+[T: copy]: op(a: Counter, b: Counter) -> T => undef[T]
}

main: fun
{
}
```

```errors
Cannot infer 'T' from the operands of '+'
```

Generics are covered in [Generics](generics.md).

## Indexers

An indexer makes `value[i]` work on a type. It's an operator named `[]`, and it usually comes as a pair: one with `imm self` that lends the element for reading, and one with `mut self` that lends it for writing.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Scores: rec
{
	values: array[i32, 3]

	[]: op(imm self, i: usize) -> imm[i32] => imm self.values[i]
	[]: op(mut self, i: usize) -> mut[i32] => mut self.values[i]
}

addTen: fun(mut value: i32)
{
	value += 10
}

main: fun
{
	var scores = Scores([0, 0, 0])
	scores[0] = 5
	scores[1] = scores[0] * 2
	scores[2] += 7
	addTen(mut scores[2])
	printf("%d %d %d\n", scores[0], scores[1], scores[2])
}
```

```output
5 10 17
```

The read-only indexer returns `imm[T]` and the writable one `mut[T]`, borrows of the element (see [Borrows](borrows.md)). `scores[i]` then works like an array element: it can be read, assigned, changed with `+=`, passed as `mut scores[i]`, and used with `.` to reach the element's fields and methods.

### Which indexer a use picks

The compiler picks the indexer from how the element is used. Reading the element, borrowing it with `imm` or calling a method on it that doesn't change it uses the `imm self` indexer. Assigning to it, changing it with a compound assignment, passing it as `mut`, assigning to one of its fields or calling a `mut self` method on it uses the `mut self` indexer:

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
	values: array[i32, 2]

	[]: op(imm self, i: usize) -> imm[i32]
	{
		printf("read ")
		ret imm self.values[i]
	}

	[]: op(mut self, i: usize) -> mut[i32]
	{
		printf("write ")
		ret mut self.values[i]
	}
}

main: fun
{
	var logged = Logged([1, 2])
	val a = logged[0]
	logged[0] = 3
	logged[1] += 4
	val b = imm logged[1]
	printf("\n%d %d\n", a, i32(b))
}
```

```output
read write write read 
1 6
```

A type with only a writable indexer uses it for reads too, as long as the value is writable. A type with only a read-only one can't have its elements changed:

```cella error
~ mod example
~
Readings: rec
{
	values: array[i32, 2]

	[]: op(imm self, i: usize) -> imm[i32] => imm self.values[i]
}

Slots: rec
{
	values: array[i32, 2]

	[]: op(mut self, i: usize) -> mut[i32] => mut self.values[i]
}

main: fun
{
	var readings = Readings([1, 2])
	readings[0] = 5
	val slots = Slots([1, 2])
	val first = slots[0]
}
```

```errors
'Readings' has no writable '[]'
'Slots' has no read-only '[]'
```

When the writable indexer is `pvt`, the elements are read-only outside the type, while the type's own members can still write them:

```cella error
~ mod example
~
Scores: rec
{
	values: array[i32, 3]

	[]: op(imm self, i: usize) -> imm[i32] => imm self.values[i]
	[]: pvt op(mut self, i: usize) -> mut[i32] => mut self.values[i]

	reset: fun(mut self, i: usize)
	{
		self[i] = 0
	}
}

main: fun
{
	var scores = Scores([4, 5, 6])
	scores.reset(1)
	scores[0] = 9
}
```

```errors
'[]' is read-only outside its type
```

### Indexers that return values

The read-only indexer can return the element by value instead of lending it. This is how a type gives out elements that aren't stored anywhere, such as single bits:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bits: rec
{
	word: u64

	[]: op(self, i: usize) -> bool => ((self.word >> u64(i)) & 1) != 0
}

main: fun
{
	val bits = Bits(0b1010)
	printf("%d %d %d %d\n", i32(bits[0]), i32(bits[1]), i32(bits[2]), i32(bits[3]))
}
```

```output
0 1 0 1
```

A value that an indexer returns isn't stored in the type, so it can't be assigned, borrowed or changed:

```cella error
~ mod example
~
Bits: rec
{
	word: u64

	[]: op(self, i: usize) -> bool => ((self.word >> u64(i)) & 1) != 0
}

flip: fun(mut value: bool)
{
	value = !value
}

main: fun
{
	var bits = Bits(5)
	bits[0] = true
	flip(mut bits[1])
}
```

```errors
Cannot assign to unstored values
Cannot mutably borrow unstored values
```

A by-value indexer can be paired with a writable one, which handles every write while the by-value one handles reads.

### Several parameters

An indexer takes any number of parameters of any type, so `m[row, column]` and `table[color]` work:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Matrix: rec
{
	cells: array[f64, 4]

	[]: op(imm self, row: usize, column: usize) -> imm[f64] => imm self.cells[row * 2 + column]
	[]: op(mut self, row: usize, column: usize) -> mut[f64] => mut self.cells[row * 2 + column]
}

Color: enum
{
	red
	green
	blue
}

Table: rec
{
	values: array[i32, 3]

	[]: op(self, color: Color) -> i32 => self.values[usize(color)]
	[]: op(mut self, color: Color) -> mut[i32] => mut self.values[usize(color)]
}

main: fun
{
	var m = Matrix([1.0, 2.0, 3.0, 4.0])
	m[1, 0] = 7.5
	m[0, 1] *= 3.0
	printf("%.1f %.1f %.1f %.1f\n", m[0, 0], m[0, 1], m[1, 0], m[1, 1])

	var table = Table([0, 0, 0])
	table[green] = 4
	table[Color.blue] += 2
	printf("%d %d %d\n", table[red], table[green], table[blue])
}
```

```output
1.0 6.0 7.5 4.0
0 4 2
```

A bare case name like `green` works as an index because the parameter expects a `Color`.

### Indexer rules

An indexer needs a receiver and at least one parameter, and none of its parameters can be `mut`. A type has at most one read-only and one writable indexer, and the two must take the same parameters and give the same element type. The read-only one takes `self` or `imm self` and returns `imm[T]` or `T`; the writable one takes `mut self` and returns `mut[T]`:

```cella error
~ mod example
~
Grid: rec
{
	cells: array[i32, 4]

	[]: op(self, i: usize) -> imm[i32] => imm self.cells[i]
	[]: op(self, row: usize, column: usize) -> imm[i32] => imm self.cells[row * 2 + column]
}

Mixed: rec
{
	cells: array[i32, 4]

	[]: op(imm self, i: usize) -> imm[i32] => imm self.cells[i]
	[]: op(mut self, i: isize) -> mut[i32] => mut self.cells[0]
}

Wrong: rec
{
	cells: array[i32, 4]

	[]: op(mut self, i: usize) -> i32 => self.cells[i]
	[]: op(i: usize) -> i32 => 0
}

main: fun
{
}
```

```errors
'[]' with 'self' is declared more than once in 'Grid'
'[]' with 'self' is declared more than once in 'Grid'
Cannot declare '[]' operators with different parameters
Cannot declare '[]' operators with different parameters
Cannot return 'i32' from '[]' with 'mut self'
Cannot declare '[]' operators without 'self'
```

Indexing with the wrong number of arguments says how many the type takes:

```cella error
~ mod example
~
Grid: rec
{
	cells: array[i32, 4]

	[]: op(imm self, row: usize, column: usize) -> imm[i32] => imm self.cells[row * 2 + column]
}

main: fun
{
	val grid = Grid([1, 2, 3, 4])
	val cell = grid[1]
}
```

```errors
Indexing 'Grid' takes 2 arguments
```

## The dereference operator

A type that holds a pointer to a value can make `*` reach that value. The operator is `*` with a receiver and no parameters. Like indexers, it comes as a read-only form with `imm self` returning `imm[T]` and a writable form with `mut self` returning `mut[T]`:

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
Enemy: rec
{
	health: i32

	hit: fun(mut self, damage: i32) => self.health -= damage
}

EnemyBox: rec
{
	pointer: req ptr[Enemy]

	new: op(enemy: Enemy)
	{
		self.pointer = ptr[Enemy](malloc(sizeOf(Enemy)))
		*self.pointer = enemy
	}

	*: op(imm self) -> imm[Enemy] => imm *self.pointer
	*: op(mut self) -> mut[Enemy] => mut *self.pointer

	drop: op
	{
		free(self.pointer)
	}
}

main: fun
{
	var boxed = EnemyBox(Enemy(30))
	printf("%d\n", (*boxed).health)
	*boxed = Enemy(50)
	(*boxed).hit(5)
	printf("%d\n", (*boxed).health)
}
```

```output
30
45
```

The use picks the form the same way as for indexers: reads take the `imm self` one, and writes, `mut` borrows and `mut self` calls take the `mut self` one. A read-only `*` can also return its target by value, as in `*: op(imm self) -> i32`.

### `.` looks through `*`

`.` on a value whose type declares `*` reaches the target's members, so `boxed.health` means `(*boxed).health`:

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
Enemy: rec
{
	health: i32

	hit: fun(mut self, damage: i32) => self.health -= damage

	describe: fun(self) => printf("enemy %d\n", self.health)
}

EnemyBox: rec
{
	pointer: req ptr[Enemy]

	new: op(enemy: Enemy)
	{
		self.pointer = ptr[Enemy](malloc(sizeOf(Enemy)))
		*self.pointer = enemy
	}

	*: op(imm self) -> imm[Enemy] => imm *self.pointer
	*: op(mut self) -> mut[Enemy] => mut *self.pointer

	describe: fun(imm self) => printf("box\n")

	drop: op
	{
		free(self.pointer)
	}
}

main: fun
{
	var boxed = EnemyBox(Enemy(30))
	boxed.hit(5)
	boxed.health += 1
	printf("%d\n", boxed.health)
	boxed.describe()
	(*boxed).describe()
}
```

```output
26
box
enemy 26
```

The type's own members come first: `boxed.describe()` calls `EnemyBox.describe`, and `(*boxed).describe()` reaches the one on `Enemy`. `.` looks through one level only. If the target also declares `*`, its members are reached with `(*outer).field`, not `outer.field`.

### Dereference rules

`*` takes a receiver and no other parameters, and `own self` isn't allowed. A type has at most one form of each kind, and both must give the same target type:

```cella error
~ mod example
~
Holder: rec
{
	pointer: req ptr[i32]
	count: i64

	*: op(self, index: i32) -> imm[i32] => imm *self.pointer
}

Mixed: rec
{
	pointer: req ptr[i32]
	count: i64

	*: op(imm self) -> imm[i32] => imm *self.pointer
	*: op(mut self) -> mut[i64] => mut self.count
}

Swapped: rec
{
	pointer: req ptr[i32]

	*: op(self) -> mut[i32] => mut *self.pointer
}

main: fun
{
}
```

```errors
Cannot take parameters in '*' operators with 'self'
Cannot declare '*' operators with different target types
Cannot declare '*' operators with different target types
Cannot return 'mut[i32]' from '*' with 'self'
```

## Custom `for` loops

`for` walks integer ranges and arrays on its own (see [Control flow](control-flow.md) and [Arrays](arrays.md)). Any other type takes part through two operators: `for: op(mut self) -> bool` and `*`. A type with both is a *cursor*. Before each pass, the loop calls `for`; when it returns `true`, the loop reads the element with `*` and runs the body, and when it returns `false`, the loop ends.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Countdown: rec
{
	left: i32

	for: op(mut self) -> bool
	{
		self.left -= 1
		ret self.left >= 0
	}

	*: op(imm self) -> imm[i32] => imm self.left
}

main: fun
{
	for x in Countdown(3)
		printf("%d ", x)

	printf("\n")
}
```

```output
2 1 0 
```

`for` takes `mut self` and nothing else, and returns `bool`. `break`, `cont` and `ret` work as in any loop.

### Stepping a cursor in place

A cursor in a variable is copied into the loop, like an argument, so the variable doesn't change. `for x in mut c` steps the variable itself, so a loop that stops early leaves it where it stopped, and a second loop carries on from there:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Countdown: rec
~ {
~ 	left: i32
~
~ 	for: op(mut self) -> bool
~ 	{
~ 		self.left -= 1
~ 		ret self.left >= 0
~ 	}
~
~ 	*: op(imm self) -> imm[i32] => imm self.left
~ }
~
main: fun
{
	var c = Countdown(6)
	for x in c
		printf("%d ", x)

	printf("| left %d\n", c.left)

	for x in mut c
	{
		if x == 3
			break
	}

	printf("left %d\n", c.left)

	for x in mut c
		printf("%d ", x)

	printf("| left %d\n", c.left)
}
```

```output
5 4 3 2 1 0 | left 6
left 3
2 1 0 | left -1
```

A cursor with a destructor can also be moved into the loop with `for x in own c`.

### Collections

A collection hands out a cursor through `in`. `in: op(imm self) -> Cursor` makes the cursor for loops that read; a second `in: op(mut self) -> Cursor` makes one for loops that change the elements. A cursor that refers back to its collection holds a borrow of it, so it's a `ref rec` (see [Borrows](borrows.md)):

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bag: rec
{
	items: array[i32, 4]
	count: usize

	in: op(imm self) -> BagCursor => BagCursor(imm self, 0, 0)
	in: op(mut self) -> BagEditor => BagEditor(mut self, 0, 0)
}

BagCursor: ref rec
{
	bag: imm[Bag]
	current: usize
	next: usize

	for: op(mut self) -> bool
	{
		self.current = self.next
		self.next += 1
		ret self.current < self.bag.count
	}

	*: op(self) -> imm[i32] => imm self.bag.items[self.current]
}

BagEditor: ref rec
{
	bag: mut[Bag]
	current: usize
	next: usize

	for: op(mut self) -> bool
	{
		self.current = self.next
		self.next += 1
		ret self.current < self.bag.count
	}

	*: op(self) -> imm[i32] => imm self.bag.items[self.current]
	*: op(mut self) -> mut[i32] => mut self.bag.items[self.current]
}

main: fun
{
	var bag = Bag([1, 2, 3, 4], 3)
	for mut x in bag
		x += 10

	for x in bag
		printf("%d ", x)

	printf("\n")
}
```

```output
11 12 13 
```

The binding picks the `in`: `for x in bag` and `for imm x in bag` use the `imm self` one, and `for mut x in bag` uses the `mut self` one. `for x in bag` copies each element, which needs a copyable element type, while `for imm x in bag` borrows it. Writing to a `mut` binding goes through the cursor's writable `*`.

### When a loop ends

The cursor lives until the loop ends, however it ends, and is dropped then. A cursor with a destructor finds out that the loop is over, which a collection can use to check, for example, that it wasn't changed during the loop:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Countdown: rec
{
	left: i32

	for: op(mut self) -> bool
	{
		self.left -= 1
		ret self.left >= 0
	}

	*: op(imm self) -> imm[i32] => imm self.left

	drop: op
	{
		printf("[done %d]", self.left)
	}
}

find: fun(target: i32) -> i32
{
	for x in Countdown(10)
	{
		if x == target
			ret x * 2
	}

	ret -1
}

main: fun
{
	for x in Countdown(5)
	{
		if x == 3
			cont

		if x == 1
			break

		printf("%d ", x)
	}

	printf("\n")
	val found = find(4)
	printf(" %d\n", found)
}
```

```output
4 2 [done 1]
[done 4] 8
```

### Loop operator rules

`in` takes a receiver, `imm self` or `mut self` but not `own self`, and no other parameters, and returns a cursor rather than a borrow. `for` takes `mut self` only and returns `bool`. A type declares each form once:

```cella error
~ mod example
~
Steps: rec
{
	left: i32

	for: op(self) -> bool => true
	for: op(mut self, n: i32) -> bool => true
	for: op(mut self) -> i32 => 1
}

Sources: rec
{
	x: i32

	in: op(own self) -> Steps => Steps(0)
	in: op(self, extra: i32) -> Steps => Steps(extra)
	in: op(imm self) -> imm[i32] => imm self.x
}

main: fun
{
}
```

```errors
Cannot take 'self' in 'for' operators
Cannot take parameters in 'for' operators
Cannot return 'i32' from 'for' operators
Cannot take 'own self' in 'in' operators
Cannot take parameters in 'in' operators
Cannot return 'imm[i32]' from 'in' operators
```

## The `?` operator

Postfix `?` unwraps a value or leaves the function early. A type declares it as `?: op(own self) -> T` with an expression body. When a function writes `x?`, the body runs in that function: its value becomes the value of `x?`, and a `ret` in the body returns from the function that wrote `x?`.

The usual use is a result type that holds either a value or an error. `?` gives the value, or returns the error to the caller:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Result[T, E]: enum
{
	ok(value: T)
	err(error: E)

	?: op(own self) -> T => match own self
	{
		ok(own value) => value
		err(own error) => ret Result.err(own error)
	}
}

parse: fun(n: i32) -> Result[i32, i32]
{
	if n < 0
		ret Result.err(n)

	ret Result.ok(n * 2)
}

sumTwo: fun(a: i32, b: i32) -> Result[i32, i32]
{
	val total = parse(a)? + parse(b)?
	ret Result.ok(total)
}

show: fun(result: Result[i32, i32])
{
	match result
	{
		ok(val value) => printf("ok %d\n", value)
		err(val error) => printf("error %d\n", error)
	}
}

main: fun
{
	show(sumTwo(1, 2))
	show(sumTwo(-1, 2))
	show(sumTwo(1, -5))
}
```

```output
ok 6
error -1
error -5
```

In `sumTwo(-1, 2)`, `parse(-1)?` runs the `err` arm, which returns `Result.err(-1)` from `sumTwo`; `parse(2)` never runs.

The function that uses `?` must be able to return what the body returns. Using it in a function with another result type, with no result, or that never returns is an error, and so is `?` on a type that doesn't declare it:

```cella error
~ mod example
~
~ Result[T, E]: enum
~ {
~ 	ok(value: T)
~ 	err(error: E)
~
~ 	?: op(own self) -> T => match own self
~ 	{
~ 		ok(own value) => value
~ 		err(own error) => ret Result.err(own error)
~ 	}
~ }
~
parse: fun(n: i32) -> Result[i32, i32] => Result.ok(n)

plain: fun -> i32 => parse(1)?

nothing: fun
{
	val x = parse(1)?
}

number: fun -> i32
{
	val x = 5
	ret x?
}

main: fun
{
}
```

```errors
Cannot use '?' on 'Result[i32, i32]' in 'plain'
Cannot use '?' on 'Result[i32, i32]' in 'nothing'
Cannot use '?' on 'i32'
```

A `?` operator takes `own self` and nothing else, has a return type and a `=>` body, and can't be generic or required by a trait:

```cella error
~ mod example
~
Copied: enum
{
	one

	?: op(self) -> i32 => 1
}

Block: enum
{
	one

	?: op(own self) -> i32
	{
		ret 1
	}
}

Untyped: enum
{
	one

	?: op(own self) => 1
}

Fallible: trait
{
	?: op(own self) -> i32
}

main: fun
{
}
```

```errors
Cannot take 'self' in '?' operators
'?' operators need '=' and a value
'?' operators need a return type
Cannot declare '?' operators in traits
```

## Operators in traits

A trait can require operators, indexers, `*` and `in` like any other member, and generic code can then use them on a type parameter. `?` is the exception. See [Traits](traits.md).
