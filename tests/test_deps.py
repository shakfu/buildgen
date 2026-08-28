"""Tests for dependency version resolution."""

import json
from unittest.mock import MagicMock, patch

from buildgen.common.deps import (
    BUILD_SYSTEM_PACKAGES,
    DEFAULT_VERSIONS,
    _fetch_latest_version,
    get_default_versions,
    resolve_latest_versions,
)


class TestDefaultVersions:
    """Test bundled default versions."""

    def test_all_expected_packages_present(self):
        expected = {
            "mypy",
            "pytest",
            "pytest-cov",
            "ruff",
            "twine",
            "pybind11-stubgen",
            "scikit-build-core",
            "uv-build",
        }
        assert expected == set(DEFAULT_VERSIONS.keys())

    def test_build_system_packages_subset(self):
        assert BUILD_SYSTEM_PACKAGES.issubset(DEFAULT_VERSIONS.keys())

    def test_get_default_versions_all(self):
        versions = get_default_versions()
        assert versions == DEFAULT_VERSIONS
        # must be a copy, not the same object
        assert versions is not DEFAULT_VERSIONS

    def test_get_default_versions_subset(self):
        versions = get_default_versions(["ruff", "mypy"])
        assert set(versions.keys()) == {"ruff", "mypy"}
        assert versions["ruff"] == DEFAULT_VERSIONS["ruff"]

    def test_get_default_versions_unknown_package(self):
        versions = get_default_versions(["nonexistent-pkg"])
        assert versions["nonexistent-pkg"] == "0"


class TestFetchLatestVersion:
    """Test PyPI version fetching."""

    def test_success(self):
        fake_response = MagicMock()
        fake_response.read.return_value = json.dumps(
            {"info": {"version": "99.0.0"}}
        ).encode()
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "buildgen.common.deps.urllib.request.urlopen", return_value=fake_response
        ):
            assert _fetch_latest_version("somepkg") == "99.0.0"

    def test_network_error_returns_none(self):
        import urllib.error

        with patch(
            "buildgen.common.deps.urllib.request.urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            assert _fetch_latest_version("somepkg") is None

    def test_bad_json_returns_none(self):
        fake_response = MagicMock()
        fake_response.read.return_value = b"not json"
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "buildgen.common.deps.urllib.request.urlopen", return_value=fake_response
        ):
            assert _fetch_latest_version("somepkg") is None


class TestResolveLatestVersions:
    """Test version resolution with fallback."""

    def test_uses_pypi_when_available(self):
        def fake_fetch(pkg):
            return "42.0.0"

        with patch(
            "buildgen.common.deps._fetch_latest_version", side_effect=fake_fetch
        ):
            versions = resolve_latest_versions(["ruff", "mypy"])
            assert versions == {"ruff": "42.0.0", "mypy": "42.0.0"}

    def test_falls_back_on_failure(self):
        with patch("buildgen.common.deps._fetch_latest_version", return_value=None):
            versions = resolve_latest_versions(["ruff"])
            assert versions["ruff"] == DEFAULT_VERSIONS["ruff"]

    def test_mixed_success_and_failure(self):
        def fake_fetch(pkg):
            if pkg == "ruff":
                return "99.0.0"
            return None

        with patch(
            "buildgen.common.deps._fetch_latest_version", side_effect=fake_fetch
        ):
            versions = resolve_latest_versions(["ruff", "mypy"])
            assert versions["ruff"] == "99.0.0"
            assert versions["mypy"] == DEFAULT_VERSIONS["mypy"]

    def test_resolves_all_defaults_when_no_packages(self):
        with patch("buildgen.common.deps._fetch_latest_version", return_value="1.0.0"):
            versions = resolve_latest_versions()
            assert set(versions.keys()) == set(DEFAULT_VERSIONS.keys())


class TestGeneratorIntegration:
    """Test that dep_versions flows through to generated output."""

    def test_default_versions_in_output(self, tmp_path):
        """Generated pyproject.toml should contain version strings from dep_versions."""
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator(
            "myext",
            "skbuild-pybind11",
            tmp_path / "myext",
            update_deps=False,
        )
        gen.generate()
        content = (tmp_path / "myext" / "pyproject.toml").read_text()
        for pkg in ("mypy", "pytest", "pytest-cov", "ruff", "twine"):
            expected_ver = DEFAULT_VERSIONS[pkg]
            assert f"{pkg}>={expected_ver}" in content

    def test_custom_versions_in_output(self, tmp_path):
        """Explicitly supplied dep_versions should appear in output."""
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator(
            "myext",
            "skbuild-pybind11",
            tmp_path / "myext",
            update_deps=False,
        )
        # Override after init
        gen.context["dep_versions"]["ruff"] = "99.9.9"
        gen.generate()
        content = (tmp_path / "myext" / "pyproject.toml").read_text()
        assert "ruff>=99.9.9" in content

    def test_update_deps_queries_pypi(self, tmp_path):
        """With update_deps=True, generator should use resolved versions."""
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        fake_versions = dict.fromkeys(DEFAULT_VERSIONS, "77.0.0")
        with patch(
            "buildgen.skbuild.generator.resolve_latest_versions",
            return_value=fake_versions,
        ):
            gen = SkbuildProjectGenerator(
                "myext",
                "skbuild-pybind11",
                tmp_path / "myext",
                update_deps=True,
            )
            gen.generate()
        content = (tmp_path / "myext" / "pyproject.toml").read_text()
        assert "ruff>=77.0.0" in content
        assert "scikit-build-core>=77.0.0" in content

    def test_flex_template_uses_dep_versions(self, tmp_path):
        """pybind11-flex template should also use dep_versions."""
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        gen = SkbuildProjectGenerator(
            "flexext",
            "skbuild-pybind11-flex",
            tmp_path / "flexext",
            update_deps=False,
        )
        gen.generate()
        content = (tmp_path / "flexext" / "pyproject.toml").read_text()
        for pkg in (
            "mypy",
            "pytest",
            "pytest-cov",
            "ruff",
            "twine",
            "pybind11-stubgen",
        ):
            expected_ver = DEFAULT_VERSIONS[pkg]
            assert f"{pkg}>={expected_ver}" in content

    def test_user_config_deps_override_defaults(self, tmp_path):
        """User config [deps] pins should override bundled defaults."""
        from buildgen.common.config import UserConfig
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        cfg = UserConfig(deps={"ruff": "0.10.0", "mypy": "1.15.0"})
        gen = SkbuildProjectGenerator(
            "myext",
            "skbuild-pybind11",
            tmp_path / "myext",
            update_deps=False,
            user_config=cfg,
        )
        gen.generate()
        content = (tmp_path / "myext" / "pyproject.toml").read_text()
        assert "ruff>=0.10.0" in content
        assert "mypy>=1.15.0" in content
        # unpinned packages still use defaults
        assert f"pytest>={DEFAULT_VERSIONS['pytest']}" in content

    def test_user_config_deps_override_pypi(self, tmp_path):
        """User config [deps] pins should override PyPI-resolved versions."""
        from buildgen.common.config import UserConfig
        from buildgen.skbuild.generator import SkbuildProjectGenerator

        cfg = UserConfig(deps={"ruff": "0.10.0"})
        fake_versions = dict.fromkeys(DEFAULT_VERSIONS, "77.0.0")
        with patch(
            "buildgen.skbuild.generator.resolve_latest_versions",
            return_value=fake_versions,
        ):
            gen = SkbuildProjectGenerator(
                "myext",
                "skbuild-pybind11",
                tmp_path / "myext",
                update_deps=True,
                user_config=cfg,
            )
            gen.generate()
        content = (tmp_path / "myext" / "pyproject.toml").read_text()
        # ruff pinned by user config, not PyPI
        assert "ruff>=0.10.0" in content
        # others got the PyPI version
        assert "mypy>=77.0.0" in content
