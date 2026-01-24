<%page args="name, options={}" />
<%include file="common/pyproject.base.toml.mako" args="
    name=name,
    framework='pybind11',
    framework_pkg='pybind11',
    description='A Python extension module built with pybind11',
    lang_classifier='C++',
    options=options
"/>
