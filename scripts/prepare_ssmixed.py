#!/usr/bin/env python3
"""Build the spectrogram-detection view of SSMixed from its three source datasets.

The script copies only the PNG files selected by the published COCO files and
writes a new SSMixed directory containing images/ and annotations/.  It never
changes the source datasets.

The three input directories may have arbitrary nested layouts, but each must
contain the source PNG files named by the `original_file_name` fields in the
published COCO annotations.  A duplicate PNG basename within one input is
treated as an error rather than guessed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("mir_st500", "ssvd3", "ismir2014")
SPLITS = ("train", "val", "test")


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def png_index(root: Path) -> dict[str, Path]:
    """Return a unique basename-to-path index for PNG files below root."""
    if not root.is_dir():
        raise FileNotFoundError(f"image directory does not exist: {root}")
    index: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".png":
            continue
        old = index.setdefault(path.name, path)
        if old != path:
            duplicates.append(path.name)
    if duplicates:
        examples = ", ".join(sorted(set(duplicates))[:10])
        raise RuntimeError(
            f"{root} contains duplicate PNG basenames; use a directory with "
            f"one copy of each source image. Examples: {examples}"
        )
    if not index:
        raise RuntimeError(f"no PNG files found below {root}")
    return index


def expected_membership() -> dict:
    return load_json(PACKAGE_ROOT / "splits" / "source_membership.json")


def validate_coco(coco: dict, split: str, membership: dict) -> None:
    categories = coco.get("categories")
    if categories != [{"id": 1, "name": "note", "supercategory": "none"}]:
        raise RuntimeError(f"{split}: unexpected category definition")
    images = coco.get("images", [])
    annotations = coco.get("annotations", [])
    ids = {image["id"] for image in images}
    if len(ids) != len(images):
        raise RuntimeError(f"{split}: duplicate image IDs")
    actual = {domain: set() for domain in DOMAINS}
    for image in images:
        domain = image.get("dataset_name")
        if domain not in actual:
            raise RuntimeError(f"{split}: unknown domain {domain!r}")
        filename = image.get("file_name", "")
        if Path(filename).is_absolute() or not filename.startswith(f"images/{split}/{domain}/"):
            raise RuntimeError(f"{split}: non-portable image path {filename!r}")
        if not image.get("original_file_name"):
            raise RuntimeError(f"{split}: missing original_file_name")
        actual[domain].add(str(image["source_id"]))
    for domain in DOMAINS:
        if actual[domain] != set(membership[split][domain]):
            raise RuntimeError(f"{split}/{domain}: COCO and source membership differ")
    for annotation in annotations:
        bbox = annotation.get("bbox", [])
        if annotation.get("image_id") not in ids or annotation.get("category_id") != 1:
            raise RuntimeError(f"{split}: invalid annotation identity")
        if len(bbox) != 4 or bbox[2] <= 0 or bbox[3] <= 0:
            raise RuntimeError(f"{split}: invalid bounding box")


def copy_coco_and_images(staging: Path, indexes: dict[str, dict[str, Path]]) -> dict[str, int]:
    membership = expected_membership()
    copied = {}
    for split in SPLITS:
        coco_path = PACKAGE_ROOT / "annotations" / f"{split}.coco.json"
        coco = load_json(coco_path)
        validate_coco(coco, split, membership)
        for image in coco["images"]:
            domain = image["dataset_name"]
            source_name = Path(image["original_file_name"]).name
            source = indexes[domain].get(source_name)
            if source is None:
                raise FileNotFoundError(
                    f"{split}/{domain}: cannot find {source_name!r} below the supplied input directory"
                )
            destination = staging / image["file_name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise RuntimeError(f"destination collision: {destination}")
            shutil.copy2(source, destination)
        destination_coco = staging / "annotations" / coco_path.name
        destination_coco.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(coco_path, destination_coco)
        copied[split] = len(coco["images"])
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assemble the spectrogram-detection version of SSMixed."
    )
    parser.add_argument("--mir-images", type=Path, required=True,
                        help="Directory containing MIR-ST500 source PNG images")
    parser.add_argument("--ssvd-images", type=Path, required=True,
                        help="Directory containing SSVD3.0 source PNG images")
    parser.add_argument("--ismir-images", type=Path, required=True,
                        help="Directory containing ISMIR2014 source PNG images")
    parser.add_argument("--output", type=Path, required=True,
                        help="New SSMixed directory to create")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    if output.parent == output:
        raise RuntimeError("refusing to create a filesystem root")
    indexes = {
        "mir_st500": png_index(args.mir_images.expanduser().resolve()),
        "ssvd3": png_index(args.ssvd_images.expanduser().resolve()),
        "ismir2014": png_index(args.ismir_images.expanduser().resolve()),
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        copied = copy_coco_and_images(staging, indexes)
        shutil.copy2(PACKAGE_ROOT / "README.md", staging / "README.md")
        os.replace(staging, output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(f"Created {output}")
    print("Images copied: " + ", ".join(f"{split}={count}" for split, count in copied.items()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
