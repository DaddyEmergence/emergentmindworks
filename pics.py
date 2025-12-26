#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

from PIL import Image

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

# ---------- helpers ----------

def is_marked_d(path: Path) -> bool:
    return "[D]" in path.stem

def mark_name(path: Path, new_ext: str) -> Path:
    # keep name, append [D], enforce ext
    return path.with_name(f"{path.stem}[D]{new_ext}")

def safe_tmp_name(final_path: Path) -> Path:
    # IMPORTANT: keep a real image extension so Pillow knows format
    # foo[D].jpg -> foo[D].tmp.jpg
    return final_path.with_name(final_path.stem + ".tmp" + final_path.suffix)

def fmt_bytes(n: int) -> str:
    n = float(n)
    for unit in ["B","KB","MB","GB","TB","PB"]:
        if n < 1024.0:
            return f"{n:.2f}{unit}" if unit != "B" else f"{int(n)}{unit}"
        n /= 1024.0
    return f"{n:.2f}EB"

def folder_size_bytes(folder: Path) -> int:
    total = 0
    for p in folder.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except FileNotFoundError:
                pass
    return total

def iter_images_flat(folder: Path) -> List[Path]:
    # flat scan (like your original) – fast and predictable
    files = []
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            files.append(p)
    return files

def iter_images_recursive(folder: Path) -> Iterable[Path]:
    for p in folder.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            yield p

def save_image_to_tmp(im: Image.Image, tmp_path: Path, quality: int) -> None:
    ext = tmp_path.suffix.lower()
    save_kwargs = {}

    if ext in {".jpg", ".jpeg"}:
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", im.size, (0, 0, 0))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
        save_kwargs["progressive"] = True

    elif ext == ".webp":
        if im.mode in ("RGBA", "LA"):
            # webp can handle alpha, but many users want consistent results
            pass
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6

    elif ext == ".png":
        # png "quality" doesn't apply the same way
        save_kwargs["optimize"] = True

    # ensure no stale tmp
    if tmp_path.exists():
        tmp_path.unlink()

    im.save(tmp_path, **save_kwargs)

def bake_one(
    src: Path,
    output_fmt: str,
    quality: int,
    delete_original_on_win: bool,
    backup_dir: Optional[Path],
    skip_if_marked: bool,
) -> Tuple[bool, str, int, int]:
    """
    Returns: (won, message, src_size, out_size)
    If won: writes marked output beside src and (optionally) deletes src.
    If not won: keeps src unchanged.
    """
    if skip_if_marked and is_marked_d(src):
        return False, f"⏭️ skip already marked {src.name}", 0, 0

    src_ext = src.suffix.lower()

    if output_fmt == "keep":
        target_ext = src_ext
    else:
        target_ext = "." + output_fmt

    final = mark_name(src, target_ext)
    tmp = safe_tmp_name(final)

    # optional backup of original
    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, backup_dir / src.name)

    src_size = src.stat().st_size

    with Image.open(src) as im:
        save_image_to_tmp(im, tmp, quality)

    if not tmp.exists():
        raise RuntimeError("Temp output was not created (save failed).")

    tmp_size = tmp.stat().st_size

    # wins rule:
    # - if keeping same format: only win if smaller
    # - if changing format: accept win (user asked for conversion)
    won = (tmp_size < src_size) if output_fmt == "keep" else True

    if won:
        if final.exists():
            final.unlink()
        tmp.rename(final)

        if delete_original_on_win:
            src.unlink(missing_ok=True)

        return True, f"✅ {src.name} -> {final.name} | {fmt_bytes(src_size)} -> {fmt_bytes(tmp_size)}", src_size, tmp_size

    # not a win: discard tmp
    tmp.unlink(missing_ok=True)
    return False, f"↩️ kept original {src.name} (no win)", src_size, src_size

# ---------- modes ----------

def run_folder_mode(
    input_dir: Path,
    output_fmt: str,
    quality: int,
    delete_original_on_win: bool,
    backup_dir: Optional[Path],
    skip_if_marked: bool,
    recursive: bool,
) -> str:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    before = folder_size_bytes(input_dir)

    files = list(iter_images_recursive(input_dir)) if recursive else iter_images_flat(input_dir)
    total = len(files)

    baked = kept = errors = 0

    print(f"Quality: {quality}")
    print(f"Found  : {total} images")
    print(f"Mark   : outputs get [D] in filename")
    print(f"Mode   : {'DELETE originals only when win' if delete_original_on_win else 'SAFE (no delete)'}")
    print(f"Scan   : {'recursive' if recursive else 'flat'}")
    print()

    for i, src in enumerate(files, start=1):
        pct = (i / total * 100.0) if total else 0.0
        try:
            won, message, _, _ = bake_one(
                src=src,
                output_fmt=output_fmt,
                quality=quality,
                delete_original_on_win=delete_original_on_win,
                backup_dir=backup_dir,
                skip_if_marked=skip_if_marked,
            )
            if won:
                baked += 1
            else:
                kept += 1
            print(f"[{i}/{total} | {pct:6.2f}%] {message}")
        except Exception as e:
            errors += 1
            print(f"[{i}/{total} | {pct:6.2f}%] ❌ {src.name} | ERROR: {e}")

    after = folder_size_bytes(input_dir)
    saved = before - after
    pct_saved = (saved / before * 100.0) if before else 0.0

    return (
        "\n===== FINALD SUMMARY =====\n"
        f"Total images   : {total}\n"
        f"Baked (wins)   : {baked}\n"
        f"Kept original  : {kept}\n"
        f"Errors         : {errors}\n"
        f"Total size     : {fmt_bytes(before)} -> {fmt_bytes(after)}\n"
        f"Saved          : {fmt_bytes(saved)} ({pct_saved:.2f}%)\n"
        "=========================\n"
    )

def default_all_roots() -> List[Path]:
    # common Termux-accessible media roots
    home = Path.home()
    shared = home / "storage" / "shared"
    candidates = [
        shared / "DCIM",
        shared / "Pictures",
        shared / "Download",
        shared / "WhatsApp" / "Media",
        shared / "Telegram",
    ]
    return [p for p in candidates if p.exists()]

def run_all_mode(
    output_fmt: str,
    quality: int,
    delete_original_on_win: bool,
    backup_dir: Optional[Path],
    skip_if_marked: bool,
    confirm: str,
) -> str:
    # hard safety lock
    required = "I UNDERSTAND THIS DELETES ORIGINALS"
    if delete_original_on_win and confirm.strip() != required:
        raise SystemExit(
            f"\nREFUSING: --delete-originals requires --confirm \"{required}\"\n"
        )

    roots = default_all_roots()
    if not roots:
        raise SystemExit("No default image roots found. (Need Termux storage access?)")

    # Create a master holding folder (just a name, we still operate in place)
    # You asked for “master clean” behavior; this is “operate in place across roots”.
    total_before = sum(folder_size_bytes(r) for r in roots)

    all_files = []
    for r in roots:
        all_files.extend(list(iter_images_recursive(r)))

    # filter
    files = [p for p in all_files if p.suffix.lower() in IMG_EXTS]
    if skip_if_marked:
        files = [p for p in files if not is_marked_d(p)]

    total = len(files)

    baked = kept = errors = 0

    print(f"ALL MODE roots:")
    for r in roots:
        print(f" - {r}")
    print(f"\nFound: {total} images total\n")

    for i, src in enumerate(files, start=1):
        pct = (i / total * 100.0) if total else 0.0
        try:
            won, message, _, _ = bake_one(
                src=src,
                output_fmt=output_fmt,
                quality=quality,
                delete_original_on_win=delete_original_on_win,
                backup_dir=backup_dir,
                skip_if_marked=skip_if_marked,
            )
            if won:
                baked += 1
            else:
                kept += 1
            print(f"[{i}/{total} | {pct:6.2f}%] {message}")
        except Exception as e:
            errors += 1
            print(f"[{i}/{total} | {pct:6.2f}%] ❌ {src.name} | ERROR: {e}")

    total_after = sum(folder_size_bytes(r) for r in roots)
    saved = total_before - total_after
    pct_saved = (saved / total_before * 100.0) if total_before else 0.0

    return (
        "\n===== FINALD ALL SUMMARY =====\n"
        f"Total images   : {total}\n"
        f"Baked (wins)   : {baked}\n"
        f"Kept original  : {kept}\n"
        f"Errors         : {errors}\n"
        f"Total size     : {fmt_bytes(total_before)} -> {fmt_bytes(total_after)}\n"
        f"Saved          : {fmt_bytes(saved)} ({pct_saved:.2f}%)\n"
        "=============================\n"
    )

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="finalD.py — mark + bake images on Android (Termux) with safe temp handling.")
    ap.add_argument("--mode", choices=["folder", "all"], default="folder", help="folder=single directory, all=scan common device image roots")
    ap.add_argument("--input", help="Input folder (folder mode)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders (folder mode)")
    ap.add_argument("--fmt", choices=["keep", "jpg", "png", "webp"], default="keep", help="Output format")
    ap.add_argument("--quality", type=int, default=85, help="JPEG/WebP quality (default 85)")
    ap.add_argument("--delete-originals", action="store_true", help="Delete originals only when win")
    ap.add_argument("--backup", help="Backup originals here before deletion (optional)")
    ap.add_argument("--skip-marked", action="store_true", default=True, help="Skip files already marked with [D] (default on)")
    ap.add_argument("--confirm", default="", help="Required for ALL+delete: I UNDERSTAND THIS DELETES ORIGINALS")

    args = ap.parse_args()

    backup_dir = Path(args.backup).expanduser().resolve() if args.backup else None

    if args.mode == "folder":
        if not args.input:
            print("ERROR: --input is required in folder mode.")
            sys.exit(1)
        input_dir = Path(args.input).expanduser().resolve()
        summary = run_folder_mode(
            input_dir=input_dir,
            output_fmt=args.fmt,
            quality=args.quality,
            delete_original_on_win=args.delete_originals,
            backup_dir=backup_dir,
            skip_if_marked=args.skip_marked,
            recursive=args.recursive,
        )
        print(summary)
        return

    # all mode
    summary = run_all_mode(
        output_fmt=args.fmt,
        quality=args.quality,
        delete_original_on_win=args.delete_originals,
        backup_dir=backup_dir,
        skip_if_marked=args.skip_marked,
        confirm=args.confirm,
    )
    print(summary)

if __name__ == "__main__":
    main()
