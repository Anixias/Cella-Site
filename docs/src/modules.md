# Modules and visibility

A module is a named group of declarations. Every source file belongs to one, and a module can span any number of files. Code reaches another module's declarations through qualified names like `geometry.area` or by importing them with `use`. Visibility keywords decide who can see a declaration: its file, its module, its project, or every project that uses it.

## The `mod` line

Every source file starts with a `mod` line that names its module. Only comments and blank lines may come before it:

```cella error
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
helper: fun -> i32 => 4

mod example

main: fun
{
}
```

```errors
Module name must precede all other declarations or imports
```

A file names exactly one module, so a second `mod` line is an error, as [Lexical structure](lexical-structure.md#source-files) shows.

The name of a file and the folder it sits in don't matter to the compiler. Only the `mod` line decides which module a file belongs to; which files belong to the project is covered in [Projects and building](projects.md#what-a-project-is). By convention, a file in `game/physics/` declares `mod game.physics`.

## Modules across files

All files with the same `mod` line form one module. Their declarations are visible to each other as if they were written in one file, so `main.ce` here calls `twice` from `helpers.ce` without anything extra:

```cella group=sameModule file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d\n", twice(21))
}
```

```cella group=sameModule file=helpers.ce
mod example

twice: fun(n: i32) -> i32 => n * 2
```

```output
42
```

Declaration order doesn't matter within a file, and it doesn't matter across files either.

## Qualified names

A declaration in another module is reached by writing the module's name, a `.`, and the declaration's name. This works for functions, types, constants, module variables and enum cases alike:

```cella group=qualified file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	val p = geometry.Point(3, 4)
	printf("%d %d\n", geometry.area(2, 3), geometry.sides)
	printf("%d\n", geometry.distance(p))
	val shape = geometry.Shape.square
	printf("%d\n", shape == geometry.Shape.circle)
}
```

```cella group=qualified file=geometry.ce
mod geometry

sides: const i32 = 4

Point: rec
{
	x: i32
	y: i32
}

Shape: enum
{
	circle
	square
}

area: fun(w: i32, h: i32) -> i32 => w * h
distance: fun(p: Point) -> i32 => p.x + p.y
```

```output
6 4
7
0
```

Inside `geometry`, its own declarations need no qualifier. A module can also name itself, as in `example.main`, which helps when a local name hides one of its declarations.

Without a qualifier or an import, a name from another module isn't found:

```cella error group=unqualified file=main.ce
~ mod example
~
main: fun
{
	val a = area(2, 3)
}
```

```cella group=unqualified file=geometry.ce
mod geometry

area: fun(w: i32, h: i32) -> i32 => w * h
```

```errors
Symbol 'area' not found in this scope
```

A module isn't a value, so its name can only be used in front of a `.`:

```cella error group=moduleValue file=main.ce
~ mod example
~
main: fun
{
	val m = geometry
}
```

```cella group=moduleValue file=geometry.ce
mod geometry

area: fun(w: i32, h: i32) -> i32 => w * h
```

```errors
Cannot use modules as values
```

## Nested module names

A module name can have several parts separated by dots, as in `mod game.physics`. The parts make a tree of names: `game.physics` is reached as `game.physics.fall`, whether or not a module named `game` exists. `game` and `game.physics` are separate modules, each with its own declarations:

```cella group=nested file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d %d\n", game.physics.fall(2), game.speed())
}
```

```cella group=nested file=game/game.ce
mod game

speed: fun -> i32 => physics.gravity * 2
```

```cella group=nested file=game/physics.ce
mod game.physics

gravity: const i32 = 10

fall: fun(time: i32) -> i32 => gravity * time * time / 2
```

```output
20 20
```

Inside `game`, its nested module `game.physics` can be written `physics`.

A module can't have a member with the same name as a nested module:

```cella error group=moduleMember file=main.ce
~ mod example
~
main: fun
{
}
```

```cella group=moduleMember file=game.ce
mod game

physics: fun -> i32 => 1
```

```cella group=moduleMember file=physics.ce
mod game.physics

gravity: const i32 = 10
```

```errors
'game.physics' is both a module and a member of 'game'
'game.physics' is both a module and a member of 'game'
```

## Imports

A `use` line after the `mod` line imports names from another module, so the file can use them without a qualifier. `use` names what it imports:

- `use geometry.area` imports one name.
- `use geometry.[area, Point]` imports several.
- `use geometry.*` imports everything in `geometry`.
- `use game.physics` imports a nested module, so the file can write `physics.fall` instead of `game.physics.fall`.

```cella group=imports file=main.ce
~ mod example
~
use geometry.[area, Point]
use shapes.*
use game.physics

~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	val p = Point(1, 2)
	printf("%d %d %d\n", area(2, 3), p.y, perimeter(5))
	printf("%d\n", physics.fall(2))
}
```

```cella group=imports file=geometry.ce
mod geometry

Point: rec
{
	x: i32
	y: i32
}

area: fun(w: i32, h: i32) -> i32 => w * h
```

```cella group=imports file=shapes.ce
mod shapes

perimeter: fun(side: i32) -> i32 => side * 4
```

```cella group=imports file=game/physics.ce
mod game.physics

fall: fun(time: i32) -> i32 => 5 * time * time
```

```output
6 2 20
20
```

An import applies to the file it's written in, not to the rest of the module. Imported names can still be written with their qualifier.

Imports come right after the `mod` line, before any declaration:

```cella error group=lateImport file=main.ce
mod example

main: fun
{
}

use geometry.area
```

```cella group=lateImport file=geometry.ce
mod geometry

area: fun(w: i32, h: i32) -> i32 => w * h
```

```errors
Imports must precede all other declarations
```

An import that names something that doesn't exist is an error, with a suggestion when a close spelling exists:

```cella error group=badImports file=main.ce
mod example

use geometry.missing
use gemoetry.area
use geometry.area.more

main: fun
{
}
```

```cella group=badImports file=geometry.ce
mod geometry

area: fun(w: i32, h: i32) -> i32 => w * h
```

```errors
Module 'geometry' has no member 'missing'
Module 'gemoetry' not found
'geometry.area' is not a module
```

Importing the same name twice is "'area' is imported more than once".

## Imports and the module's own names

A file sees its module's declarations and its imports together, and neither one wins over the other:

- Functions from both form one set of overloads. When the module declares a function with the same name and parameters as an imported one, the module's own function hides the import; the imported one is still reachable through its qualifier.
- A type, constant or variable that comes in through `*` is hidden by a module declaration with the same name.

```cella group=precedence file=main.ce
~ mod example
~
use geometry.area
use geometry.scale
use geometry.*

~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
area: fun -> i32 => 1
scale: fun(a: i32, b: i32) -> i32 => a + b
limit: val i32 = 3

main: fun
{
	printf("%d %d\n", area(), geometry.area())
	printf("%d %d\n", scale(1), scale(1, 2))
	printf("%d %d\n", limit, geometry.limit)
}
```

```cella group=precedence file=geometry.ce
mod geometry

area: fun -> i32 => 2
scale: fun(x: i32) -> i32 => x * 10
limit: val i32 = 7
```

```output
1 2
10 3
3 7
```

Naming a type, constant or variable in an import while the module declares the same name is an error, since the import could never be used by its plain name. Both places are reported:

```cella error group=importConflict file=main.ce
mod example

use geometry.Point

Point: rec
{
	z: i32
}

main: fun
{
}
```

```cella group=importConflict file=geometry.ce
mod geometry

Point: rec
{
	x: i32
}
```

```errors
'Point' is ambiguous
'Point' is ambiguous
```

The first error is on the import, with the note "Also declared in 'example'", and the second on the declaration, with "Also imported from 'geometry'".

Imports never hide each other. When two imports bring in the same name, using it is ambiguous; for functions, only when they have the same parameters:

```cella error group=importAmbiguity file=main.ce
mod example

use geometry.*
use shapes.*

main: fun
{
	val a = area()
	val p = Point(1)
}
```

```cella group=importAmbiguity file=geometry.ce
mod geometry

area: fun -> i32 => 2

Point: rec
{
	x: i32
}
```

```cella group=importAmbiguity file=shapes.ce
mod shapes

area: fun -> i32 => 3

Point: rec
{
	y: i32
}
```

```errors
Call to 'area' is ambiguous
Reference to 'Point' is ambiguous
```

The qualified names `geometry.area` and `shapes.area` still work.

## `mod.` paths

A local variable, parameter or declaration can have the same name as a module and hide it. A path starting with `mod.` always starts from the top of the module tree, whatever is in scope:

```cella group=rootPaths file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	val geometry = 4
	val shape = mod.geometry.Shape(3)
	printf("%d %d %d\n", geometry, shape.side, mod.geometry.area(2))
}
```

```cella group=rootPaths file=geometry.ce
mod geometry

Shape: rec
{
	side: i32
}

area: fun(side: i32) -> i32 => side * side
```

```output
4 3 4
```

## Visibility

Every top-level declaration has one of four visibility levels:

| Keyword | Visible in |
| --- | --- |
| `pvt` | its own file |
| `mod` | its own module, in every file |
| none | its own project |
| `pub` | every project that references this one |

The keyword goes after the colon, before what the declaration is, as in `helper: pvt fun` or `Point: pub rec`. A declaration without one is visible in the whole project, which is all a program made of one project needs.

`pvt` keeps a declaration to its file, even from other files of the same module:

```cella error group=pvtFile file=main.ce
~ mod example
~
main: fun
{
	val n = helper()
}
```

```cella group=pvtFile file=helpers.ce
mod example

helper: pvt fun -> i32 => 1
```

```errors
'helper' is private to its file
```

`mod` keeps a declaration to its module. A nested module is a different module, so `game.physics` can't see `mod` declarations of `game`, and the other way around:

```cella error group=modModule file=main.ce
~ mod example
~
main: fun
{
	val n = game.tool()
}
```

```cella group=modModule file=game.ce
mod game

tool: mod fun -> i32 => 1
```

```errors
'game.tool' is private to its module
```

The same rules apply to imports: a hidden declaration that comes in through `*` still can't be used, and naming one in an import is an error.

Types, functions, constants, module variables, traits and `ext` declarations all take visibility. Local variables don't:

```cella error
mod example

main: fun
{
	val x: pvt i32 = 1
}
```

```errors
Cannot use 'pvt' on local variables
```

Members of records, enums and other types have their own visibility rules, covered in [Methods and properties](methods.md).

### Visibility blocks

A block gives every declaration in it the same visibility: `pvt { ... }`, `mod { ... }` or `pub { ... }`. It can hold any top-level declarations, `ext` blocks included, and `pvt ext { ... }` is short for an `ext` block inside a `pvt` block:

```cella
mod example

pvt ext
{
	printf: fun(format: cstr, ...) -> i32
}

mod
{
	twice: fun(n: i32) -> i32 => n * 2
	limit: const i32 = 100
}

main: fun
{
	printf("%d %d\n", twice(4), limit)
}
```

```output
8 100
```

A declaration inside a block can't name a visibility of its own, and blocks of different levels can't be nested:

```cella error
mod example

mod
{
	helper: pvt fun -> i32 => 0

	pvt
	{
		other: fun -> i32 => 1
	}
}

twice: pvt mod fun -> i32 => 0

main: fun
{
}
```

```errors
Cannot use 'pvt' in 'mod' blocks
Cannot use 'pvt' in 'mod' blocks
Cannot combine 'pvt' and 'mod'
```

### Signatures can't expose hidden types

A declaration can't mention a type that is less visible than the declaration itself, since code that can see the declaration couldn't name the type. This covers parameter and result types, field types, payloads and the types of module variables:

```cella error
mod example

Node: pvt rec
{
	value: i32
}

Tree: rec
{
	root: Node
}

make: fun -> Node => Node(1)

take: fun(node: Node) -> i32 => node.value

keep: pvt fun(node: Node) -> i32 => node.value

main: fun
{
}
```

```errors
'Node' is less visible than 'root'
'Node' is less visible than 'make'
'Node' is less visible than 'take'
```

`keep` is fine: it's `pvt` like `Node`, so it's never visible where `Node` isn't. The same holds for types built from a hidden type, like `ptr[Node]` or `array[Node, 4]`, and for traits named in bounds and `dyn` types.

## Libraries

A project can reference a library project, as [Projects and building](projects.md) shows, and use its declarations. Only the library's `pub` declarations cross over; everything else is private to the library's project. The library's modules are reached by name, exactly like the program's own:

```celp group=library
OutputType = "Executable"

[[ProjectReferences]]
Path = 'shapes/shapes.celp'
```

```celp group=library file=shapes/shapes.celp
OutputType = "StaticLibrary"
```

```cella group=library file=shapes/shapes.ce
mod shapes

Square: pub rec
{
	side: i32
}

area: pub fun(s: Square) -> i32 => s.side * s.side * scale()

scale: fun -> i32 => 1
```

```cella group=library file=main.ce
~ mod example
~
use shapes.[Square, area]

~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d\n", area(Square(3)))
}
```

```output
9
```

Using `scale` from the program would be "'shapes.scale' is private to its project". A `pub` declaration also can't expose a type that isn't `pub`, by the rule in the previous section.

## Project imports

A project's `.celp` file can list imports that apply to every source file in the project, so each file doesn't need its own `use` lines. `Imports` takes the same forms as `use`, written as strings:

```celp group=projectImports
OutputType = "Executable"
Imports = ["geometry.area", "shapes.*"]
```

```cella group=projectImports file=main.ce
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	printf("%d %d\n", area(2, 3), perimeter(5))
}
```

```cella group=projectImports file=geometry.ce
mod geometry

area: fun(w: i32, h: i32) -> i32 => w * h
```

```cella group=projectImports file=shapes.ce
mod shapes

perimeter: fun(side: i32) -> i32 => side * 4
```

```output
6 20
```

Project imports combine with the module's own declarations by the same rules as `use` lines. An import listed there and in a file's `use` line is "'area' is imported more than once", and errors in the list point into the `.celp` file.

A library's `.celp` can list a `Prelude` instead: imports that every project referencing the library gets automatically. A `use` line that repeats one of them gets the hint "Redundant import".

```celp group=prelude
OutputType = "Executable"

[[ProjectReferences]]
Path = 'greetings/greetings.celp'
```

```celp group=prelude file=greetings/greetings.celp
OutputType = "StaticLibrary"
Prelude = ["greetings.greet"]
```

```cella group=prelude file=greetings/greetings.ce
mod greetings

pvt ext
{
	printf: fun(format: cstr, ...) -> i32
}

greet: pub fun => printf("hello from the prelude\n")
```

```cella group=prelude file=main.ce
mod example

main: fun
{
	greet()
}
```

```output
hello from the prelude
```
