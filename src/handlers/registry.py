# -*- coding: utf-8 -*-
"""
Handler registry and factory.
"""

from typing import Any, Dict

from ..core.file_scanner import FileScanner


def get_handler_registry():
    """Return mode name -> handler class mapping."""
    from .sort_handler import SortModeHandler
    from .clean_handler import CleanModeHandler
    from .png_prompt_sort_handler import PngPromptSortModeHandler
    from .pipeline_handler import PipelineModeHandler

    handlers = [
        SortModeHandler,
        CleanModeHandler,
        PngPromptSortModeHandler,
        PipelineModeHandler,
    ]
    return {handler.MODE: handler for handler in handlers}


def get_handler_modes() -> list[str]:
    """Return registered mode names."""
    return list(get_handler_registry().keys())


def get_handler_class(mode: str):
    """Return the handler class for a mode."""
    registry = get_handler_registry()
    if mode not in registry:
        raise ValueError(f"不明なモード '{mode}'")
    return registry[mode]


def build_handler(
    config: Dict[str, Any],
    logger,
    config_loader=None,
    config_path=None,
    planning_context=None,
):
    """Validate config, create scanner if needed, and instantiate a handler."""
    mode = config["meta"]["mode"]
    handler_class = get_handler_class(mode)
    handler_class.validate_config(config, config_path=config_path)

    scanner = None
    if handler_class.REQUIRES_SCANNER:
        scanner = FileScanner(
            config["settings"]["target_directory"],
            logger,
            planning_context=planning_context,
        )

    return handler_class(
        config=config,
        scanner=scanner,
        logger=logger,
        config_loader=config_loader,
        planning_context=planning_context,
    )
