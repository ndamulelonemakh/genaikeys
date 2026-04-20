"""Command-line interface for genaikeys."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .keeper import GenAIKeys

logger = logging.getLogger(__name__)

_LINE_RE = re.compile(r"""^(?P<indent>\s*)(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*?)\s*$""")
_NEEDS_QUOTING_RE = re.compile(r"[\s#\"'`$\\]")


@dataclass(frozen=True)
class _ParsedLine:
    raw: str
    key: str | None
    value: str | None
    prefix: str
    suffix: str


def _parse_line(line: str) -> _ParsedLine:
    stripped = line.rstrip("\n")
    if not stripped.strip() or stripped.lstrip().startswith("#"):
        return _ParsedLine(raw=line, key=None, value=None, prefix="", suffix="")

    inline_comment = ""
    code = stripped
    in_single = in_double = False
    for i, ch in enumerate(stripped):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            code = stripped[:i].rstrip()
            inline_comment = " " + stripped[i:]
            break

    match = _LINE_RE.match(code)
    if match is None:
        return _ParsedLine(raw=line, key=None, value=None, prefix="", suffix="")

    raw_value = match.group("value")
    value = _unquote(raw_value)
    prefix = code[: match.start("value")]
    return _ParsedLine(raw=line, key=match.group("key"), value=value, prefix=prefix, suffix=inline_comment)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _quote(value: str) -> str:
    if value == "" or _NEEDS_QUOTING_RE.search(value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def fill_env_file(
    source: str,
    resolver: Callable[[str], str | None],
    overwrite: bool = False,
) -> tuple[str, list[str], list[str]]:
    """Return (rendered_text, filled_keys, missing_keys)."""
    filled: list[str] = []
    missing: list[str] = []
    out_lines: list[str] = []

    for raw in source.splitlines(keepends=True):
        parsed = _parse_line(raw)
        if parsed.key is None:
            out_lines.append(parsed.raw)
            continue

        if parsed.value and not overwrite:
            out_lines.append(parsed.raw)
            continue

        looked_up = resolver(parsed.key)
        if looked_up is None:
            missing.append(parsed.key)
            out_lines.append(parsed.raw)
            continue

        newline = "\n" if parsed.raw.endswith("\n") else ""
        out_lines.append(f"{parsed.prefix}{_quote(looked_up)}{parsed.suffix}{newline}")
        filled.append(parsed.key)

    return "".join(out_lines), filled, missing


def parse_env_file(source: str) -> list[tuple[str, str]]:
    """Return non-empty (key, value) pairs from a .env-style string, preserving order."""
    pairs: list[tuple[str, str]] = []
    for raw in source.splitlines():
        parsed = _parse_line(raw)
        if parsed.key is None or parsed.value is None or parsed.value == "":
            continue
        pairs.append((parsed.key, parsed.value))
    return pairs


def _build_keeper(args: argparse.Namespace) -> GenAIKeys:
    backend = args.backend
    if args.keyvault and backend in (None, "azure"):
        return GenAIKeys.azure(vault_url=args.keyvault)
    if backend == "azure":
        return GenAIKeys.azure(vault_url=args.keyvault)
    if backend == "aws":
        return GenAIKeys.aws(region_name=args.region, profile_name=args.profile)
    if backend == "gcp":
        return GenAIKeys.gcp(project_id=args.project_id)
    return GenAIKeys.azure(vault_url=args.keyvault)


def _resolver_from_keeper(keeper: GenAIKeys) -> Callable[[str], str | None]:
    def _lookup(key: str) -> str | None:
        try:
            return keeper.get(key)
        except Exception as exc:
            logger.debug("lookup failed for %s: %s", key, exc)
            return None

    return _lookup


def _print_summary(filled: Iterable[str], missing: Iterable[str], destination: str, dry_run: bool) -> None:
    filled_list = list(filled)
    missing_list = list(missing)
    action = "would fill" if dry_run else "filled"
    print(f"{action} {len(filled_list)} value(s)" + (f" -> {destination}" if not dry_run else ""))
    for key in filled_list:
        print(f"  + {key}")
    if missing_list:
        print(f"missing in vault ({len(missing_list)}):", file=sys.stderr)
        for key in missing_list:
            print(f"  - {key}", file=sys.stderr)


def _cmd_fill(args: argparse.Namespace) -> int:
    source_path = Path(args.file)
    if not source_path.is_file():
        print(f"error: {source_path} not found", file=sys.stderr)
        return 2

    source_text = source_path.read_text(encoding="utf-8")
    keeper = _build_keeper(args)
    rendered, filled, missing = fill_env_file(source_text, _resolver_from_keeper(keeper), overwrite=args.overwrite)

    destination = args.output or str(source_path)
    if args.dry_run:
        sys.stdout.write(rendered)
    else:
        Path(destination).write_text(rendered, encoding="utf-8")

    _print_summary(filled, missing, destination, args.dry_run)
    if missing and args.strict:
        return 1
    return 0


def _cmd_push(args: argparse.Namespace) -> int:
    source_path = Path(args.file)
    if not source_path.is_file():
        print(f"error: {source_path} not found", file=sys.stderr)
        return 2

    pairs = parse_env_file(source_path.read_text(encoding="utf-8"))
    only = {k.strip() for k in args.only.split(",")} if args.only else None
    if only:
        pairs = [(k, v) for k, v in pairs if k in only]

    if not pairs:
        print("nothing to push (no non-empty keys matched)", file=sys.stderr)
        return 0

    keeper = _build_keeper(args)
    pushed: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for key, value in pairs:
        if not args.overwrite:
            try:
                if keeper.exists(key):
                    skipped.append(key)
                    continue
            except NotImplementedError:
                pass
            except Exception as exc:
                logger.debug("exists() check failed for %s: %s", key, exc)
        if args.dry_run:
            pushed.append(key)
            continue
        try:
            keeper.put(key, value)
            pushed.append(key)
        except Exception as exc:
            failed.append((key, type(exc).__name__))

    action = "would push" if args.dry_run else "pushed"
    print(f"{action} {len(pushed)} secret(s) from {source_path}")
    for key in pushed:
        print(f"  + {key}")
    if skipped:
        print(f"skipped (already in vault, use --overwrite): {len(skipped)}", file=sys.stderr)
        for key in skipped:
            print(f"  = {key}", file=sys.stderr)
    if failed:
        print(f"failed ({len(failed)}):", file=sys.stderr)
        for key, reason in failed:
            print(f"  ! {key}: {reason}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genaikeys",
        description="Manage Generative AI secrets across cloud vaults.",
    )
    parser.add_argument("--version", action="version", version=f"genaikeys {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    fill = sub.add_parser("fill", help="Populate a .env file from a secret vault.")
    fill.add_argument("file", help="Path to the .env (or .env.example) file.")
    fill.add_argument(
        "--backend",
        choices=["azure", "aws", "gcp"],
        default="azure",
        help="Secret backend to use (default: azure).",
    )
    fill.add_argument("--keyvault", help="Azure Key Vault URL (implies --backend azure).")
    fill.add_argument("--region", help="AWS region.")
    fill.add_argument("--profile", help="AWS profile.")
    fill.add_argument("--project-id", dest="project_id", help="GCP project id.")
    fill.add_argument("--output", help="Write to this path instead of editing in place.")
    fill.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing values; by default only empty values are populated.",
    )
    fill.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rendered file to stdout without writing.",
    )
    fill.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status when any key is missing in the vault.",
    )
    fill.set_defaults(func=_cmd_fill)

    push = sub.add_parser("push", help="Upload values from a .env file into a secret vault.")
    push.add_argument("file", help="Path to the .env file containing values to upload.")
    push.add_argument(
        "--backend",
        choices=["azure", "aws", "gcp"],
        default="azure",
        help="Secret backend to use (default: azure).",
    )
    push.add_argument("--keyvault", help="Azure Key Vault URL (implies --backend azure).")
    push.add_argument("--region", help="AWS region.")
    push.add_argument("--profile", help="AWS profile.")
    push.add_argument("--project-id", dest="project_id", help="GCP project id.")
    push.add_argument(
        "--only",
        help="Comma-separated list of keys to push; others are ignored.",
    )
    push.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite secrets that already exist in the vault (default: skip).",
    )
    push.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be pushed without calling the backend.",
    )
    push.set_defaults(func=_cmd_push)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
