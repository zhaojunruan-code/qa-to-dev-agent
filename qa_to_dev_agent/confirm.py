from __future__ import annotations

from collections.abc import Callable
from typing import TextIO


InputFunc = Callable[[str], str]


def confirm_yes_no(prompt: str, input_func: InputFunc, output: TextIO) -> bool:
    print(f"{prompt} [y/N]", file=output)
    answer = input_func("> ").strip().lower()
    return answer in {"y", "yes"}


def confirm_phrase(prompt: str, phrase: str, input_func: InputFunc, output: TextIO) -> bool:
    print(prompt, file=output)
    print(f'Type "{phrase}" to continue:', file=output)
    return input_func("> ").strip() == phrase


def confirm_typed(
    prompt: str,
    phrase: str,
    input_func: InputFunc,
    output_func,
) -> bool:
    output_func(prompt)
    output_func(f'Type "{phrase}" to continue:')
    return input_func("> ").strip() == phrase
