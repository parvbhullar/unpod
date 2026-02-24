import ast
from pathlib import Path


SOURCE_PATH = Path("super/core/voice/voice_agent_handler.py")


def _class_node() -> ast.ClassDef:
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    return next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "VoiceAgentHandler"
    )


def _method_node(name: str) -> ast.AsyncFunctionDef:
    class_node = _class_node()
    method = next(
        node
        for node in class_node.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == name
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


def test_instant_handover_isolated_from_sip_creation_retry_scope() -> None:
    method = _method_node("_create_sip_participant_in_room")

    handover_await = next(
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Await)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "_instant_handover"
    )

    nearest_try = _nearest_try(handover_await)
    assert nearest_try is not None

    # Handover failures must not trigger SIP creation retries.
    assert not any(
        _is_attr_call(node, "create_sip_participant")
        for node in ast.walk(nearest_try)
    )


def test_instant_handover_waits_for_created_identity_with_timeout() -> None:
    method = _method_node("_instant_handover")

    request_call = next(
        node
        for node in ast.walk(method)
        if _is_attr_call(node, "CreateSIPParticipantRequest")
    )
    created_identity = next(
        kw.value for kw in request_call.keywords if kw.arg == "participant_identity"
    )

    wait_for_participant_call = next(
        node
        for node in ast.walk(method)
        if _is_attr_call(node, "wait_for_participant")
    )
    awaited_identity = next(
        kw.value for kw in wait_for_participant_call.keywords if kw.arg == "identity"
    )

    assert ast.dump(created_identity) == ast.dump(awaited_identity)

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
