"""End-to-end tests for the mypy plugin.

Each test runs the real mypy against a small snippet with the plugin enabled and
asserts on the reported output. ``src`` is put on mypy's search path so that
``import namespaced_enums`` resolves to the in-repo (typed) package, and the
plugin is loaded straight from its source file.
"""

import pathlib
import textwrap

import pytest

mypy_api = pytest.importorskip("mypy.api")

# The plugin relies on mypy's modern enum model (``TypeInfo.enum_members`` /
# ``Var.has_explicit_value``) and only supports mypy >= 1.0.
mypy_version = pytest.importorskip("mypy.version")
if int(mypy_version.__version__.split(".")[0]) < 1:
    pytest.skip(
        "namespaced_enums.plugin requires mypy >= 1.0",
        allow_module_level=True,
    )

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
PLUGIN = SRC / "namespaced_enums" / "plugin.py"


def run_mypy(code: str, tmp_path: pathlib.Path) -> str:
    """Type-check ``code`` with the plugin enabled and return mypy's stdout."""
    target = tmp_path / "snippet.py"
    target.write_text(textwrap.dedent(code))

    config = tmp_path / "mypy.ini"
    config.write_text(textwrap.dedent(f"""
            [mypy]
            mypy_path = {SRC}
            plugins = {PLUGIN}
            show_error_codes = True
            """))

    stdout, _stderr, _status = mypy_api.run(
        ["--no-incremental", "--config-file", str(config), str(target)]
    )
    return stdout


def test_strict_container_is_indexable_by_enum(tmp_path):
    out = run_mypy(
        """
        from namespaced_enums import NamespacedEnum, StrictEnumContainer

        class Dog(NamespacedEnum):
            BULLDOG = "bulldog"
            PUG = "pug"
            size = StrictEnumContainer({BULLDOG: 40, PUG: 30})

        reveal_type(Dog.size)
        s: int = Dog.size[Dog.PUG]
        """,
        tmp_path,
    )
    assert 'Revealed type is "dict[snippet.Dog, int]"' in out
    assert "error:" not in out


def test_indexing_strict_container_with_value_type_is_rejected(tmp_path):
    out = run_mypy(
        """
        from namespaced_enums import NamespacedEnum, StrictEnumContainer

        class Dog(NamespacedEnum):
            BULLDOG = "bulldog"
            PUG = "pug"
            size = StrictEnumContainer({BULLDOG: 40, PUG: 30})

        Dog.size["bulldog"]
        """,
        tmp_path,
    )
    assert "Invalid index type" in out


def test_missing_enum_member_key_is_reported_statically(tmp_path):
    out = run_mypy(
        """
        from namespaced_enums import NamespacedEnum, StrictEnumContainer

        class Dog(NamespacedEnum):
            BULLDOG = "bulldog"
            PUG = "pug"
            SHIBA = "shiba"
            size = StrictEnumContainer({BULLDOG: 40, PUG: 30})
        """,
        tmp_path,
    )
    assert (
        'StrictEnumContainer "size" is missing keys for enum members: SHIBA'
        in out
    )
    assert "[namespaced-enum]" in out


def test_complete_strict_container_reports_no_error(tmp_path):
    out = run_mypy(
        """
        from namespaced_enums import NamespacedEnum, StrictEnumContainer

        class Dog(NamespacedEnum):
            BULLDOG = "bulldog"
            PUG = "pug"
            size = StrictEnumContainer({BULLDOG: 40, PUG: 30})
        """,
        tmp_path,
    )
    assert "Success" in out


def test_enum_container_list_type_and_no_exhaustiveness_check(tmp_path):
    out = run_mypy(
        """
        from enum import Enum
        from namespaced_enums import NamespacedEnumMeta, EnumContainer

        class Color(Enum, metaclass=NamespacedEnumMeta):
            RED = 1
            GREEN = 2
            BLUE = 3
            warm = EnumContainer([RED, GREEN])

        reveal_type(Color.warm)
        """,
        tmp_path,
    )
    assert 'Revealed type is "list[int]"' in out
    assert "error:" not in out


def test_indirect_subclass_chain_is_supported(tmp_path):
    out = run_mypy(
        """
        from namespaced_enums import NamespacedEnum, StrictEnumContainer

        class Base(NamespacedEnum):
            pass

        class Priority(Base):
            LOW = 1
            HIGH = 2
            labels = StrictEnumContainer({LOW: "low", HIGH: "high"})

        reveal_type(Priority.labels)
        v: str = Priority.labels[Priority.LOW]
        """,
        tmp_path,
    )
    assert 'Revealed type is "dict[snippet.Priority, str]"' in out
    assert "error:" not in out
