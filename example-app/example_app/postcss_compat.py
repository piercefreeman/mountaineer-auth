from pathlib import Path


def ensure_postcss_bin() -> None:
    """
    Normalize the local postcss CLI shim.

    Some npm/client combinations install `node_modules/.bin/postcss` as a copied
    ESM entrypoint instead of a symlink to `postcss-cli/index.js`. In that form,
    relative imports like `./lib/args.js` resolve against `.bin/` and the Mountaineer
    CSS build fails. We normalize it back to the package entrypoint before any app
    build/watch/server command runs.
    """

    views_root = Path(__file__).parent / "views"
    bin_path = views_root / "node_modules" / ".bin" / "postcss"
    target_path = views_root / "node_modules" / "postcss-cli" / "index.js"

    if not bin_path.exists() or not target_path.exists():
        return

    if bin_path.is_symlink() and bin_path.resolve() == target_path.resolve():
        return

    bin_path.unlink()
    bin_path.symlink_to(Path("../postcss-cli/index.js"))
