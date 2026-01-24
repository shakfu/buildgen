<%page args="name, options={}" />
<%include file="common/pyproject.base.toml.mako" args="
    name=name,
    framework='cython',
    framework_pkg='cython',
    description='A Python extension module built with Cython',
    lang_classifier='Cython',
    options=options
"/>
