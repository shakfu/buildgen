<%page args="name, options={}" />
<%include file="common/pyproject.base.toml.mako" args="
    name=name,
    framework='python',
    framework_pkg=None,
    description='A pure-Python package with no runtime dependencies',
    lang_classifier=None,
    native=False,
    options=options
"/>

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
src = ["src", "tests"]

[tool.mypy]
strict = true
