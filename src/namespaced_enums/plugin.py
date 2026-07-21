"""A mypy plugin that teaches the type checker about ``NamespacedEnum``.

Why it is needed
----------------
mypy (like the runtime ``enum`` machinery) turns every simple assignment in an
enum body into an enum *member*.  Unlike the runtime, however, mypy does **not**
recognise that an assigned value is a *descriptor* and therefore should not be a
member.  As a result, without this plugin ``EnumContainer`` / ``StrictEnumContainer``
attributes are seen as enum members typed ``Literal[Enum.attr]`` and any attempt
to index them fails with ``"Enum" is not indexable``.

What the plugin does
--------------------
1.  For every class deriving from :class:`namespaced_enums.NamespacedEnum` (or
    using :class:`namespaced_enums.NamespacedEnumMeta`) it marks each container
    attribute as a *non-member* so mypy falls back to the descriptor protocol
    and infers the real ``__get__`` return type (``dict``/``list``/...).
2.  For ``StrictEnumContainer`` it rewrites the resulting dict's key type to the
    enum class itself, mirroring the runtime behaviour of converting the keys
    into enum members.
3.  It reports a *static* error (code ``namespaced-enum``) when a
    ``StrictEnumContainer`` does not provide a key for every enum member, i.e.
    the same condition that raises ``RuntimeError`` at import time.

Enable it in ``mypy.ini`` / ``pyproject.toml``::

    [mypy]
    plugins = namespaced_enums.plugin

Requires a modern mypy (>= 1.0).
"""

from __future__ import annotations

from typing import Callable, List, Optional

from mypy.errorcodes import ErrorCode
from mypy.nodes import (
    AssignmentStmt,
    CallExpr,
    DictExpr,
    NameExpr,
    RefExpr,
    TypeInfo,
    Var,
)
from mypy.plugin import AttributeContext, ClassDefContext, Plugin
from mypy.types import CallableType, Instance, Type, get_proper_type

MODULE = "namespaced_enums"
NAMESPACED_ENUM = f"{MODULE}.NamespacedEnum"
NAMESPACED_ENUM_META = f"{MODULE}.NamespacedEnumMeta"
STRICT_CONTAINER = f"{MODULE}.StrictEnumContainer"
ENUM_CONTAINER = f"{MODULE}.EnumContainer"
CONTAINERS = frozenset({ENUM_CONTAINER, STRICT_CONTAINER})

# Key under which we stash per-class plugin data on the ``TypeInfo``.  This is
# serialised together with mypy's incremental cache.
METADATA_KEY = MODULE

MISSING_KEYS: ErrorCode = ErrorCode(
    "namespaced-enum",
    "Check that a StrictEnumContainer covers every enum member",
    "General",
)


def _is_container_call(stmt: object) -> Optional[bool]:
    """Return ``True``/``False`` (strict) if ``stmt`` assigns a container, else ``None``."""
    rhs = getattr(stmt, "rvalue", None)
    if (
        isinstance(stmt, AssignmentStmt)
        and isinstance(rhs, CallExpr)
        and isinstance(rhs.callee, RefExpr)
        and rhs.callee.fullname in CONTAINERS
    ):
        return rhs.callee.fullname == STRICT_CONTAINER
    return None


def _transform_class(ctx: ClassDefContext) -> None:
    """De-member container attributes and record which of them are strict."""
    strict: List[str] = []
    for stmt in ctx.cls.defs.body:
        is_strict = _is_container_call(stmt)
        if is_strict is None:
            continue
        assert isinstance(stmt, AssignmentStmt)
        for lval in stmt.lvalues:
            if not isinstance(lval, NameExpr):
                continue
            sym = ctx.cls.info.names.get(lval.name)
            if sym is not None and isinstance(sym.node, Var):
                # ``has_explicit_value == False`` excludes the name from
                # ``TypeInfo.enum_members`` so descriptor access kicks in.
                sym.node.has_explicit_value = False
                if is_strict:
                    strict.append(lval.name)
    _check_exhaustive(ctx)
    ctx.cls.info.metadata[METADATA_KEY] = {"strict": strict}


def _member_names(ctx: ClassDefContext) -> List[str]:
    """Best-effort list of enum member names declared in the class body."""
    names: List[str] = []
    for stmt in ctx.cls.defs.body:
        if not isinstance(stmt, AssignmentStmt):
            continue
        if _is_container_call(stmt) is not None:
            continue  # containers are not members
        if len(stmt.lvalues) != 1 or not isinstance(stmt.lvalues[0], NameExpr):
            continue
        name = stmt.lvalues[0].name
        if name.startswith("__") or (
            name.startswith("_") and name.endswith("_")
        ):
            continue  # dunder / sunder names are never members
        names.append(name)
    return names


def _check_exhaustive(ctx: ClassDefContext) -> None:
    """Emit an error for any ``StrictEnumContainer`` missing an enum member key."""
    members = _member_names(ctx)
    if not members:
        return
    for stmt in ctx.cls.defs.body:
        if _is_container_call(stmt) is not True:
            continue
        assert isinstance(stmt, AssignmentStmt)
        rhs = stmt.rvalue
        assert isinstance(rhs, CallExpr)
        if not (rhs.args and isinstance(rhs.args[0], DictExpr)):
            continue
        key_names = set()
        for key, _value in rhs.args[0].items:
            if isinstance(key, NameExpr):
                key_names.add(key.name)
            else:
                # A non-trivial key (literal, computed, ...) — stay silent
                # rather than risk a false positive.
                break
        else:
            missing = [m for m in members if m not in key_names]
            if missing:
                attr = (
                    stmt.lvalues[0].name
                    if isinstance(stmt.lvalues[0], NameExpr)
                    else "?"
                )
                ctx.api.fail(
                    f'StrictEnumContainer "{attr}" is missing keys for enum '
                    f'members: {", ".join(missing)}',
                    stmt,
                    code=MISSING_KEYS,
                )


def _enum_instance(attr_type: Type) -> Optional[Instance]:
    """Extract the enum ``Instance`` from an attribute-access owner type."""
    owner = get_proper_type(attr_type)
    if isinstance(owner, CallableType):
        # Class-level access: the owner is the enum's constructor callable.
        ret = get_proper_type(owner.ret_type)
        return ret if isinstance(ret, Instance) else None
    if isinstance(owner, Instance):
        # Instance-level access.
        return owner
    return None


def _rewrite_strict_key(ctx: AttributeContext) -> Type:
    """Replace ``dict[<value>, V]`` with ``dict[<enum>, V]`` for strict containers."""
    default = get_proper_type(ctx.default_attr_type)
    enum_inst = _enum_instance(ctx.type)
    if (
        enum_inst is not None
        and isinstance(default, Instance)
        and default.type.fullname == "builtins.dict"
        and len(default.args) == 2
    ):
        return default.copy_modified(args=[enum_inst, default.args[1]])
    return ctx.default_attr_type


class NamespacedEnumsPlugin(Plugin):
    def _strict_attr_hook(
        self, fullname: str
    ) -> Optional[Callable[[AttributeContext], Type]]:
        cls_fullname, _, attr = fullname.rpartition(".")
        sym = self.lookup_fully_qualified(cls_fullname)
        if sym is None or not isinstance(sym.node, TypeInfo):
            return None
        meta = sym.node.metadata.get(METADATA_KEY)
        if meta and attr in meta.get("strict", []):
            return _rewrite_strict_key
        return None

    def get_base_class_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        # Fire for any class whose base has ``NamespacedEnum`` in its MRO, so
        # that indirect subclasses (mixin chains) are handled too.
        sym = self.lookup_fully_qualified(fullname)
        if (
            sym is not None
            and isinstance(sym.node, TypeInfo)
            and any(base.fullname == NAMESPACED_ENUM for base in sym.node.mro)
        ):
            return _transform_class
        return None

    def get_metaclass_hook(
        self, fullname: str
    ) -> Optional[Callable[[ClassDefContext], None]]:
        # Handles ``class X(Enum, metaclass=NamespacedEnumMeta)`` usage.
        return _transform_class if fullname == NAMESPACED_ENUM_META else None

    def get_class_attribute_hook(
        self, fullname: str
    ) -> Optional[Callable[[AttributeContext], Type]]:
        return self._strict_attr_hook(fullname)

    def get_attribute_hook(
        self, fullname: str
    ) -> Optional[Callable[[AttributeContext], Type]]:
        return self._strict_attr_hook(fullname)


def plugin(version: str) -> type[Plugin]:
    return NamespacedEnumsPlugin
