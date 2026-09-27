# SSMixed: A Three-Domain Dataset for Automatic Singing Transcription

SSMixed is a fixed three-domain dataset for automatic singing transcription. It combines MIR-ST500, SSVD3.0, and ISMIR2014 into one training set, validation set, and test set. The released package contains the source-level split, COCO note annotations, and a script that builds the spectrogram-detection dataset from locally obtained source images.

## Contents

```text
SSMixed/
├── annotations/                 # COCO annotations for train, val, and test
├── splits/
│   └── source_membership.json   # selected source IDs for every split and domain
├── scripts/
│   └── prepare_ssmixed.py       # creates the image-and-COCO dataset
└── README.md
```

## Dataset split

| Split | MIR-ST500 | SSVD3.0 | ISMIR2014 | Images | Note boxes |
|---|---:|---:|---:|---:|---:|
| Train | 100 sources | 100 sources | 27 sources | 6,423 | 39,343 |
| Validation | 37 sources | 30 sources | 3 sources | 2,156 | 14,027 |
| Test | 100 sources | 100 sources | 8 sources | 5,684 | 36,556 |
| **Total** | **237 sources** | **230 sources** | **38 sources** | **14,263** | **89,926** |

All slices from one original source are assigned to the same split. The selected source IDs are listed in `splits/source_membership.json`.

## Annotation format

`annotations/train.coco.json`, `annotations/val.coco.json`, and `annotations/test.coco.json` use the standard COCO format. There is one category:

```json
{"id": 1, "name": "note", "supercategory": "none"}
```

Every image record includes the domain, source ID, and a destination-relative image path:

```json
{
  "id": 1,
  "file_name": "images/train/mir_st500/198_03_009.png",
  "dataset_name": "mir_st500",
  "source_id": "198"
}
```

## Build SSMixed

First obtain MIR-ST500, SSVD3.0, and ISMIR2014 from their original sources. Prepare one directory for each dataset that contains its corresponding spectrogram PNG files. The directory may contain subdirectories, but every required PNG basename must occur exactly once inside that dataset directory.

Run the following command from this repository:

```bash
python scripts/prepare_ssmixed.py \
  --mir-images /path/to/MIR-ST500/pngs \
  --ssvd-images /path/to/SSVD3/pngs \
  --ismir-images /path/to/ISMIR2014/pngs \
  --output /path/to/SSMixed
```

The command creates:

```text
SSMixed/
├── annotations/
│   ├── train.coco.json
│   ├── val.coco.json
│   └── test.coco.json
├── images/
│   ├── train/{mir_st500,ssvd3,ismir2014}/
│   ├── val/{mir_st500,ssvd3,ismir2014}/
│   └── test/{mir_st500,ssvd3,ismir2014}/
└── README.md
```

The script copies only the selected PNG files and does not modify the three input datasets. It uses only Python's standard library.

## Training entry points

Use the generated SSMixed root as the image root:

```text
training annotations:   <SSMixed>/annotations/train.coco.json
validation annotations: <SSMixed>/annotations/val.coco.json
test annotations:       <SSMixed>/annotations/test.coco.json
image root:             <SSMixed>
```

For frameworks that use zero-based internal class indices, map COCO category `1` (`note`) to internal class index `0` without changing the COCO files.

## Citation

Please cite the accompanying SSMixed study and the original MIR-ST500, SSVD3.0, and ISMIR2014 dataset papers when using this split.

```bibtex
@article{ssmixed,
  title   = {To be added},
  author  = {To be added},
  year    = {To be added}
}
```
