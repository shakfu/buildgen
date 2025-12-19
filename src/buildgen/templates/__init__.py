"""Buildgen template system with override support.

Templates are resolved in this order (first match wins):
1. Environment variable: $BUILDGEN_TEMPLATES/{type}/
2. Project-local: .buildgen/templates/{type}/
3. User-global: ~/.buildgen/templates/{type}/
4. Built-in: src/buildgen/templates/{type}/
"""

from buildgen.templates.resolver import (
    BUILTIN_TEMPLATES_DIR,
    TemplateResolver,
    copy_templates,
    get_builtin_template_types,
)

__all__ = [
    "BUILTIN_TEMPLATES_DIR",
    "TemplateResolver",
    "copy_templates",
    "get_builtin_template_types",
]
