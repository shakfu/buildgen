<%page args="name, options={}" />
<%include file="common/pyproject.base.toml.mako" args="
    name=name,
    framework='c-extension',
    framework_pkg='',
    description='A Python C extension module',
    lang_classifier='C',
    options=options
"/>
