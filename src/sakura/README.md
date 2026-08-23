# 🌸 Sakura

<p>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/config-TOML-9C4221?logo=toml&logoColor=white" alt="TOML"/>
  <img src="https://img.shields.io/badge/type-JetBrains%20Mono-000000?logo=jetbrains&logoColor=white" alt="JetBrains Mono"/>
  <img src="https://img.shields.io/badge/output-animated%20SVG-FFB13B?logo=svg&logoColor=white" alt="animated SVG"/>
  <img src="https://img.shields.io/badge/commits-Conventional-FE5196?logo=conventionalcommits&logoColor=white" alt="Conventional Commits"/>
  <img src="https://img.shields.io/badge/license-MIT-3DA639?logo=opensourceinitiative&logoColor=white" alt="MIT"/>
  <img src="https://img.shields.io/badge/Made%20with-Claude%20Code-D97757?logo=claude&logoColor=white" alt="Made with Claude Code"/>
</p>

**Sakura** grows a bonsai out of its pot one character at a time and unrolls a
profile card beside it, either live in a terminal or baked into an animated SVG
for a GitHub README. It is the whole profile page: nothing to serve, nothing to
keep running.

The tree is not generated. It was recovered from the original artwork, which was
itself a rendered ASCII grid — 70×125 px cells, sixteen distinct glyphs, 29
colours — so every character and colour in `art.py` is that artwork's, read back
rather than approximated. The reconstruction was exact, which is why the image is
no longer kept here; `git log --diff-filter=D -- src/sakura-original.png` finds
it. That constraint decides the rest: the growth may add limbs while it runs, but
the last frame has to come out identical to the source, so nothing is ever drawn
where a blossom will not later cover it.

## 📦 Dependencies

The terminal mode needs nothing but Python 3.11 or newer — `tomllib` is stdlib
from 3.11.

Rendering an SVG additionally needs `fonttools` with Brotli, to subset and embed
JetBrains Mono:

```sh
pip install "fonttools[woff]"
```

JetBrains Mono itself is looked up in `~/.local/share/fonts`, `~/.fonts`,
`/usr/share/fonts` and `/usr/local/share/fonts`. Without it the SVG still
renders, falling back to the viewer's own monospace font.

## 🚀 Running

```sh
python3 sakura.py
```

```sh
python3 sakura.py --render ../sakura-anim.svg
```

```sh
python3 sakura.py --render ../sakura-light.svg --light
```

| Flag | What it does |
| --- | --- |
| `--still` | print the finished picture and exit |
| `--tree-only` | drop the card, grow just the tree |
| `--render FILE.svg` | write an animated SVG instead of playing it |
| `--light` | render on white instead of the dark terminal window |
| `--config FILE.toml` | read the card and the palette from elsewhere |
| `--font DIR` | look for JetBrains Mono here |
| `--speed X` | terminal only, animation speed multiplier |
| `--loop` | terminal only, grow it again and again |
| `--no-color` | plain text |

`NO_COLOR` is honoured, and the terminal drops to the 256-colour cube when it
does not advertise truecolor. Piping gives plain text, so
`python3 sakura.py --still --no-color > tree.txt` is the whole export path.

## 🔧 Configuration

Everything the card says, and every colour that is not the tree's own, is in
[`profile.toml`](profile.toml).

| Key | Default | What it is |
| --- | --- | --- |
| `title` | `nktkln@github: ~/sakura` | text in the window's title bar |
| `name` | `NKTKLN` | the card's heading |
| `tagline` | `ML Engineer · Moscow` | one line under the name |
| `quote` | `«Data has a memory…»` | the line under the tagline |
| `footer` | `Thank you for visiting!` | last line, under the closing rule |
| `[[block]]` | two of them | one group of rows; keys are labels, values the text |

Blocks are separated by a blank line in the card, and every label across every
block shares one column — so a long label shifts them all. Inside a value, `" · "`
marks the item separator and is tinted apart from the words around it; long
values wrap under their own label.

### Render

| Key | Default | What it is |
| --- | --- | --- |
| `font_size` | `24` | px in the SVG; the terminal uses its own font |
| `tracking` | `1.16` | `1.0` is the font's own advance, higher spaces glyphs out |
| `leading` | `1.32` | line height in ems; the source art sat at `1.25` |
| `padding` | `64` | px of air between the window frame and the art |
| `bar_height` | `52` | px; the window buttons and its title scale with it |
| `duration` | `5.0` | seconds the growth takes, start to finish |
| `seed` | `7` | fixes the order the blossoms open in |

### Themes

`[dark]` and `[light]` hold one flat table of colours each — `paper`, `bar`,
`seam`, `frame`, `title`, `sheen`, `shadow`, their two alphas, the three `dots`,
and the card inks `head`, `tag`, `muted`, `mark`, `label`, `value`, `dot`,
`rule`, `rule_dim`. The defaults are GitHub's own canvas colours, so the card
sits on a README as if it belonged there.

Two things there are deliberate and worth keeping if you re-colour it. The card
inks separate by lightness *and* by hue — a rose `label` against a neutral
`value` — because two pastels from one family read as a single run of text. And
there is no green in the card: the tree owns that hue.

The tree's own 29 colours are not configurable. On a dark ground they are lifted
by `lift()`, which remaps the whole dark range at once instead of clamping it, so
the trunk becomes visible without losing the ramp from root to branch tip.

## 🌱 How the growth works

The pot settles bottom-up, the skeleton climbs out of it row by row, then the
canopy opens outwards from the crown. Horizontal distance is halved when ordering
the blossoms, because a terminal cell is about twice as tall as it is wide and
the bloom front should read as round.

The visible wood falls into sixteen disconnected pieces — each is the tip of a
branch the blossom hides. `ghost_branches()` routes every piece back to the trunk
with Dijkstra, passing only through cells a blossom will later cover, and those
thirty limbs fade out exactly as their blossom lands on them. So the tree grows a
whole skeleton before it flowers, and still ends as the original picture.

In the SVG this is one pass and then it stands still: two keyframes, one
`animation-delay` per group, `fill-mode: both` holding the end state. No loop, no
script, ~19 kB over the wire.

## 📁 Source layout

| Path | What is in it |
| --- | --- |
| `sakura.py` | the player, the SVG renderer, the growth |
| `art.py` | the recovered grid: characters, palette indices, layers |
| `profile.toml` | the card's text, the render metrics, the two themes |

## 📜 License

MIT, see [LICENSE](../../LICENSE).
