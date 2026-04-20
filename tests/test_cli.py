from unittest.mock import patch

import pytest

from genaikeys.cli import build_parser, fill_env_file, main
from tests.helpers import FakePlugin


def _resolver(secrets: dict[str, str]):
    return lambda key: secrets.get(key)


def test_fills_only_empty_values_by_default():
    source = "FOO=\nBAR=already\nBAZ=\n"
    rendered, filled, missing = fill_env_file(source, _resolver({"FOO": "f", "BAR": "new", "BAZ": "z"}))
    assert rendered == "FOO=f\nBAR=already\nBAZ=z\n"
    assert filled == ["FOO", "BAZ"]
    assert missing == []


def test_overwrite_replaces_existing_values():
    source = "FOO=old\nBAR=keep\n"
    rendered, filled, _ = fill_env_file(source, _resolver({"FOO": "new"}), overwrite=True)
    assert "FOO=new" in rendered
    assert "BAR=keep" in rendered
    assert filled == ["FOO"]


def test_preserves_comments_blank_lines_and_inline_comments():
    source = "# header\n\nFOO=  # tbd\nBAR=set\n"
    rendered, filled, _ = fill_env_file(source, _resolver({"FOO": "v"}))
    assert rendered.startswith("# header\n\n")
    assert "FOO=v # tbd" in rendered
    assert "BAR=set" in rendered
    assert filled == ["FOO"]


def test_quotes_values_with_special_chars():
    source = "FOO=\nBAR=\n"
    rendered, _, _ = fill_env_file(source, _resolver({"FOO": "a b#c", "BAR": "plain"}))
    assert 'FOO="a b#c"' in rendered
    assert "BAR=plain" in rendered


def test_escapes_quotes_and_backslashes_in_values():
    source = "TOK=\n"
    rendered, _, _ = fill_env_file(source, _resolver({"TOK": 'he said "hi"\\path'}))
    assert r'TOK="he said \"hi\"\\path"' in rendered


def test_missing_keys_are_reported_and_left_unchanged():
    source = "FOO=\nMISSING=\n"
    rendered, filled, missing = fill_env_file(source, _resolver({"FOO": "f"}))
    assert "MISSING=" in rendered
    assert filled == ["FOO"]
    assert missing == ["MISSING"]


def test_export_prefix_is_preserved():
    source = "export FOO=\n"
    rendered, filled, _ = fill_env_file(source, _resolver({"FOO": "v"}))
    assert rendered == "export FOO=v\n"
    assert filled == ["FOO"]


def test_unparsable_lines_pass_through():
    source = "not a kv line\nFOO=\n"
    rendered, filled, _ = fill_env_file(source, _resolver({"FOO": "v"}))
    assert rendered.startswith("not a kv line\n")
    assert "FOO=v" in rendered
    assert filled == ["FOO"]


def test_parser_requires_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_main_fill_writes_in_place(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=\nKEEP=ok\n", encoding="utf-8")
    plugin = FakePlugin({"OPENAI_API_KEY": "sk-test"})

    with patch("genaikeys.cli.GenAIKeys.azure", return_value=__import__("genaikeys").GenAIKeys(plugin)):
        rc = main(["fill", str(env), "--keyvault", "https://example.vault.azure.net"])

    assert rc == 0
    text = env.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=sk-test" in text
    assert "KEEP=ok" in text


def test_main_fill_dry_run_does_not_write(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("FOO=\n", encoding="utf-8")
    plugin = FakePlugin({"FOO": "bar"})

    with patch("genaikeys.cli.GenAIKeys.azure", return_value=__import__("genaikeys").GenAIKeys(plugin)):
        rc = main(["fill", str(env), "--dry-run"])

    assert rc == 0
    assert env.read_text(encoding="utf-8") == "FOO=\n"
    out = capsys.readouterr().out
    assert "FOO=bar" in out


def test_main_fill_strict_returns_nonzero_on_missing(tmp_path):
    env = tmp_path / ".env"
    env.write_text("ABSENT=\n", encoding="utf-8")
    plugin = FakePlugin({})

    with patch("genaikeys.cli.GenAIKeys.azure", return_value=__import__("genaikeys").GenAIKeys(plugin)):
        rc = main(["fill", str(env), "--strict"])

    assert rc == 1


def test_main_fill_missing_file_returns_2(tmp_path):
    rc = main(["fill", str(tmp_path / "nope.env")])
    assert rc == 2


def test_main_fill_writes_to_output(tmp_path):
    env = tmp_path / ".env.example"
    env.write_text("FOO=\n", encoding="utf-8")
    out = tmp_path / ".env"
    plugin = FakePlugin({"FOO": "bar"})

    with patch("genaikeys.cli.GenAIKeys.azure", return_value=__import__("genaikeys").GenAIKeys(plugin)):
        rc = main(["fill", str(env), "--output", str(out)])

    assert rc == 0
    assert env.read_text(encoding="utf-8") == "FOO=\n"
    assert "FOO=bar" in out.read_text(encoding="utf-8")


def test_console_script_entry_point_resolves():
    from importlib.metadata import entry_points

    scripts = entry_points(group="console_scripts")
    names = {ep.name for ep in scripts}
    if "genaikeys" in names:
        ep = next(ep for ep in scripts if ep.name == "genaikeys")
        assert ep.value == "genaikeys.cli:main"
    else:
        pytest.skip("console script not installed in this environment")
