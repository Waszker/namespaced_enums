## NamespacedEnums

Library for defining containers within `Enum` Python classes.

## Installation

Run

```bash
$ pip install namespaced_enums
```

## Usage

Library provides two special descriptors for `Enum` classes:
- `EnumContainer`
- `StrictEnumContainer`

as well as an additional enum-subclass:
- `NamespacedEnum`

### EnumContainer

This allows for defining arbitrary containers within `Enum` classes, e.g.

```python
from enum import Enum
from namespaced_enum import EnumContainer

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
    
    LIGHT_RED = 4
    LIGHT_GREEN = 5
    LIGHT_BLUE = 6
    
    DARK_RED = 7
    DARK_GREEN = 8
    DARK_BLUE = 9
    
    light_colors = EnumContainer([LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE])
    dark_colors = EnumContainer([DARK_RED, DARK_GREEN, DARK_BLUE])
    
---

>>> print(Color.RED.value in Color.light_colors)  # False
>>> print(Color.DARK_BLUE.value in Color.dark_colors)  # True

# Caution!
# Values within containers are of enum value types
>>> print(Color.dark_colors)  # prints [7, 8, 9] and not [DARK_RED, DARK_GREEN, DARK_BLUE]!
```

### StrictEnumContainer and NamespacedEnum

`StrictEnumContainer` accepts only dict containers. Using this descriptor within
a class inheriting from `NamespacedEnum` will enforce that the provided 
dictionary contains all enum possible values:

```python
from namespaced_enums import NamespacedEnum, StrictEnumContainer

class Food(NamespacedEnum):
    spam = "spam"
    eggs = "eggs"
    foo = "foo"

    reactions = StrictEnumContainer(
        {
            spam: "I like it",
            eggs: "I don't like it...",
            foo: "I like?",
        }
    )

---

>>> print(Food.reactions[Food.spam])  # "I like it"

# Caution!
# Unlike the `EnumContainer` this one converts dict keys to enums!
>>> print(list[Food.reactions.keys()])  # prints [<Food.spam: spam>, <Food.eggs: eggs>, <Food.foo: foo>]
```

Forgetting to provide all possible enum values within a strict container will
raise a `RuntimeError`:

```python
from namespaced_enums import NamespacedEnum, StrictEnumContainer

class Food(NamespacedEnum):
    spam = "spam"
    eggs = "eggs"
    foo = "foo"

    reactions = StrictEnumContainer(
        {
            spam: "I like it",
            eggs: "I don't like it...",
            # missing foo in the dict
        }
    )

---

>>> # Trying to start the program raises a `RuntimeError`:
# The following Food fields do not contain all possible enum values: ['reactions']
```

## Rationale

It's a common practice to use enums in a project as a way to denote 
"characteristics" of certain objects. 

Consider the following example:

```python
from enum import Enum

class DogBreed(Enum):
    BULLDOG = 'bulldog'
    PUG = 'pug'
    SHIBA = 'shiba'

    
class Dog:
    def __init__(self, breed: DogBreed) -> None:
        self.breed = breed
        
    @property
    def size(self) -> int:
        """Returns size of the dog (in centimeters)."""
        if self.breed == DogBreed.BULLDOG:
            return 40
        elif self.breed == DogBreed.PUG:
            return 30
        elif self.breed == DogBreed.SHIBA:
            return 35
        else:  # pragma: no cover
            raise ValueError(f"Unknown dog breed: {self.breed}")
```

The `Dog.size` property implementation poses a threat when it comes to further
additions to the `DogBreed` enum: 
- programmers would have to **remember to update** it every time they add a new 
breed support. What if there are more such properties like color, weight or 
tail length?
- the **if-elif-else chain is hard to test** as the last `else` clause would 
require injecting some arbitrary value into the `DogBreed` enum during runtime 
in order to ensure proper coverage. In my experience, most developers would 
prefer to add `# pragma: no cover` instead.
- the size characteristic should arguably be not part of the `Dog` class as it
is more specific to the `DogBreed` enum - the `Dog` class should be aware of
how to retrieve that data.

That's why I decided to create a `NamespacedEnum` class that allows for writing
self-contained enums, that can help in maintaining the integrity of the written
code. The example above could be rewritten in a following manner:

```python
from namespaced_enums import NamespacedEnum, StrictEnumContainer


class DogBreed(NamespacedEnum):
    BULLDOG = 'bulldog'
    PUG = 'pug'
    SHIBA = 'shiba'

    size = StrictEnumContainer({
        BULLDOG: 40,
        PUG: 30,
        SHIBA: 35,
    })

    
class Dog:
    def __init__(self, breed: DogBreed) -> None:
        self.breed = breed

    @property
    def size(self) -> int:
        """Returns size of the dog (in centimeters)."""
        return DogBreed.size[self.breed]
```