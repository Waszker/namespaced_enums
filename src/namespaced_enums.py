from __future__ import annotations

import inspect
from enum import Enum, EnumMeta, _EnumDict
from typing import Any, Dict, Generic, List, Set, TypeVar, Union

T = TypeVar("T", bound=Union[List[Any], Dict[Any, Any], Set[Any]])
K = TypeVar("K", bound=Dict[Any, Any])


class EnumContainer(Generic[T]):
    """Descriptor that allows for definitions of containers within Enum."""

    def __init__(self, container: T):
        self._container = container

    def __get__(self, instance: Any, instance_cls: Any) -> T:
        return self._container


class StrictEnumContainer(EnumContainer[K]):
    """`EnumContainer` class that requires dict to be passed as a container."""

    def __init__(self, container: K):
        if not issubclass(type(container), dict):
            raise ValueError(
                f"{StrictEnumContainer.__name__} supports only dict-based "
                + f"containers, {type(container)} provided",
            )

        super().__init__(container)


class NamespacedEnumMeta(EnumMeta):
    """Metaclass ensuring that all enum values are in `StrictEnumContainer`s."""

    def __new__(
        mcs,
        cls,
        bases: tuple[type, ...],
        namespace: _EnumDict,
    ):
        enum_values = {
            namespace[member]: member
            for member in namespace._member_names  # type: ignore
        }
        strict_enum_container_fields = {
            field_name: field
            for field_name, field in namespace.items()
            if (
                inspect.ismethoddescriptor(field)
                and isinstance(field, StrictEnumContainer)
            )
        }

        # Check for string container violations
        strict_enum_containers_violated = [
            field_name
            for (field_name, field) in strict_enum_container_fields.items()
            if not all(enum in field._container for enum in enum_values)
        ]
        if strict_enum_containers_violated:
            raise RuntimeError(
                f"The following {cls} fields do not contain all possible "
                + f"enum values: {strict_enum_containers_violated}"
            )

        # Instantiate the class
        instantiated_enum = EnumMeta.__new__(mcs, cls, bases, namespace)

        # Change the StrictEnumContainer key values to proper enum objects
        for container in strict_enum_container_fields.values():
            new_container_content = {
                getattr(instantiated_enum, enum_values[enum_value]): dict_value
                for enum_value, dict_value in container._container.items()
            }
            container._container.clear()
            container._container.update(new_container_content)

        return instantiated_enum


class NamespacedEnum(Enum, metaclass=NamespacedEnumMeta):
    """
    Extension of the basic Enum class, allowing for EnumContainer usages.

    Example usage:
    >>> class Items(metaclass=NamespacedEnumMeta):
    >>>     spam = "spam"
    >>>     eggs = "eggs"
    >>>     foo = "foo"
    >>>
    >>>     food_preferences = StrictEnumContainer({
    >>>         spam: "I like spam!",
    >>>         eggs: "I really don't like eggs...",
    >>>     })
    will not instantiate and the `RuntimeError` informing about missing mapping
    for `Items.foo` will be raised.

    This class takes burden of remembering to add new enum values to mapping off
    programmers' shoulders by doing it automatically during runtime.
    """
