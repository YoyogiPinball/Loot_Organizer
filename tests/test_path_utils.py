# -*- coding: utf-8 -*-
"""パス正規化ヘルパーの回帰テスト。"""

import ntpath
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.core.config_loader import ConfigLoader
from src.utils import path_utils
from src.utils.path_utils import to_path
from tests.conftest import posix_only, sort_config, write_yaml


def test_to_path_resolves_relative_path_and_parent_segments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert to_path("input/../output/file.txt") == tmp_path / "output" / "file.txt"


@posix_only
def test_to_path_normalizes_parent_segments_in_wsl_drive_path():
    assert to_path(r"D:\Images\..\Loot\file.txt") == Path(
        "/mnt/d/Loot/file.txt"
    )


@pytest.mark.parametrize("server", ["wsl.localhost", "wsl$"])
@posix_only
def test_to_path_converts_local_wsl_unc_path(server, monkeypatch):
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")

    assert to_path(
        rf"\\{server}\Ubuntu\home\testuser\Loot\..\file.txt"
    ) == Path("/home/testuser/file.txt")


@pytest.mark.parametrize("written_distro", ["ubuntu", "UBUNTU", "UbUnTu"])
@posix_only
def test_to_path_accepts_unc_distro_written_in_another_case(
    written_distro,
    monkeypatch,
):
    """Windows は UNC を大文字小文字を区別せず解決するため綴り違いを許す。"""
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")

    assert to_path(
        rf"\\wsl.localhost\{written_distro}\home\testuser\file.txt"
    ) == Path("/home/testuser/file.txt")


def test_to_path_keeps_wsl_unc_path_native_on_windows(monkeypatch):
    unc_path = r"\\wsl.localhost\Ubuntu\home\testuser\file.txt"
    windows_os = SimpleNamespace(name="nt", path=ntpath, environ={})
    monkeypatch.setattr(path_utils, "os", windows_os)

    assert to_path(unc_path) == Path(unc_path)


@pytest.mark.parametrize(
    ("configured_distro", "expected"),
    [
        ("Debian", "Debian"),
        (None, "未設定"),
    ],
)
def test_to_path_rejects_unc_when_local_distro_cannot_be_identified(
    configured_distro,
    expected,
    monkeypatch,
):
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")
    if configured_distro is None:
        monkeypatch.delenv("WSL_DISTRO_NAME", raising=False)
    else:
        monkeypatch.setenv("WSL_DISTRO_NAME", configured_distro)

    with pytest.raises(ValueError) as exc_info:
        to_path(r"\\wsl.localhost\Ubuntu\home\testuser\file.txt")

    message = str(exc_info.value)
    assert "別のディストリビューション名が指定されている" in message
    assert "Ubuntu" in message
    assert expected in message


@pytest.mark.parametrize(
    "network_path",
    [
        r"\\server\share\x",
        "//server/share/x",
    ],
)
def test_to_path_rejects_non_wsl_unc_on_posix(network_path, monkeypatch):
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")

    with pytest.raises(ValueError) as exc_info:
        to_path(network_path)

    message = str(exc_info.value)
    assert network_path in message
    assert "WSL からはネットワーク共有パスを解決できません" in message


def test_to_path_keeps_network_unc_native_on_windows(monkeypatch):
    network_path = r"\\server\share\x"
    windows_os = SimpleNamespace(name="nt", path=ntpath, environ={})
    monkeypatch.setattr(path_utils, "os", windows_os)

    assert to_path(network_path) == Path(network_path)


@posix_only
def test_to_path_keeps_single_slash_posix_absolute_path(monkeypatch):
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")

    assert to_path("/mnt/d/x") == Path("/mnt/d/x")


@pytest.mark.parametrize("posix_path", ["/mnt/d/x", "/home/testuser/loot"])
def test_to_path_rejects_posix_absolute_path_on_windows(posix_path, monkeypatch):
    """Windows では先頭 / が現在のドライブを指すため、黙って別の場所になる。"""
    windows_os = SimpleNamespace(name="nt", path=ntpath, environ={})
    monkeypatch.setattr(path_utils, "os", windows_os)

    with pytest.raises(ValueError) as exc_info:
        to_path(posix_path)

    message = str(exc_info.value)
    assert "Linux 形式の絶対パスを解決できません" in message
    assert posix_path in message


def test_to_path_keeps_drive_path_on_windows(monkeypatch):
    """拒否するのは先頭 / のパスだけ。ドライブ文字付きは従来どおり通す。"""
    windows_os = SimpleNamespace(name="nt", path=ntpath, environ={})
    monkeypatch.setattr(path_utils, "os", windows_os)

    assert to_path(r"D:\Loot\file.txt") == Path(r"D:\Loot\file.txt")


@posix_only
def test_config_loader_converts_pipeline_step_unc_path(tmp_path, monkeypatch):
    config_path = write_yaml(
        tmp_path / "step.yaml",
        sort_config(tmp_path, [{"pattern": "*", "dest": str(tmp_path / "dest")}]),
    )
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.setattr("src.utils.path_utils.os.name", "posix")
    unc_path = (
        r"\\wsl.localhost\Ubuntu"
        + str(config_path).replace("/", "\\")
    )

    loaded = ConfigLoader().load_config(unc_path)

    assert loaded["meta"]["name"] == "test-sort"


def test_config_loader_keeps_file_not_found_error_message(tmp_path):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(
        FileNotFoundError,
        # Windows のパスには \U などの正規表現エスケープに見える並びが入る
        match=rf"^設定ファイルが見つかりません: {re.escape(str(missing))}$",
    ):
        ConfigLoader().load_config(missing)
