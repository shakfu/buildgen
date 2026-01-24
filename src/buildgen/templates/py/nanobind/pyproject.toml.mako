<%page args="name, options={}" />
<%include file="common/pyproject.base.toml.mako" args="
    name=name,
    framework='nanobind',
    framework_pkg='nanobind',
    description='A Python extension module built with nanobind',
    lang_classifier='C++',
    options=options
"/>
