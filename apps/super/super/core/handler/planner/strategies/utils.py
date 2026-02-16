import ast
import json
from typing import List


def to_numbered_list(
    items: List[str],
    no_items_response: str = "",
    use_format=True,
    **template_args,
) -> str:
    if items:
        if not use_format:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        else:
            # no requirement to use format?
            return "\n".join(
                f"{i+1}. {item.format(**template_args)}" for i, item in enumerate(items)
            )
    else:
        return no_items_response
