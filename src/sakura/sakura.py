#!/usr/bin/env python3
"""Grow the sakura bonsai, in colour, with the profile card unrolling alongside
it -- either live in a terminal or baked into an animated SVG.

The tree comes from ``art.py``, recovered character by character out of the
original image. Everything the card says, and every colour that is not the
tree's own, lives in ``profile.toml``.

    python3 sakura.py                       # watch it grow
    python3 sakura.py --render out.svg      # bake it into an animated SVG
    python3 sakura.py --still               # print it and exit

See README.md for the rest of the flags and for what is configurable.
"""

import argparse
import colorsys
import heapq
import math
import os
import random
import shutil
import sys
import time

import tomllib

from art import ART, COLOR, COLS, LAYER, PALETTE, ROWS

CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'profile.toml')

BOLD = frozenset(('head', 'label'))          # ink keys drawn at weight 700
BULLET = '\u25b8'      # a small marker that points at the label
TAPER = '\u2504\u2504\u2504\u2504'   # a rule thins to this at both ends

PAD = ''              # left margin that centres the whole thing in the terminal
POT_X = 31            # the pot's centre column: the axis the composition hangs on
TRUNK_X = 31          # the trunk sits here, branches spread away from it
CROWN = (6.0, 34.0)   # row/col the canopy blooms out from
FADE = 0.18           # seconds a glyph takes to appear
CAP = 0.730           # JetBrains Mono cap height, in em
DOT_R_EM = 0.155      # button radius, as a fraction of the bar's height
TITLE_EM = 0.40       # title type, ditto -- so the two always stay in step
OUT = 22.0            # room outside the window for its shadow


def load(path=CONF_PATH):
    """Read profile.toml into the handful of globals the rest of this uses."""
    global CFG, NAME, TAGLINE, QUOTE, FOOTER, TITLE, BLOCKS
    global DARK, LIGHT, INK, SEED, DURATION
    global FS, TRACK, LEAD, CW, CH, BASE, PAD_IN, PAD_Y, BAR, DOT_R, TITLE_FS

    with open(path, 'rb') as fh:
        CFG = tomllib.load(fh)

    NAME = CFG['name']
    TAGLINE = CFG['tagline']
    QUOTE = CFG['quote']
    FOOTER = CFG['footer']
    TITLE = CFG['title']
    BLOCKS = [tuple(block.items()) for block in CFG['block']]

    DARK, LIGHT = CFG['dark'], CFG['light']
    INK = DARK                              # the terminal is the dark case

    r = CFG['render']
    SEED, DURATION = r['seed'], float(r['duration'])
    FS = float(r['font_size'])
    TRACK = float(r['tracking'])
    LEAD = float(r['leading'])
    PAD_IN = float(r['padding'])
    PAD_Y = float(r['padding_y'])
    BAR = float(r['bar_height'])
    DOT_R = BAR * DOT_R_EM
    TITLE_FS = BAR * TITLE_EM
    CW = FS * 0.6 * TRACK   # cell advance; 0.6em is a monospace font's own step
    CH = FS * LEAD          # line height
    BASE = 0.808 * CH       # baseline inside a cell, measured off the source art


load()

# --------------------------------------------------------------------------- #
# colour

def _truecolor(r, g, b):
    return '\x1b[38;2;%d;%d;%dm' % (r, g, b)


def _cube256(r, g, b):
    if abs(r - g) < 8 and abs(g - b) < 8:            # grey ramp is finer
        return '\x1b[38;5;%dm' % (232 + min(23, (r * 23) // 255))
    q = lambda v: (v * 5 + 127) // 255
    return '\x1b[38;5;%dm' % (16 + 36 * q(r) + 6 * q(g) + q(b))


def pick_mode(force_plain):
    if force_plain or os.environ.get('NO_COLOR') or not sys.stdout.isatty():
        return None
    if os.environ.get('COLORTERM', '') in ('truecolor', '24bit'):
        return _truecolor
    if '256' in os.environ.get('TERM', ''):
        return _cube256
    return _truecolor


def unhex(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


RGB = tuple(unhex(c) for c in PALETTE)
_RGB_CACHE = {}


def RGB_OF(hexc):
    if hexc not in _RGB_CACHE:
        _RGB_CACHE[hexc] = unhex(hexc)
    return _RGB_CACHE[hexc]


def lighten(rgb, k):
    """Blend towards white -- a bud before it opens, a petal catching light."""
    return tuple(int(v + (255 - v) * k) for v in rgb)


# --------------------------------------------------------------------------- #
# laying the card out


def _centre(spans, width):
    """Centre on the pot's axis, not on the grid, so nothing sits half a cell off."""
    pad = POT_X - sum(len(t) for t, _ in spans) // 2
    return ([(' ' * pad, None)] if pad > 0 else []) + list(spans)


def _rule(width):
    """A stroke that thins to a dashed taper at both ends."""
    mid = width - 2 * len(TAPER)
    mid -= 1 - mid % 2                      # odd, so it sits square on POT_X
    return _centre([(TAPER, 'rule_dim'), ('\u2500' * mid, 'rule'),
                    (TAPER[::-1], 'rule_dim')], width)


def _atoms(value):
    """Words and the README's dot separator, each already carrying its style."""
    out = []
    for i, part in enumerate(value.split(' \u00b7 ')):
        if i:
            out.append(('\u00b7', 'dot'))
        out.extend((w, 'value') for w in part.split(' ') if w)
    return out


def _fill(atoms, room):
    lines, cur, used = [], [], 0
    for text, key in atoms:
        step = len(text) + (1 if cur else 0)
        if cur and used + step > room:
            lines.append(cur)
            cur, used, step = [], 0, len(text)
        if cur:
            cur.append((' ', None))
        cur.append((text, key))
        used += step
    if cur:
        lines.append(cur)
    return lines


def _rows(pairs, width, indent=2, lab=None):
    lab = lab or max(len(l) for l, _ in pairs)
    head = ' ' * indent + BULLET + ' '
    col = len(head) + lab + 2
    lines = []
    for label, value in pairs:
        for i, chunk in enumerate(_fill(_atoms(value), max(24, width - col - 2))):
            lines.append(([(head, 'mark'), (label.ljust(lab) + '  ', 'label')]
                          if i == 0 else [(' ' * col, None)]) + chunk)
    return lines


def build_card(width):
    """The card as span-lines: (text, ink key) runs, one list per line."""
    lab = max(len(label) for block in BLOCKS for label, _ in block)
    lines = [[], _rule(width), [],
             _centre([(NAME, 'head')], width),
             _centre([(TAGLINE, 'tag')], width), [],
             _centre([(QUOTE, 'muted')], width), []]
    for i, block in enumerate(BLOCKS):
        if i:
            lines.append([])
        lines += _rows(block, width, lab=lab)
    lines += [[], _rule(width), []]
    lines += [_centre([(FOOTER, 'muted')], width)]
    return lines


def card_width():
    """Same width as the tree, so the two blocks share a centre line."""
    return min(COLS, max(40, shutil.get_terminal_size((80, 24)).columns - 1))


# --------------------------------------------------------------------------- #
# unrolling it


def _flatten(spans):
    return [(ch, colour) for text, colour in spans for ch in text]


def _paint_chars(chars, paint, glow_from):
    out, last = [], None
    for i, (ch, key) in enumerate(chars):
        if key is None or not paint:
            out.append(ch)
            continue
        rgb = RGB_OF(INK[key])
        if i >= glow_from:
            rgb = lighten(rgb, 0.5)
        esc = ('\x1b[1m' if key in BOLD else '\x1b[22m') + paint(*rgb)
        if esc != last:
            out.append(esc)
            last = esc
        out.append(ch)
    if last is not None:
        out.append('\x1b[0m')
    return ''.join(out)


def card_frame(cells, costs, budget, paint, glow):
    out, start = [], 0
    for chars, cost in zip(cells, costs):
        seen = max(0, min(len(chars), budget - start))
        active = glow and start <= budget < start + cost
        out.append(_paint_chars(chars[:seen], paint,
                                max(0, seen - glow) if active else len(chars)))
        start += cost
    return out


def reveal_card(card, paint, speed):
    cells = [_flatten(l) for l in card]
    costs = [max(len(c), 6) for c in cells]     # blank lines still take a beat
    total = sum(costs)
    step = max(4, int(round(16 * speed)))
    delay = 0.035 / speed
    budget, first = 0, True
    while budget < total:
        budget = min(total, budget + step)
        draw_in_place(card_frame(cells, costs, budget, paint, 10), first, len(cells))
        first = False
        time.sleep(delay)
    draw_in_place(card_frame(cells, costs, total, paint, 0), False, len(cells))


def still_card(card, paint):
    cells = [_flatten(l) for l in card]
    costs = [len(c) for c in cells]
    sys.stdout.write('\n'.join(
        (PAD + ln).rstrip()
        for ln in card_frame(cells, costs, sum(costs), paint, 0)) + '\n')


# --------------------------------------------------------------------------- #
# the limbs the picture hides


WOOD_RAMP = ('#5a4037', '#6e4c42', '#7b5c50', '#9c7b6d', '#b99588')


def _components(cells):
    seen, out = set(), []
    for cell in sorted(cells):
        if cell in seen:
            continue
        stack, comp = [cell], []
        while stack:
            r, c = stack.pop()
            if (r, c) in seen or (r, c) not in cells:
                continue
            seen.add((r, c))
            comp.append((r, c))
            stack += [(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def _step_cost(r, c):
    """Only blossom and wood are passable: a limb routed across open sky would
    still be standing there after the canopy filled in, and the finished picture
    has to come out exactly as the original."""
    layer = LAYER[r][c]
    if layer == 'w':
        return 0
    return 1 if layer == 'f' else None


def _route(sources, target):
    """Dijkstra from everything already attached to the trunk, to one fragment."""
    dist = {cell: 0 for cell in sources}
    prev, heap = {}, [(0, cell) for cell in sources]
    heapq.heapify(heap)
    goal = set(target)
    while heap:
        d, (r, c) = heapq.heappop(heap)
        if d > dist.get((r, c), 1e9):
            continue
        if (r, c) in goal:
            path = []
            while (r, c) in prev:
                path.append((r, c))
                r, c = prev[(r, c)]
            return path
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < ROWS and 0 <= nc < COLS) or (dr == 0 and dc == 0):
                    continue
                cost = _step_cost(nr, nc)
                if cost is None and (nr, nc) not in goal:
                    continue
                nd = d + (cost or 0)
                if nd < dist.get((nr, nc), 1e9):
                    dist[(nr, nc)] = nd
                    prev[(nr, nc)] = (r, c)
                    heapq.heappush(heap, (nd, (nr, nc)))
    return []


def _limb_char(prv, cell, nxt):
    dr = (nxt or cell)[0] - (prv or cell)[0]
    dc = (nxt or cell)[1] - (prv or cell)[1]
    if dc == 0:
        return '|'
    if dr == 0:
        return '_'
    return '/' if (dr < 0) == (dc > 0) else '\\'


def ghost_branches():
    """Wood shows through the canopy in sixteen disconnected pieces; every piece
    is the tip of a branch the blossom hides. Route each one back to the trunk so
    the tree grows a whole skeleton, then flowers over it."""
    wood = {(r, c) for r in range(ROWS) for c in range(COLS) if LAYER[r][c] == 'w'}
    comps = _components(wood)
    attached, ghosts = set(comps[0]), {}
    for comp in comps[1:]:
        path = _route(attached, comp)
        if not path:
            continue
        path.reverse()                       # trunk end first
        for i, cell in enumerate(path):
            if cell in attached or LAYER[cell[0]][cell[1]] == 'w':
                continue
            prv = path[i - 1] if i else None
            nxt = path[i + 1] if i + 1 < len(path) else None
            depth = min(len(WOOD_RAMP) - 1, 1 + i * 2 // max(1, len(path)) + 1)
            ghosts[cell] = (_limb_char(prv, cell, nxt), WOOD_RAMP[depth])
        attached |= set(path) | set(comp)
    return ghosts


GHOSTS = ghost_branches()


# --------------------------------------------------------------------------- #
# the order things grow in


def growth_order(rng):
    """Cells tagged 'p' pot, 'w' wood, 'g' hidden limb, 'f' blossom."""
    pot, wood, foliage = [], [], []
    for r in range(ROWS):
        for c in range(COLS):
            layer = LAYER[r][c]
            if layer == 'p':
                pot.append((r, c, 'p'))
            elif layer == 'w':
                wood.append((r, c, 'w'))
            elif layer == 'f':
                foliage.append((r, c, 'f'))
    wood += [(r, c, 'g') for r, c in GHOSTS]        # limbs the blossom will bury

    # the pot settles bottom-up, the whole skeleton climbs out of it row by row
    pot.sort(key=lambda t: (-t[0], abs(t[1] - TRUNK_X)))
    wood.sort(key=lambda t: (-t[0], abs(t[1] - TRUNK_X)))

    # blossom opens outwards from the crown; cells are twice as tall as wide,
    # so halve the horizontal distance to keep the bloom front round on screen
    cr, cc = CROWN
    foliage.sort(key=lambda t: math.hypot((t[1] - cc) * 0.5, t[0] - cr)
                 + rng.uniform(0.0, 2.5))
    return [(pot, 6), (wood, 5), (foliage, 11)]


# --------------------------------------------------------------------------- #
# drawing


def render(shown, limbs, age, paint):
    """One frame: 26 lines, one escape only where the colour actually changes."""
    out = []
    for r in range(ROWS):
        line, last, tail_ws = [], None, 0
        for c in range(COLS):
            if (r, c) in shown:
                ch = ART[r][c]
                rgb = RGB[ord(COLOR[r][c]) - 33]
            elif (r, c) in limbs:
                ch, hexc = GHOSTS[(r, c)]
                rgb = RGB_OF(hexc)
            else:
                tail_ws += 1
                continue
            if ch == ' ':
                tail_ws += 1
                continue
            a = age.get((r, c), 99)
            if a < 3:
                rgb = lighten(rgb, (0.55, 0.35, 0.15)[a])
            if paint:
                esc = paint(*rgb)
                if esc != last:
                    line.append(esc)
                    last = esc
            line.append(' ' * tail_ws)
            tail_ws = 0
            line.append(ch)
        out.append(''.join(line) + ('\x1b[0m' if paint and last else ''))
    return out


def draw_in_place(lines, first, height=None):
    buf = [] if first else ['\x1b[%dA' % (len(lines) if height is None else height)]
    for ln in lines:
        buf.append('\x1b[2K' + (PAD + ln if ln else '') + '\n')
    sys.stdout.write(''.join(buf))
    sys.stdout.flush()


def growth_plan(rng):
    """The whole growth as a list of frames, each naming the cells it lights."""
    frames = []
    for cells, per_frame in growth_order(rng):
        for i in range(0, len(cells), per_frame):
            frames.append(cells[i:i + per_frame])
        frames += [(), (), (), ()]      # a beat between pot, trunk and blossom
    return frames


def animate(paint, speed, plan, cells, costs, together):
    """Grow the tree; if there is room, unroll the card in the same frames."""
    delay = 0.035 / speed
    total = sum(costs)
    height = ROWS + (len(cells) if together else 0)
    shown, limbs, age, first = set(), set(), {}, True
    for i, batch in enumerate(plan):
        for r, c, kind in batch:
            (limbs if kind == 'g' else shown).add((r, c))
            age[(r, c)] = 0
        lines = render(shown, limbs, age, paint)
        if together:
            lines += card_frame(cells, costs,
                                int(round(total * (i + 1) / len(plan))), paint, 10)
        draw_in_place(lines, first, height)
        first = False
        for rc in age:
            age[rc] += 1
        time.sleep(delay)
    if together:
        draw_in_place(render(shown, limbs, age, paint)
                      + card_frame(cells, costs, total, paint, 0), False, height)


def still(paint):
    every = {(r, c) for r in range(ROWS) for c in range(COLS)}
    sys.stdout.write('\n'.join(PAD + ln
                                for ln in render(every, set(), {}, paint)) + '\n')


# --------------------------------------------------------------------------- #
# the other mode: the same growth baked into one animated SVG


def lift(hexc, floor=0.38, ceil=0.72, knee=0.65):
    """Dark ink disappears on a dark ground. Lift the trunk and the pot into
    view, but map the whole range at once so the ramp between them survives --
    flattening every dark colour onto one value would cost the tree its depth.
    Blossom already sits above the knee and is left exactly as it was."""
    r, g, b = (v / 255.0 for v in unhex(hexc))
    h, l, sat = colorsys.rgb_to_hls(r, g, b)
    if l >= knee:
        return hexc
    l = floor + (l - 0.20) / (knee - 0.20) * (ceil - floor)
    r, g, b = colorsys.hls_to_rgb(h, min(1.0, max(0.0, l)), sat)
    return '#%02x%02x%02x' % (int(r * 255 + .5), int(g * 255 + .5), int(b * 255 + .5))

FONT_DIRS = ('~/.local/share/fonts', '~/.fonts', '/usr/share/fonts',
             '/usr/local/share/fonts')
BODY_FACES = ('Medium', 'Regular')
BOLD_FACES = ('Bold', 'ExtraBold', 'SemiBold')


def find_font(styles, explicit=None):
    import glob
    roots = [explicit] if explicit else [os.path.expanduser(d) for d in FONT_DIRS]
    for style in styles:
        for root in roots:
            hits = sorted(glob.glob(os.path.join(root, '**', 'JetBrainsMono*-%s.ttf' % style),
                                    recursive=True))
            if hits:
                return hits[0]
    return None


def embed_font(path, chars):
    """Subset to the glyphs actually drawn, then woff2 -- a few kB, not a few hundred."""
    import base64
    import io
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    opts = subset.Options(layout_features=[], notdef_outline=True)
    opts.drop_tables += ['GSUB', 'GPOS', 'GDEF', 'kern', 'morx']
    sub = subset.Subsetter(options=opts)
    sub.populate(text=''.join(sorted(chars)))
    sub.subset(font)
    # fontTools stamps head with the build clock; pin it so the diff of a
    # re-render is not dominated by a timestamp. The woff2 bytes can still vary
    # slightly between runs -- that is inside fontTools, not here -- so the
    # committed SVG is not bit-reproducible even though the picture is identical.
    font['head'].created = font['head'].modified = 3660249600   # 2020-01-01
    font.flavor = 'woff2'
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _card_cells(card):
    """Card characters as (row, col, char, ink key), spaces dropped."""
    out = []
    for i, line in enumerate(card):
        col = 0
        for text, key in line:
            for ch in text:
                if ch != ' ' and key:
                    out.append((ROWS + i, col, ch, key))
                col += 1
    return out


def _xml(ch):
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;'}.get(ch, ch)


def render_svg(path, font_dir=None, light=False):
    theme = LIGHT if light else DARK
    tone = (lambda c: c) if light else lift
    rng = random.Random(SEED)
    plan = growth_plan(rng)
    card = build_card(COLS)
    n = len(plan)

    # when each hidden limb gets buried by its blossom
    buried = {}
    for i, batch in enumerate(plan):
        for r, c, kind in batch:
            if kind == 'f' and (r, c) in GHOSTS:
                buried[(r, c)] = i

    # the card unrolls on the same clock as the tree
    chars = _card_cells(card)
    costs = []
    for i, line in enumerate(card):
        costs.append(max(len(''.join(t for t, _ in line)), 6))
    total = sum(costs)
    starts, run = [], 0
    for cost in costs:
        starts.append(run)
        run += cost
    frame_of = {}
    for row, col, ch, key in chars:
        idx = starts[row - ROWS] + col
        frame_of[(row, col)] = min(n - 1, int(idx * n / total))

    body, bold, groups = set(TITLE), set(), [[] for _ in range(n)]
    limbs = []
    for i, batch in enumerate(plan):
        for r, c, kind in batch:
            if kind == 'g':
                ch, hexc = GHOSTS[(r, c)]
                limbs.append((i, buried.get((r, c), n - 1), r, c, ch, tone(hexc)))
            else:
                ch = ART[r][c]
                groups[i].append(
                    (r, c, ch, tone(PALETTE[ord(COLOR[r][c]) - 33]), False))
            body.add(ch)
    for row, col, ch, key in chars:
        strong = key in BOLD
        (bold if strong else body).add(ch)
        groups[frame_of[(row, col)]].append((row, col, ch, theme[key], strong))


    content_w = COLS * CW
    win_w = content_w + 2 * PAD_IN
    win_h = BAR + 2 * PAD_Y + (ROWS + len(card)) * CH
    w, h = win_w + 2 * OUT, win_h + 2 * OUT

    def place(r, c):
        return (OUT + PAD_IN + (c + 0.5) * CW,
                OUT + BAR + PAD_Y + r * CH + BASE)

    def at(i):
        return i / n * DURATION

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" '
           'width="%.0f" height="%.0f" role="img" '
           'aria-label="NKTKLN -- ASCII sakura bonsai">' % (w, h, w, h),
           '<title>NKTKLN</title>', '<defs>',
           '<clipPath id="win"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
           'rx="14"/></clipPath>' % (OUT, OUT, win_w, win_h),
           '<filter id="drop" x="-20%%" y="-20%%" width="140%%" height="140%%">'
           '<feDropShadow dx="0" dy="9" stdDeviation="13" flood-color="%s" '
           'flood-opacity="%.2f"/></filter>'
           % (theme['shadow'], theme['shadow_alpha'])]

    # One pass, then it stands still: every group runs its animation once and
    # keeps the end state, so nothing loops and nothing redraws after the growth.
    css = ['text{font-family:JBM,ui-monospace,SFMono-Regular,Menlo,monospace;'
           'font-size:%.2fpx;text-anchor:middle;white-space:pre}' % FS,
           '.b{font-weight:700}',
           '.t{font-size:%.2fpx}' % TITLE_FS,
           '@keyframes in{from{opacity:0}to{opacity:1}}',
           '@keyframes out{from{opacity:1}to{opacity:0}}',
           '.g{opacity:0;animation:in %.2fs ease-out both}' % FADE,
           '.l{opacity:0;animation:in %.2fs ease-out both,'
           'out %.2fs ease-in forwards}' % (FADE, FADE)]

    faces = []
    body_path = find_font(BODY_FACES, font_dir)
    bold_path = find_font(BOLD_FACES, font_dir)
    if body_path:
        faces.append((500, body_path, body))
        if bold_path and bold:
            faces.append((700, bold_path, bold))
    for weight, fpath, glyphs in faces:
        css.insert(0, "@font-face{font-family:JBM;font-style:normal;font-weight:%d;"
                      "src:url(data:font/woff2;base64,%s) format('woff2')}"
                      % (weight, embed_font(fpath, glyphs | set(' '))))
    if not faces:
        sys.stderr.write("JetBrains Mono not found, falling back to the "
                         "viewer's monospace font\n")

    out.append('<style>%s</style>' % ''.join(css))
    out.append('</defs>')

    # the window it all sits in
    bx, by = OUT, OUT
    # the shadow is cast by a plain rect behind the window: filtering the whole
    # group would clip the bloom against the filter region and leave a seam
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="14" '
               'fill="%s" filter="url(#drop)"/>'
               % (bx, by, win_w, win_h, theme['paper']))
    out.append('<g clip-path="url(#win)">')
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
               % (bx, by, win_w, win_h, theme['paper']))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>'
               % (bx, by, win_w, BAR, theme['bar']))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="1" fill="%s"/>'
               % (bx, by + BAR, win_w, theme['seam']))
    for j, dot in enumerate(theme['dots']):
        out.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                   % (bx + 26 + j * DOT_R * 3.5, by + BAR / 2, DOT_R, dot))
    # centred on the bar both ways: half the cap height puts the optical middle
    # of the letters on the middle of the bar, which the baseline alone does not
    out.append('<text class="t" x="%.1f" y="%.1f" fill="%s">%s</text>'
               % (bx + win_w / 2, by + BAR / 2 + CAP * TITLE_FS / 2,
                  theme['title'], _xml(TITLE)))
    out.append('</g>')
    # a hairline inside the edge reads as glass; the frame itself sits outside it
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="13" '
               'fill="none" stroke="%s" stroke-opacity="%.3f"/>'
               % (bx + 1.5, by + 1.5, win_w - 3, win_h - 3,
                  theme['sheen'], theme['sheen_alpha']))
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="14" '
               'fill="none" stroke="%s"/>'
               % (bx + 0.5, by + 0.5, win_w - 1, win_h - 1, theme['frame']))

    for born, gone, r, c, ch, hexc in limbs:
        x, y = place(r, c)
        out.append('<g class="l" style="animation-delay:%.2fs,%.2fs">'
                   '<text x="%.1f" y="%.1f" fill="%s">%s</text></g>'
                   % (at(born), at(gone), x, y, hexc, _xml(ch)))

    for i, cells in enumerate(groups):
        if not cells:
            continue
        parts = ['<g class="g" style="animation-delay:%.2fs">' % at(i)]
        for r, c, ch, colour, strong in cells:
            x, y = place(r, c)
            parts.append('<text%s x="%.1f" y="%.1f" fill="%s">%s</text>'
                         % (' class="b"' if strong else '', x, y, colour, _xml(ch)))
        parts.append('</g>')
        out.append(''.join(parts))

    out.append('</svg>')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out) + '\n')
    return w, h, os.path.getsize(path)


# --------------------------------------------------------------------------- #


def main():
    ap = argparse.ArgumentParser(description='Grow an ASCII sakura bonsai.')
    ap.add_argument('--still', action='store_true', help='print it, do not animate')
    ap.add_argument('--tree-only', action='store_true', help='skip the profile card')
    ap.add_argument('--render', metavar='FILE.svg',
                    help='render the animation to an animated SVG instead of playing it')
    ap.add_argument('--config', metavar='FILE.toml',
                    help='read the card and the palette from somewhere else')
    ap.add_argument('--light', action='store_true',
                    help='SVG: light paper instead of the dark terminal window')
    ap.add_argument('--font', metavar='DIR', help='SVG: where to look for JetBrains Mono')
    ap.add_argument('--speed', type=float, default=1.0, metavar='X',
                    help='animation speed multiplier (default: 1.0)')
    ap.add_argument('--loop', action='store_true', help='grow it again, forever')
    ap.add_argument('--no-color', action='store_true', help='plain text')
    args = ap.parse_args()

    global PAD
    if args.config:
        load(args.config)
    if args.render:
        w, h, size = render_svg(args.render, args.font, args.light)
        sys.stderr.write('%s  %.0fx%.0f  %.1f kB\n' % (args.render, w, h, size / 1024))
        return

    paint = pick_mode(args.no_color)
    card = None if args.tree_only else build_card(card_width())

    if args.still or not sys.stdout.isatty():
        still(paint)
        if card:
            still_card(card, paint)
        return

    width, height = shutil.get_terminal_size((80, 24))
    if width < COLS:
        sys.stderr.write('terminal is %d columns, the tree needs %d\n' % (width, COLS))
    PAD = ' ' * max(0, (width - 1) // 2 - POT_X)

    cells = [_flatten(l) for l in card] if card else []
    costs = [max(len(c), 6) for c in cells]
    # both blocks share the frame only if the terminal is tall enough to hold them
    together = bool(cells) and height >= ROWS + len(cells) + 1

    rng = random.Random(SEED)
    sys.stdout.write('\x1b[?25l')
    try:
        speed = max(0.05, args.speed)
        while True:
            animate(paint, speed, growth_plan(rng), cells, costs, together)
            if cells and not together:
                reveal_card(card, paint, speed)
            if not args.loop:
                break
            time.sleep(1.6 / speed)
            sys.stdout.write('\x1b[%dA' % (ROWS + len(cells)))
    except KeyboardInterrupt:
        pass          # a frame always ends on the line below the tree
    finally:
        sys.stdout.write('\x1b[?25h\x1b[0m')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
