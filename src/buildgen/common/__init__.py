"""Common utilities shared across build system generators."""

from buildgen.common.base import BaseBuilder, BaseGenerator
from buildgen.common.config import UserConfig, load_user_config
from buildgen.common.platform import PLATFORM, PythonSystem
from buildgen.common.project import DependencyConfig, ProjectConfig, TargetConfig
from buildgen.common.utils import UniqueList, always_true, check_output, env_var

__all__ = [
    "PLATFORM",
    "BaseBuilder",
    "BaseGenerator",
    "DependencyConfig",
    "ProjectConfig",
    "PythonSystem",
    "TargetConfig",
    "UniqueList",
    "UserConfig",
    "always_true",
    "check_output",
    "env_var",
    "load_user_config",
]
