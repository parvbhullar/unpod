import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/lite_handler.py")


def _class_node() -> ast.ClassDef:
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    return next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "LiveKitLiteAgent"
    )


def _method_node(name: str) -> ast.AsyncFunctionDef:
    class_node = _class_node()
    method = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    )

    for parent in ast.walk(method):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)

    return method


def _nearest_try(node: ast.AST) -> ast.Try | None:
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, ast.Try):
            return current
        current = getattr(current, "parent", None)
    return None


def _is_attr_call(node: ast.AST, attr_name: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attr_name
    )


def _is_name_call(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name


def test_handover_wait_for_participant_is_bounded_with_timeout() -> None:
    method = _method_node("handover_call")

    wait_for_call = next(
        node
        for node in ast.walk(method)
        if _is_attr_call(node, "wait_for")
        and node.args
        and isinstance(node.args[0], ast.Call)
        and _is_attr_call(node.args[0], "wait_for_participant")
    )

    has_timeout = len(wait_for_call.args) >= 2 or any(
        kw.arg == "timeout" for kw in wait_for_call.keywords
    )
    assert has_timeout


def test_handover_retry_scope_excludes_post_connect_setup() -> None:
    method = _method_node("handover_call")

    create_call = next(
        node for node in ast.walk(method) if _is_attr_call(node, "create_sip_participant")
    )
    retry_try = _nearest_try(create_call)
    assert retry_try is not None

    # Retry scope should only cover SIP dial/connect, not post-connect side effects.
    assert not any(
        _is_name_call(node, "save_execution_log")
        for node in ast.walk(retry_try)
    )
