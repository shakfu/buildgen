"""Common utilities shared across build system generators."""

from buildgen.common.utils import UniqueList, check_output, env_var, always_true
from buildgen.common.platform import PLATFORM, PythonSystem
from buildgen.common.base import BaseGenerator, BaseBuilder
from buildgen.common.project import ProjectConfig, TargetConfig, DependencyConfig

__all__ = [
    "UniqueList",
    "check_output",
    "env_var",
    "always_true",
    "PLATFORM",
    "PythonSystem",
    "BaseGenerator",
    "BaseBuilder",
    "ProjectConfig",
    "TargetConfig",
    "DependencyConfig",
]
