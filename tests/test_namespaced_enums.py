import pytest

from src.namespaced_enums import (
    EnumContainer,
    NamespacedEnum,
    StrictEnumContainer,
)


def test_providing_non_dict_for_strict_container_raises_error() -> None:
    """Confirms that `StrictEnumContainer` accepts only dict-based container."""
    with pytest.raises(ValueError) as error:
        StrictEnumContainer(["value1"])  # type: ignore

    assert (
        "StrictEnumContainer supports only dict-based containers, "
        + "<class 'list'> provided"
        == str(error.value)
    )


def test_strict_enum_container_violation_raises() -> None:
    """Confirms that missing enum value in `StrictEnumContainer` raises."""
    with pytest.raises(RuntimeError) as error:

        class ActionEnum(NamespacedEnum):
            ACTION1 = "action1"
            ACTION2 = "action2"

            func_for_action = StrictEnumContainer(
                {
                    ACTION1: lambda: print("Doing action 1"),
                }
            )

    assert (
        "The following ActionEnum fields do not contain all possible "
        + "enum values: ['func_for_action']"
        == str(error.value)
    )


def test_enum_container_does_not_convert_items() -> None:
    """Confirms that `EnumContainer` does not convert the items."""

    class ActionEnum(NamespacedEnum):
        ACTION1 = "action1"
        ACTION2 = "action2"

        actions = EnumContainer([ACTION1, ACTION2])

    assert ActionEnum.actions == ["action1", "action2"]


def test_strict_enum_container_converts_keys_to_enum_representation() -> None:
    """Confirms that `StrictEnumContainer` has its keys converted."""

    class ActionEnum(NamespacedEnum):
        ACTION1 = "action1"
        ACTION2 = "action2"

        func_for_action = StrictEnumContainer(
            {
                ACTION1: lambda: print("Doing action 1"),
                ACTION2: lambda: print("Doing action 2"),
            },
        )

    assert list(ActionEnum.func_for_action.keys()) == [
        ActionEnum.ACTION1,
        ActionEnum.ACTION2,
    ]
