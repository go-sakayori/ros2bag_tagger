# ros2bag_tagger

## :rocket: Getting started

Clone the repository:

```sh
git clone --recursive git@github.com:go-sakayori/ros2bag_tagger.git
```

## How to use

| Verb                                      | What it does                                            | Key options                                               |
| ----------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------- |
| `ros2bag-tagger convert <bag.mcap>`       | Infer tags for a **single** bag and write `<bag>.json`. | `--out/-o <file>` custom output path                      |
| `ros2bag-tagger batch <dir>`              | Recursively tag every `.mcap` under a directory.        | `--template/-t <json>`, `--recursive/-r`, `--jobs/-j <N>` |
| `ros2bag-tagger template new <file>`      | Generate a fresh template JSON.                         | `--preset/-p minimal`                                     |
| `ros2bag-tagger template validate <file>` | Static validation of a template file.                   | N/A                                                       |

See `--help` on any verb for the full option list.

---
