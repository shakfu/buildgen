"""buildgen: Build system generator package.

Supports generating Makefiles, CMakeLists.txt, and direct compilation.

For additional components, import from submodules:
    from buildgen.makefile.variables import Var, SVar, IVar, CVar, AVar
    from buildgen.makefile.functions import Mk
    from buildgen.cmake.variables import CMakeVar, CMakeCacheVar
    from buildgen.cmake.functions import Cm
    from buildgen.common.project import TargetConfig, DependencyConfig
"""

__version__ = "0.3.1"

# Core API - minimal exports for early development flexibility
from buildgen.cmake.generator import CMakeListsGenerator
from buildgen.common.project import ProjectConfig
from buildgen.makefile.generator import MakefileGenerator

__all__ = [
    "CMakeListsGenerator",
    "MakefileGenerator",
    "ProjectConfig",
]
