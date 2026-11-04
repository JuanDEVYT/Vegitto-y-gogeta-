#!/usr/bin/env python3
"""Genera kino-plugin.json: plugin de TEMAS de la app para Kino (appThemes, apiVersion 18).

El logo de cada tema es el logo real de Kino (el wordmark "kino" + la "TV" y la marca de la "o",
con la geometría de app/src/main/java/app/kino/demo/ui/brand/KinoWordmark.kt de kinotvapp/kino-light)
con detalles de los dos personajes:

  · las letras y el aro de la "o" siguen en textPrimary, como el logo original;
  · un mechón de pelo pegado a la "k" (nace dentro del trazo, así que queda unido a la letra);
  · la "i" lleva un aro (el aro Potara) en vez del punto redondo;
  · el punto de la "o" va partido en dos colores y la barra bajo "kino" también;
  · la marca del TV (el riel cerrado) es la "o" con el círculo partido y el mechón encima.

`logo.paths` solo rellena (no hay `stroke`), así que los trazos de Kino (grosor 42, extremos
redondos) se convierten a contornos rellenos equivalentes, con coordenadas enteras para que el
manifiesto quepa en sus 16 KB.

Solo usa lo que aceptan a la vez contract.json del kit (apiVersion 20) y el de los docs
(apiVersion 21): nada de `decor` ni de bordes (llegan con Kino 0.9.82), así se instala desde
Kino 0.9.81, la versión que estrena los temas.

Uso: python3 tools/gen_manifest.py
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- SVG helpers
def nf(v):
    return str(int(round(v)))

def d_of(polys):
    out = []
    for pts in polys:
        s = "M" + nf(pts[0][0]) + " " + nf(pts[0][1])
        for q in pts[1:]:
            s += "L" + nf(q[0]) + " " + nf(q[1])
        out.append(s + "Z")
    return "".join(out)

def xf(pts, ox, oy):
    return [(x + ox, y + oy) for x, y in pts]

def circle(cx, cy, r, seg=16):
    return [(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / seg),
             cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / seg)) for i in range(seg)]

def annulus(cx, cy, r_out, r_in, seg=20):
    return [circle(cx, cy, r_out, seg), list(reversed(circle(cx, cy, r_in, seg)))]

def half_disc(cx, cy, r, side, seg=12):
    """Medio círculo: 'left' va del fondo a la punta por la izquierda; 'right' por la derecha."""
    a0, a1 = (90, 270) if side == "left" else (270, 450)
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / seg)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / seg))) for i in range(seg + 1)]

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

def capsule(p1, p2, r, seg=7):
    """Trazos de Kino: grosor 42 y extremos redondos -> contorno relleno."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    n = (-d[1], d[0])
    pts = [(p1[0] + n[0] * r, p1[1] + n[1] * r), (p2[0] + n[0] * r, p2[1] + n[1] * r)]
    for k in range(seg + 1):                     # remate redondo del final
        t = math.pi * k / seg
        c, s = math.cos(t), math.sin(t)
        pts.append((p2[0] + r * (n[0] * c + d[0] * s), p2[1] + r * (n[1] * c + d[1] * s)))
    pts.append((p1[0] - n[0] * r, p1[1] - n[1] * r))
    for k in range(seg + 1):                     # remate redondo del inicio
        t = math.pi * k / seg
        c, s = math.cos(t), math.sin(t)
        pts.append((p1[0] - r * (n[0] * c + d[0] * s), p1[1] - r * (n[1] * c + d[1] * s)))
    return pts

def cubic(p0, p1, p2, p3, steps=8):
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out

def thick_curve(pts, r):
    """Contorno relleno de una polilínea (el arco de la "n"): la normal desplazada a cada lado."""
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        left.append((p[0] + nx * r, p[1] + ny * r))
        right.append((p[0] - nx * r, p[1] - ny * r))
    return left + list(reversed(right))

def tuft(cx, cy, angles, radii, r0=9.0):
    """Mechón de pelo pegado: los mechones nacen en un círculo pequeño DENTRO del trazo de la
    letra (r0), así que la figura queda unida a la letra y no flotando encima."""
    out = []
    for i, r in enumerate(radii):
        a0, a1 = math.radians(angles[i]), math.radians(angles[i + 1])
        mid = math.radians((angles[i] + angles[i + 1]) / 2)
        out.append([(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)),
                    (cx + r * math.cos(mid), cy + r * math.sin(mid)),
                    (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1))])
    return out

# ---------------------------------------------------------------- logo de Kino (KinoWordmark.kt)
LEFT, RIGHT, TOP, BOTTOM = 126.0, 984.0, 84.0, 350.0
STROKE, TV_STROKE = 42.0, 26.0
O_C = (687.0, 252.0)
O_RADIUS, O_STROKE = 80.0, 35.0
I_DOT, I_DOT_RADIUS = (343.0, 123.0), 25.0
R, RT = STROKE / 2, TV_STROKE / 2
K_TOP = (142.0, 122.0)               # esquina superior del asta de la "k": ahí nace el mechón
TUFT_ROOT = 16.0                     # raíz sólida del mechón, dentro del trazo de la letra
BAR_Y0, BAR_Y1 = 356.0, 366.0        # la barra bajo "kino"
BAR_X0, BAR_X1, BAR_SPLIT = 126.0, 600.0, 340.0

def kino_k():
    return [capsule((147, 133), (147, 324), R),
            capsule((267, 170), (199, 250), R),
            capsule((199, 250), (270, 324), R),
            capsule((152, 250), (199, 250), R)]

def kino_i_stem():
    return [capsule((343, 185), (343, 324), R)]

def kino_n():
    arch = cubic((422, 255), (422, 210), (452, 182), (490, 182), 8) + \
        cubic((490, 182), (524, 182), (544, 206), (544, 242), 8)[1:]
    return [capsule((422, 324), (422, 185), R), thick_curve(arch, R), capsule((544, 242), (544, 324), R)]

def kino_tv():
    return [capsule((791, 97), (862, 97), RT, 6),
            capsule((826, 97), (826, 182), RT, 6),
            capsule((896, 97), (933, 182), RT, 6),
            capsule((933, 182), (971, 97), RT, 6)]

def kino_o_ring():
    return annulus(O_C[0], O_C[1], O_RADIUS + O_STROKE / 2, O_RADIUS - O_STROKE / 2, 20)

def wordmark_tuft(which):
    """Mechón sobre la "k": una raíz sólida dentro del trazo y mechones hacia arriba."""
    angles = [184, 218, 250, 282, 314, 348]             # 5 mechones: 6 bordes
    radii = [54, 70, 82, 66, 50]
    spikes = tuft(K_TOP[0], K_TOP[1], angles, radii, 20.0)
    root = [circle(K_TOP[0], K_TOP[1], TUFT_ROOT, 12)]
    return (spikes[:2] + root, spikes[2:]) if which == "a_first" else (spikes[2:] + root, spikes[:2])

def mark_tuft(which):
    """Mechón sobre la marca: nace dentro del anillo de la "o"."""
    cx, cy = MARK_C[0], MARK_C[1] - 82.0
    angles = [198, 236, 268, 300, 338]                  # 4 mechones: 5 bordes
    radii = [66, 82, 70, 54]
    spikes = tuft(cx, cy, angles, radii, 20.0)
    root = [circle(cx, cy, TUFT_ROOT, 12)]
    return (spikes[:2] + root, spikes[2:]) if which == "a_first" else (spikes[2:] + root, spikes[:2])

# ---------------------------------------------------------------- paletas (los dos personajes)
BLUE = "#2E9BFF"     # la faja azul de Gogeta
GOLD = "#FFD24A"     # el aro Potara de Vegitto / las botas de Gogeta
CYAN = "#35D6FF"     # el pelo de Vegitto
ORANGE = "#FF8C1E"   # el pelo y el chaleco de Gogeta

THEMES = [
    {
        "id": "vegitto",
        "name": {"es": "Vegitto Azul", "en": "Blue Vegitto"},
        # Vegitto: gi azul casi negro, pelo cian, faja naranja, guantes azul claro, aro Potara de oro.
        "colors": {
            "accent": CYAN, "onAccent": "#00131C",
            "surface": "#0A1626", "surfaceHigh": "#142C4A",
            "textPrimary": "#EAF7FF", "textSecondary": "#A9C4DC",
            "focus": "#9FE8FF", "onFocus": "#00131C",
            "outline": "#8FB8D8", "railPanel": "#040C16",
            "placeholderTop": "#0D2135", "placeholderBottom": "#08131F",
            "success": "#3EE8A8", "warning": "#FF9E2C", "error": "#FF5C77",
            "favorite": "#FF9E2C", "scrim": "#02070D",
        },
        "background": {"type": "gradient", "colors": ["#03070E", "#061426", "#0A2240"], "angle": 165},
        "shape": {"cardRadius": 12, "channelRadius": 14, "buttonRadius": 22, "chipRadius": 18,
                  "dialogRadius": 20, "inputRadius": 10},
        "typography": {"scale": 1.0, "titleScale": 1.06, "bodyScale": 1.0},
        "elevation": {"cardShadow": 0.45, "dialogShadow": 0.5, "heroScrim": 0.86},
        "motion": {"focusZoom": 1.06, "crossfadeMs": 220, "heroDrift": "on"},
        "player": {"buttonScale": 1.05, "playButtonScale": 1.18, "seekBarScale": 1.15,
                   "labelScale": 1.0, "buttonShape": "circle"},
        "adjustable": {
            "colors.accent": {"swatches": [CYAN, "#4D7CFF", "#00C2A8", "#EAF7FF"]},
            "colors.focus": {"swatches": ["#9FE8FF", GOLD, "#FFFFFF"]},
            "shape.cardRadius": {"min": 0, "max": 24},
            "typography.scale": {"min": 0.9, "max": 1.2},
            "player.buttonShape": True,
            "background": True,
        },
        "logo_colors": (CYAN, GOLD),
    },
    {
        "id": "gogeta",
        "name": {"es": "Gogeta Fuego", "en": "Fire Gogeta"},
        # Gogeta: chaleco naranja, camiseta y pantalón claros, faja azul, botas doradas.
        "colors": {
            "accent": ORANGE, "onAccent": "#1A0A00",
            "surface": "#1A0C07", "surfaceHigh": "#2C1509",
            "textPrimary": "#FFF6EC", "textSecondary": "#D8B79E",
            "focus": "#FFC63D", "onFocus": "#241400",
            "outline": BLUE, "railPanel": "#0C0302",
            "placeholderTop": "#241008", "placeholderBottom": "#140604",
            "success": "#4ADE80", "warning": "#FFB020", "error": "#FF4D4D",
            "favorite": "#FF4B3E", "scrim": "#080202",
        },
        "background": {"type": "gradient", "colors": ["#100402", "#1B0803", "#280D05"], "angle": 200},
        "shape": {"cardRadius": 16, "channelRadius": 16, "buttonRadius": 26, "chipRadius": 22,
                  "dialogRadius": 24, "inputRadius": 12},
        "typography": {"scale": 1.02, "titleScale": 1.1, "bodyScale": 1.0},
        "elevation": {"cardShadow": 0.5, "dialogShadow": 0.55, "heroScrim": 0.8},
        "motion": {"focusZoom": 1.09, "crossfadeMs": 160, "heroDrift": "on"},
        "player": {"buttonScale": 1.1, "playButtonScale": 1.25, "seekBarScale": 1.2,
                   "labelScale": 1.05, "buttonShape": "circle"},
        "adjustable": {
            "colors.accent": {"swatches": [ORANGE, "#FF4D1F", GOLD, "#FF2E63"]},
            "colors.focus": {"swatches": ["#FFC63D", "#4FC3FF", "#FFFFFF"]},
            "shape.cardRadius": {"min": 0, "max": 28},
            "typography.scale": {"min": 0.9, "max": 1.2},
            "player.buttonShape": True,
            "background": True,
        },
        "logo_colors": (ORANGE, BLUE),
    },
    {
        "id": "fusion",
        "name": {"es": "Fusión V+G", "en": "V+G Fusion"},
        # Los dos: naranja y azul de los dos personajes, con el oro y el cian de Vegitto.
        "colors": {
            "accent": "#FFC63D", "onAccent": "#1A1100",
            "surface": "#101827", "surfaceHigh": "#1B2637",
            "textPrimary": "#F2F7FF", "textSecondary": "#BAC8DD",
            "focus": "#55E6FF", "onFocus": "#001018",
            "outline": BLUE, "railPanel": "#060B16",
            "placeholderTop": "#0E1830", "placeholderBottom": "#120B08",
            "success": "#34E0A1", "warning": "#FFB020", "error": "#FF5B6E",
            "favorite": "#FF6B9D", "scrim": "#03060E",
        },
        "background": {"type": "gradient", "colors": ["#040A18", "#0A1024", "#170B07"], "angle": 135},
        "shape": {"cardRadius": 14, "channelRadius": 14, "buttonRadius": 24, "chipRadius": 20,
                  "dialogRadius": 22, "inputRadius": 11},
        "typography": {"scale": 1.02, "titleScale": 1.08, "bodyScale": 1.0},
        "elevation": {"cardShadow": 0.5, "dialogShadow": 0.55, "heroScrim": 0.85},
        "motion": {"focusZoom": 1.08, "crossfadeMs": 200, "heroDrift": "on"},
        "player": {"buttonScale": 1.08, "playButtonScale": 1.22, "seekBarScale": 1.18,
                   "labelScale": 1.02, "buttonShape": "rounded"},
        "adjustable": {
            "colors.accent": {"swatches": ["#FFC63D", CYAN, ORANGE, "#8B7BFF"]},
            "colors.focus": {"swatches": ["#55E6FF", GOLD, "#FFFFFF"]},
            "shape.cardRadius": {"min": 0, "max": 26},
            "typography.scale": {"min": 0.9, "max": 1.2},
            "player.buttonShape": True,
            "background": True,
        },
        "logo_colors": (ORANGE, BLUE),
    },
]

# ---------------------------------------------------------------- montaje del logo
MARK_C = (98.0, 138.0)
MARK_INNER_R = 58.0
PAD = 12

def bbox(polys):
    xs = [p[0] for poly in polys for p in poly]
    ys = [p[1] for poly in polys for p in poly]
    return min(xs), min(ys), max(xs), max(ys)

def pack(layers, pad=PAD):
    """layers: [(polys, fill)] -> {size}, paths. Encaja todo en el lienzo con margen."""
    allp = [p for polys, _ in layers for p in polys]
    minx, miny, maxx, maxy = bbox(allp)
    ox, oy = pad - minx, pad - miny
    w = int(math.ceil(maxx - minx + 2 * pad))
    h = int(math.ceil(maxy - miny + 2 * pad))
    paths = [{"d": d_of([xf(p, ox, oy) for p in polys]), "fill": fill} for polys, fill in layers]
    return {"size": [w, h]}, paths

CROWN_A, CROWN_B = "a_first", "b_first"

def wordmark_layers(theme):
    a, b = theme["logo_colors"]
    letters = kino_k() + kino_i_stem() + kino_tv()
    dot_r = 40.0
    tuft_a, tuft_b = wordmark_tuft(CROWN_A)
    return [
        (letters, "textPrimary"),                       # letras y TV, como el logo de Kino
        (kino_n(), "textPrimary"),
        (kino_o_ring(), "textPrimary"),                 # el aro de la "o" sigue blanco
        # el aro Potara en lugar del punto de la "i" (su propio trazo: el agujero va con
        # borde contrario, y así se ve hueco con non-zero y con even-odd)
        (annulus(I_DOT[0], I_DOT[1], 26, 15, 18), a),
        # color A: mitad derecha del punto de la "o", barra izquierda y su mechón
        ([half_disc(O_C[0], O_C[1], dot_r, "right")]
         + [rect(BAR_X0, BAR_Y0, BAR_SPLIT, BAR_Y1)]
         + tuft_a, a),
        # color B: mitad izquierda del punto de la "o", barra derecha y su mechón
        ([half_disc(O_C[0], O_C[1], dot_r, "left")]
         + [rect(BAR_SPLIT, BAR_Y0, BAR_X1, BAR_Y1)]
         + tuft_b, b),
    ]

def mark_layers(theme):
    a, b = theme["logo_colors"]
    tuft_a, tuft_b = mark_tuft(CROWN_A)
    return [
        (annulus(MARK_C[0], MARK_C[1], O_RADIUS + O_STROKE / 2, O_RADIUS - O_STROKE / 2, 20), "textPrimary"),
        ([half_disc(MARK_C[0], MARK_C[1], MARK_INNER_R, "right")] + tuft_a, a),
        ([half_disc(MARK_C[0], MARK_C[1], MARK_INNER_R, "left")] + tuft_b, b),
    ]

PREVIEW = {}
for t in THEMES:
    t["experience"] = "full"
    wsize, wpaths = pack(wordmark_layers(t))
    msize, mpaths = pack(mark_layers(t))
    t["logo"] = {"wordmark": {"size": wsize["size"], "paths": wpaths},
                 "mark": {"size": msize["size"], "paths": mpaths}}
    t.pop("logo_colors")   # clave de trabajo: Kino rechaza un campo desconocido
    PREVIEW[t["id"]] = (t["logo"]["wordmark"], t["logo"]["mark"])

MANIFEST = {
    "id": "fusion-warriors",
    "name": "Fusión Vegitto y Gogeta",
    "version": "2.0.0",
    "apiVersion": 18,
    "entry": "plugin.js",
    "description": "Tres temas de fusión para toda la app: Vegitto Azul, Gogeta Fuego y Fusión V+G. El logo de Kino con el pelo y los colores de cada personaje.",
    "author": "FastGamer",
    "homepage": "https://github.com/JuanDEVYT/Vegitto-y-gogeta-",
    "hosts": [],
    "capabilities": ["screen"],
    "categories": ["themes"],
    "color": "#35D6FF",
    "screen": {"label": "Fusión V+G", "labelEn": "V+G Fusion", "icon": "bolt", "menuOpens": "screen"},
    "appThemes": THEMES,
}

# ---------------------------------------------------------------- comprobaciones
def lin(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def lum(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)

def contrast(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)

KINO_ACCENT = "#E50914"

def check(t):
    problems, c = [], t["colors"]
    stops = t["background"]["colors"]
    worst = lambda col: min(contrast(col, s) for s in stops)
    for s in stops:
        if lum(s) > 0.05:
            problems.append(f"fondo {s} demasiado claro (L={lum(s):.3f} > 0.05)")
    if worst(c["accent"]) < 3.0:
        problems.append(f"accent sobre fondo {worst(c['accent']):.2f} < 3.0")
    if contrast(c["onAccent"], c["accent"]) < 4.5:
        problems.append(f"onAccent sobre accent {contrast(c['onAccent'], c['accent']):.2f} < 4.5")
    if worst(KINO_ACCENT) < 3.0:
        problems.append(f"acento de Kino sobre el fondo {worst(KINO_ACCENT):.2f} < 3.0")
    for k in ("textPrimary", "textSecondary"):
        if worst(c[k]) < 4.5:
            problems.append(f"{k} sobre fondo {worst(c[k]):.2f} < 4.5")
        if contrast(c[k], c["surface"]) < 4.5:
            problems.append(f"{k} sobre surface {contrast(c[k], c['surface']):.2f} < 4.5")
    if contrast(c["textPrimary"], c["surfaceHigh"]) < 4.5:
        problems.append(f"textPrimary sobre surfaceHigh {contrast(c['textPrimary'], c['surfaceHigh']):.2f} < 4.5")
    if worst(c["focus"]) < 3.0:
        problems.append(f"focus sobre fondo {worst(c['focus']):.2f} < 3.0")
    if contrast(c["onFocus"], c["focus"]) < 4.5:
        problems.append(f"onFocus sobre focus {contrast(c['onFocus'], c['focus']):.2f} < 4.5")
    return problems

def logo_checks(t):
    out = []
    for key in ("wordmark", "mark"):
        s = t["logo"][key]
        w, h = s["size"]
        assert 1 <= w <= 1000 and 1 <= h <= 1000, (t["id"], key, s["size"])
        assert w <= h * 8 and h <= w * 8, (t["id"], key, "aspecto")
        assert 1 <= len(s["paths"]) <= 8, (t["id"], key, "paths")
        for i, p in enumerate(s["paths"]):
            assert 1 <= len(p["d"]) <= 2000, (t["id"], key, i, len(p["d"]))
            assert all(ch in "MmLlHhVvCcSsQqTtAaZz0123456789eE.,+- " for ch in p["d"]), (t["id"], key, i)
        out.append(f"  {t['id']}.{key}: {w}x{h}, {len(s['paths'])} paths, "
                   f"máx {max(len(p['d']) for p in s['paths'])} chars")
    return out

def polys_of(d):
    return [[tuple(map(float, seg.split())) for seg in sub.replace("M", "").split("L") if seg.strip()]
            for sub in d.rstrip("Z").split("Z") if sub.strip()]

def preview():
    """Vista previa del logo SOLO: fondo transparente, sin ningún degradado."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    resolve = lambda t, f: t["colors"][f] if f in t["colors"] else f
    row_h, pad, w = 220, 26, 1000
    img = Image.new("RGBA", (w, row_h * len(THEMES)), (0, 0, 0, 0))

    def paint(shape, ox, oy, s, theme):
        for p in shape["paths"]:
            subs = polys_of(p["d"])
            mask = Image.new("L", img.size, 0)
            md = ImageDraw.Draw(mask)
            for j, poly in enumerate(subs):
                md.polygon([(x * s + ox, y * s + oy) for x, y in poly],
                           fill=0 if (j == 1 and len(subs) == 2) else 255)
            layer = Image.new("RGBA", img.size, resolve(theme, p["fill"]))
            img.paste(layer, (0, 0), mask)

    for i, t in enumerate(THEMES):
        wm, mk = PREVIEW[t["id"]]
        s = 165 / wm["size"][1]
        paint(wm, pad, i * row_h + (row_h - wm["size"][1] * s) / 2, s, t)
        ms = 145 / mk["size"][1]
        paint(mk, w - pad - mk["size"][0] * ms, i * row_h + (row_h - mk["size"][1] * ms) / 2, ms, t)
    out = os.path.join(ROOT, "preview-logos.png")
    img.save(out)
    return out

if __name__ == "__main__":
    bad = False
    print("Legibilidad (contract.json: fondo L<=0.05, texto 4.5:1, UI 3:1):")
    for t in THEMES:
        ps = check(t)
        c = t["colors"]
        stops = t["background"]["colors"]
        if ps:
            bad = True
            print(f"  {t['id']}: FALLA")
            for p in ps:
                print(f"    - {p}")
        else:
            print(f"  {t['id']}: OK  accent {min(contrast(c['accent'], s) for s in stops):.1f}:1 · "
                  f"onAccent {contrast(c['onAccent'], c['accent']):.1f}:1 · "
                  f"texto {min(min(contrast(c['textPrimary'], s), contrast(c['textSecondary'], s)) for s in stops):.1f}:1 · "
                  f"foco {min(contrast(c['focus'], s) for s in stops):.1f}:1")
    print("Logos vectoriales (KinoWordmark.kt + detalle del personaje):")
    for t in THEMES:
        for line in logo_checks(t):
            print(line)
    with open(os.path.join(ROOT, "kino-plugin.json"), "w", encoding="utf-8") as f:
        # Compacto: el manifiesto tiene un tope de 16 KB y los trazos vectoriales ocupan casi todo.
        json.dump(MANIFEST, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    size = os.path.getsize(os.path.join(ROOT, "kino-plugin.json"))
    print(f"kino-plugin.json: {size} bytes (máximo 16384) {'OK' if size <= 16384 else 'DEMASIADO GRANDE'}")
    p = preview()
    print("preview-logos.png (sin fondo):", p or "Pillow no instalado, se omite")
    sys.exit(1 if bad or size > 16384 else 0)
