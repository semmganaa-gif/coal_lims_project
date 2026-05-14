"""CSS declaration → Tailwind v4 utility class mapping (with `` prefix).

Each function returns a Tailwind class string, or None if unmappable.
Migration script consumes this; failures are reported for manual review.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Color mapping — exact hex match → Tailwind palette OR semantic token class
# ---------------------------------------------------------------------------
# Lab-domain semantic tokens are defined in src/styles.css @theme.
# Other colors snap to Tailwind's default palette by exact hex match.

HEX_TO_TOKEN: dict[str, str] = {
    # Семантик (custom @theme tokens)
    "#20c997": "pass",
    "#15803d": "pass-bold",
    "#f59e0b": "warn",
    "#fef3c7": "warn-soft",
    "#b45309": "warn-bold",
    "#ef4444": "fail",
    "#fee2e2": "fail-soft",
    "#3b82f6": "info-2",
    "#dbeafe": "info-2-soft",
    "#1d4ed8": "info-2-bold",
    "#8b5cf6": "accent",
    "#ede9fe": "accent-soft",
    "#6366f1": "accent-2",
    "#0d9488": "teal",
    "#059669": "success-emerald",
    "#dc2626": "fail-rose",
    "#0f172a": "brand-deep",
    "#1e40af": "brand-primary",
}

# Tailwind v4 default palette — exact hex match → palette class fragment
HEX_TO_PALETTE: dict[str, str] = {
    "#fff": "white",
    "#ffffff": "white",
    "#000": "black",
    "#000000": "black",
    # slate
    "#f8fafc": "slate-50",
    "#f1f5f9": "slate-100",
    "#e2e8f0": "slate-200",
    "#cbd5e0": "slate-300",  # close to slate-300 (#cbd5e1)
    "#cbd5e1": "slate-300",
    "#94a3b8": "slate-400",
    "#64748b": "slate-500",
    "#475569": "slate-600",
    "#334155": "slate-700",
    "#1e293b": "slate-800",
    # gray
    "#f9fafb": "gray-50",
    "#f3f4f6": "gray-100",
    "#e5e7eb": "gray-200",
    "#d1d5db": "gray-300",
    # neutral / zinc / stone (rare)
    # red
    "#fef2f2": "red-50",
    "#fee2e2": "red-100",
    # green
    "#ecfdf5": "emerald-50",
    "#d1fae5": "emerald-100",
    "#a7f3d0": "emerald-200",
    "#10b981": "emerald-500",
    "#16a34a": "green-600",
    # blue
    "#eff6ff": "blue-50",
    "#dbeafe": "blue-100",
    "#bfdbfe": "blue-200",
    "#2563eb": "blue-600",
    # amber
    "#fffbeb": "amber-50",
    "#fef3c7": "amber-100",
    "#fde68a": "amber-200",
    # rose
    "#fff1f2": "rose-50",
    # f7fafc — close to slate-50
    "#f7fafc": "slate-50",
    # f0fdf4 — close to emerald-50
    "#f0fdf4": "emerald-50",
}


def hex_to_class(hex_value: str, kind: str) -> str | None:
    """kind = 'text' | 'bg' | 'border'"""
    h = hex_value.lower().strip()
    if h in HEX_TO_TOKEN:
        return f"{kind}-{HEX_TO_TOKEN[h]}"
    if h in HEX_TO_PALETTE:
        return f"{kind}-{HEX_TO_PALETTE[h]}"
    return f"{kind}-[{h}]"  # arbitrary value fallback


# ---------------------------------------------------------------------------
# Width / Height — % and px
# ---------------------------------------------------------------------------

WIDTH_PERCENT_TO_FRACTION: dict[str, str] = {
    "100%": "full",
    "50%": "1/2",
    "33%": "1/3",
    "33.33%": "1/3",
    "66%": "2/3",
    "66.67%": "2/3",
    "25%": "1/4",
    "75%": "3/4",
    "20%": "1/5",
    "40%": "2/5",
    "60%": "3/5",
    "80%": "4/5",
    "16.67%": "1/6",
    "83.33%": "5/6",
}


def width_class(value: str, axis: str) -> str | None:
    """axis = 'w' | 'h' | 'min-w' | 'min-h' | 'max-w' | 'max-h'"""
    v = value.strip().lower()
    if v == "0":
        return f"{axis}-0"
    if v in ("auto",):
        return f"{axis}-auto"
    # %  → fraction (where defined) else arbitrary
    if v.endswith("%"):
        if v in WIDTH_PERCENT_TO_FRACTION:
            return f"{axis}-{WIDTH_PERCENT_TO_FRACTION[v]}"
        return f"{axis}-[{v}]"
    # px
    if v.endswith("px"):
        return f"{axis}-[{v}]"
    # rem / em / vh / vw / calc()
    if v.endswith(("rem", "em", "vh", "vw")) or v.startswith("calc("):
        # arbitrary value — escape parens for calc()
        return f"{axis}-[{v.replace(' ', '_')}]"
    return None


# ---------------------------------------------------------------------------
# Font size — snap to defined @theme tokens or arbitrary
# ---------------------------------------------------------------------------

FONT_SIZE_TO_CLASS: dict[str, str] = {
    "0.6rem": "3xs",
    "0.65rem": "2xs",
    "0.68rem": "xs-1",
    "0.7rem": "xs-2",
    "0.72rem": "xs-3",
    "0.75rem": "xs",          # Tailwind default
    "0.8rem": "sm-1",
    "0.82rem": "sm-2",
    "0.85rem": "sm-3",
    "0.875rem": "sm",         # Tailwind default
    "1rem": "base",            # Tailwind default
    "1.1rem": "[1.1rem]",
    "1.125rem": "lg",          # Tailwind default
    "1.2rem": "[1.2rem]",
    "1.25rem": "xl",           # Tailwind default
    "1.3rem": "[1.3rem]",
    "1.5rem": "2xl",           # Tailwind default
    "1.875rem": "3xl",
    "2rem": "[2rem]",
}


def font_size_class(value: str) -> str | None:
    v = value.strip().lower()
    if v in FONT_SIZE_TO_CLASS:
        token = FONT_SIZE_TO_CLASS[v]
        return f"text-{token}"
    if v.endswith(("rem", "em", "px", "pt", "%")):
        return f"text-[{v}]"
    return None


# ---------------------------------------------------------------------------
# Font weight
# ---------------------------------------------------------------------------

FONT_WEIGHT: dict[str, str] = {
    "300": "light",
    "400": "normal",
    "500": "medium",
    "600": "semibold",
    "700": "bold",
    "800": "extrabold",
    "900": "black",
    "normal": "normal",
    "bold": "bold",
}


def font_weight_class(value: str) -> str | None:
    v = value.strip().lower()
    if v in FONT_WEIGHT:
        return f"font-{FONT_WEIGHT[v]}"
    return None


# ---------------------------------------------------------------------------
# Border radius
# ---------------------------------------------------------------------------

RADIUS_TO_CLASS: dict[str, str] = {
    "0": "none",
    "2px": "sm",
    "4px": "md",
    "6px": "lg",
    "8px": "lg",          # close to default lg (0.5rem = 8px)
    "10px": "[10px]",
    "12px": "xl",         # default xl
    "16px": "2xl",
    "24px": "3xl",
    "9999px": "full",
    "50%": "full",
}


def border_radius_class(value: str) -> str | None:
    v = value.strip().lower()
    if v in RADIUS_TO_CLASS:
        return f"rounded-{RADIUS_TO_CLASS[v]}"
    if v.endswith(("px", "rem", "em", "%")):
        return f"rounded-[{v}]"
    return None


# ---------------------------------------------------------------------------
# Spacing (padding, margin, gap) — snap to default scale or arbitrary
# ---------------------------------------------------------------------------

# Bootstrap-тай spacing scale зөрчилдөнө (BS m-3=1rem vs TW m-3=0.75rem) — тиймээс
# bare scale-ийг ердөө 0 ба auto тохиолдолд л ашиглана. Бусад px/rem утгууд
# arbitrary-аар emit хийгдэнэ (m-[12px]) — collision-гүй, нарийн утга.
SAFE_SPACING_SCALE: dict[str, str] = {
    "0": "0",
    "auto": "auto",
}


def spacing_class(prefix: str, value: str) -> str | None:
    v = value.strip().lower()
    if v in SAFE_SPACING_SCALE:
        return f"{prefix}-{SAFE_SPACING_SCALE[v]}"
    if v.endswith(("px", "rem", "em", "%")):
        return f"{prefix}-[{v}]"
    return None


def _spacing_atom(value: str) -> str | None:
    """Convert single spacing token (px/rem/0/auto) to its scale token.
    Bootstrap collision үгүй болгохын тулд бараг бүх утгыг arbitrary-аар буцаана.
    """
    v = value.strip().lower()
    if v in SAFE_SPACING_SCALE:
        return SAFE_SPACING_SCALE[v]
    if v in ("auto", "-auto"):
        return "auto"
    if v.endswith(("px", "rem", "em", "%")):
        return f"[{v}]"
    return None


def spacing_shorthand(prefix: str, value: str) -> str | None:
    """Handle margin/padding multi-value shorthand:
        - 1 value: all sides
        - 2 values: y, x
        - 4 values: top, right, bottom, left
    Returns space-separated multiple classes.
    """
    parts = value.split()
    atoms = [_spacing_atom(p) for p in parts]
    if any(a is None for a in atoms):
        return None
    side_map = {"p": ("p", "pt", "pr", "pb", "pl", "px", "py"),
                "m": ("m", "mt", "mr", "mb", "ml", "mx", "my")}
    p, pt, pr, pb, pl, px, py = side_map[prefix]
    if len(atoms) == 1:
        return f"{p}-{atoms[0]}"
    if len(atoms) == 2:
        # vertical, horizontal
        cls = []
        if atoms[0] != "0" or len(parts) == 2:
            cls.append(f"{py}-{atoms[0]}")
        cls.append(f"{px}-{atoms[1]}")
        return " ".join(cls)
    if len(atoms) == 4:
        # top right bottom left → emit per-side, dropping zero unless meaningful
        cls = [
            f"{pt}-{atoms[0]}",
            f"{pr}-{atoms[1]}",
            f"{pb}-{atoms[2]}",
            f"{pl}-{atoms[3]}",
        ]
        # filter out XX-0 to keep output tidy when adjacent zeros are default
        return " ".join(c for c in cls if not c.endswith("-0"))
    if len(atoms) == 3:
        # top, horizontal, bottom
        cls = [
            f"{pt}-{atoms[0]}",
            f"{px}-{atoms[1]}",
            f"{pb}-{atoms[2]}",
        ]
        return " ".join(c for c in cls if not c.endswith("-0"))
    return None


# ---------------------------------------------------------------------------
# Linear gradient — predefined palette mapped to custom @utility classes
# ---------------------------------------------------------------------------
# These gradients appear in inline styles and are added as @utility blocks
# in src/styles.css with matching class names. Migration replaces inline
# gradient with the corresponding utility class.

GRADIENT_TO_UTILITY: dict[str, str] = {
    # Brand
    "linear-gradient(135deg,#0f172a,#1e40af)": "bg-brand-gradient",
    "linear-gradient(135deg, #0f172a, #1e40af)": "bg-brand-gradient",
    "linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)": "bg-brand-deep-gradient",
    # Soft pastels (status backdrops)
    "linear-gradient(135deg,#d1fae5,#bbf7d0)": "bg-pass-gradient",
    "linear-gradient(135deg,#fef3c7,#fffbeb)": "bg-warn-gradient",
    "linear-gradient(135deg,#dbeafe,#bfdbfe)": "bg-info-gradient",
    "linear-gradient(135deg,#6366f1,#8b5cf6)": "bg-accent-gradient",
    "linear-gradient(135deg, #ef4444, #dc2626)": "bg-fail-gradient",
    "linear-gradient(135deg, #f1f5f9, #e2e8f0)": "bg-slate-gradient",
    "linear-gradient(135deg, #6366f1, #4f46e5)": "bg-indigo-gradient",
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)": "bg-purple-gradient",
    "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)": "bg-amber-gradient",
    "linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%)": "bg-sky-gradient",
}


# ---------------------------------------------------------------------------
# rgba support
# ---------------------------------------------------------------------------

RGBA_RE = re.compile(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$")


def rgba_class(value: str, kind: str) -> str | None:
    """rgba(255,255,255,0.6) → bg-white/60"""
    m = RGBA_RE.match(value.strip().lower().replace(" ", ""))
    if not m:
        return None
    r, g, b, a = m.group(1), m.group(2), m.group(3), m.group(4)
    rgb = (int(r), int(g), int(b))
    base_color = {
        (255, 255, 255): "white",
        (0, 0, 0): "black",
    }.get(rgb)
    if base_color is None:
        # arbitrary
        return f"{kind}-[rgba({r},{g},{b},{a or '1'})]"
    if a is None:
        return f"{kind}-{base_color}"
    alpha_pct = int(round(float(a) * 100))
    return f"{kind}-{base_color}/{alpha_pct}"


# ---------------------------------------------------------------------------
# Border side shorthand
# ---------------------------------------------------------------------------

BORDER_SHORTHAND_RE = re.compile(r"^(\d+)px\s+solid\s+(#[0-9a-f]{3,8})$")


def border_side_class(side: str, value: str) -> str | None:
    """Handle `border-bottom: 1px solid #fde68a` → `border-b border-amber-200`."""
    m = BORDER_SHORTHAND_RE.match(value.strip().lower())
    if not m:
        return None
    width_px = m.group(1)
    color_hex = m.group(2)
    side_token = {"top": "t", "bottom": "b", "left": "l", "right": "r"}[side]
    color_cls = hex_to_class(color_hex, "border")
    width_cls = f"border-{side_token}" if width_px == "1" else f"border-{side_token}-{width_px}"
    return f"{width_cls} {color_cls}"


# ---------------------------------------------------------------------------
# Named colors (CSS keywords)
# ---------------------------------------------------------------------------

NAMED_COLOR_TO_HEX: dict[str, str] = {
    "white": "#ffffff",
    "black": "#000000",
    "red": "#ef4444",
    "blue": "#3b82f6",
    "green": "#10b981",
    "yellow": "#facc15",
    "orange": "#f97316",
    "purple": "#a855f7",
    "transparent": "transparent",
}


# ---------------------------------------------------------------------------
# Master mapper — dispatches by property
# ---------------------------------------------------------------------------

def map_declaration(prop: str, value: str) -> str | None:
    p = prop.lower().strip()
    v = value.strip()
    vl = v.lower()

    # Strip "!important" — Tailwind utilities aren't !important by default,
    # but for inline migration, attach `!` prefix to force importance.
    important = False
    if vl.endswith("!important"):
        vl = vl[:-len("!important")].strip()
        v = v[: v.lower().rfind("!important")].strip()
        important = True

    def _ret(cls: str | None) -> str | None:
        if cls is None or not important:
            return cls
        return " ".join(f"{c}!" if not c.endswith("!") else c for c in cls.split())

    # Display
    if p == "display":
        return {
            "none": "hidden",
            "block": "block",
            "inline": "inline",
            "inline-block": "inline-block",
            "flex": "flex",
            "inline-flex": "inline-flex",
            "grid": "grid",
            "table": "table",
            "table-cell": "table-cell",
            "table-row": "table-row",
        }.get(vl)

    # Flex shorthand
    if p == "flex":
        if vl == "1":
            return _ret("flex-1")
        if vl == "auto":
            return _ret("flex-auto")
        if vl == "none":
            return _ret("flex-none")
        # `0 0 100px` shorthand → shrink-0 grow-0 basis-[100px]
        m = re.match(r"^(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(.+)$", vl)
        if m:
            grow, shrink, basis = m.group(1), m.group(2), m.group(3).strip()
            cls = []
            cls.append("grow" if grow == "1" else f"grow-{grow}" if grow != "0" else "grow-0")
            cls.append("shrink" if shrink == "1" else f"shrink-{shrink}" if shrink != "0" else "shrink-0")
            if basis.endswith(("px", "rem", "em", "%")):
                cls.append(f"basis-[{basis}]")
            elif basis == "auto":
                cls.append("basis-auto")
            else:
                return None
            return _ret(" ".join(cls))
        # numeric grow value → arbitrary
        if re.match(r"^\d+(\.\d+)?$", vl):
            return _ret(f"grow-[{vl}]")
        return None
    if p == "flex-shrink":
        if vl in ("0", "1"):
            return _ret(f"shrink-{vl}")
        return _ret(f"shrink-[{vl}]")
    if p == "flex-grow":
        if vl in ("0", "1"):
            return _ret(f"grow-{vl}")
        return _ret(f"grow-[{vl}]")
    if p == "flex-basis":
        if vl == "auto":
            return _ret("basis-auto")
        if vl.endswith(("px", "rem", "em", "%")):
            return _ret(f"basis-[{vl}]")
        return None

    if p == "flex-direction":
        return {
            "row": "flex-row",
            "row-reverse": "flex-row-reverse",
            "column": "flex-col",
            "column-reverse": "flex-col-reverse",
        }.get(vl)

    if p == "flex-wrap":
        return {"wrap": "flex-wrap", "nowrap": "flex-nowrap"}.get(vl)

    if p == "justify-content":
        return {
            "flex-start": "justify-start",
            "flex-end": "justify-end",
            "center": "justify-center",
            "space-between": "justify-between",
            "space-around": "justify-around",
            "space-evenly": "justify-evenly",
        }.get(vl)

    if p == "align-items":
        return {
            "flex-start": "items-start",
            "flex-end": "items-end",
            "center": "items-center",
            "baseline": "items-baseline",
            "stretch": "items-stretch",
        }.get(vl)

    if p == "gap":
        return spacing_class("gap", v)

    # Sizing
    if p == "width":
        return width_class(v, "w")
    if p == "height":
        return width_class(v, "h")
    if p == "min-width":
        return width_class(v, "min-w")
    if p == "min-height":
        return width_class(v, "min-h")
    if p == "max-width":
        return width_class(v, "max-w")
    if p == "max-height":
        return width_class(v, "max-h")

    # Spacing — shorthand first (multi-value)
    if p == "padding":
        if len(v.split()) > 1:
            return _ret(spacing_shorthand("p", v))
        return _ret(spacing_class("p", v))
    if p == "margin":
        if len(v.split()) > 1:
            return _ret(spacing_shorthand("m", v))
        return _ret(spacing_class("m", v))
    if p == "padding-top":
        return _ret(spacing_class("pt", v))
    if p == "padding-right":
        return _ret(spacing_class("pr", v))
    if p == "padding-bottom":
        return _ret(spacing_class("pb", v))
    if p == "padding-left":
        return _ret(spacing_class("pl", v))
    if p == "margin-top":
        return _ret(spacing_class("mt", v))
    if p == "margin-right":
        return _ret(spacing_class("mr", v))
    if p == "margin-bottom":
        return _ret(spacing_class("mb", v))
    if p == "margin-left":
        return _ret(spacing_class("ml", v))

    # Color
    if p == "color":
        if vl.startswith("#"):
            return _ret(hex_to_class(vl, "text"))
        if vl in NAMED_COLOR_TO_HEX:
            if vl == "transparent":
                return _ret("text-transparent")
            return _ret(hex_to_class(NAMED_COLOR_TO_HEX[vl], "text"))
        if vl.startswith("rgba(") or vl.startswith("rgb("):
            return _ret(rgba_class(vl, "text"))
        if vl.startswith("var("):
            # CSS variable — preserve via arbitrary value
            return _ret(f"text-[{v}]")
        return None
    if p in ("background", "background-color"):
        if vl == "none":
            return _ret("bg-none")
        if vl.startswith("linear-gradient") or vl.startswith("radial-gradient"):
            grad = GRADIENT_TO_UTILITY.get(vl)
            if grad:
                return _ret(grad)
            # Fallback: arbitrary value, with whitespace stripped (Tailwind v4 syntax)
            arbitrary = re.sub(r"\s+", "", vl)
            return _ret(f"bg-[{arbitrary}]")
        if vl.startswith("#"):
            hex_only = re.match(r"#[0-9a-f]{3,8}", vl)
            if hex_only:
                return _ret(hex_to_class(hex_only.group(0), "bg"))
        if vl in NAMED_COLOR_TO_HEX:
            if vl == "transparent":
                return _ret("bg-transparent")
            return _ret(hex_to_class(NAMED_COLOR_TO_HEX[vl], "bg"))
        if vl.startswith("rgba(") or vl.startswith("rgb("):
            return _ret(rgba_class(vl, "bg"))
        if vl.startswith("var("):
            return _ret(f"bg-[{v}]")
        return None
    if p in ("border-color",):
        if vl.startswith("#"):
            return _ret(hex_to_class(vl, "border"))
        if vl in NAMED_COLOR_TO_HEX and vl != "transparent":
            return _ret(hex_to_class(NAMED_COLOR_TO_HEX[vl], "border"))
        return None

    # Typography
    if p == "font-size":
        return font_size_class(v)
    if p == "font-weight":
        return font_weight_class(v)
    if p == "text-align":
        return {
            "left": "text-left",
            "center": "text-center",
            "right": "text-right",
            "justify": "text-justify",
        }.get(vl)
    if p == "white-space":
        return {
            "normal": "whitespace-normal",
            "nowrap": "whitespace-nowrap",
            "pre": "whitespace-pre",
            "pre-wrap": "whitespace-pre-wrap",
            "pre-line": "whitespace-pre-line",
        }.get(vl)
    if p == "line-height":
        if vl.endswith(("rem", "em", "px")):
            return f"leading-[{vl}]"
        if re.match(r"^\d+(\.\d+)?$", vl):
            return f"leading-[{vl}]"
        return None
    if p == "letter-spacing":
        return f"tracking-[{vl}]" if vl.endswith(("em", "px", "rem")) else None
    if p == "text-transform":
        return {
            "uppercase": "uppercase",
            "lowercase": "lowercase",
            "capitalize": "capitalize",
            "none": "normal-case",
        }.get(vl)
    if p == "text-decoration":
        if vl == "none":
            return "no-underline"
        if vl == "underline":
            return "underline"
        return None

    # Border
    if p == "border":
        if vl == "none":
            return _ret("border-0")
        m = re.match(r"^(\d+)px\s+solid\s+(#[0-9a-f]{3,8})$", vl)
        if m:
            width_px = m.group(1)
            color = m.group(2)
            color_cls = hex_to_class(color, "border")
            base = "border" if width_px == "1" else f"border-{width_px}"
            return _ret(f"{base} {color_cls}")
        # rgba/rgb border — `1px solid rgba(...)`
        m = re.match(r"^(\d+)px\s+solid\s+(rgba?\([^)]+\))$", vl)
        if m:
            width_px = m.group(1)
            rgba_color = m.group(2)
            cls = rgba_class(rgba_color, "border")
            if cls:
                base = "border" if width_px == "1" else f"border-{width_px}"
                return _ret(f"{base} {cls}")
        return None
    if p in ("border-top", "border-right", "border-bottom", "border-left"):
        side = p.split("-")[1]
        return _ret(border_side_class(side, v))
    if p == "border-radius":
        return _ret(border_radius_class(v))
    if p == "border-width":
        if vl.endswith("px"):
            n = vl[:-2]
            return _ret(f"border-{n}" if n in ("0", "1", "2", "4", "8") else f"border-[{vl}]")
        return None
    if p == "border-style":
        return {
            "solid": "border-solid",
            "dashed": "border-dashed",
            "dotted": "border-dotted",
            "none": "border-none",
        }.get(vl)

    # Layout / overflow / position
    if p == "overflow":
        return {
            "hidden": "overflow-hidden",
            "auto": "overflow-auto",
            "scroll": "overflow-scroll",
            "visible": "overflow-visible",
        }.get(vl)
    if p == "overflow-x":
        return {
            "hidden": "overflow-x-hidden",
            "auto": "overflow-x-auto",
            "scroll": "overflow-x-scroll",
            "visible": "overflow-x-visible",
        }.get(vl)
    if p == "overflow-y":
        return {
            "hidden": "overflow-y-hidden",
            "auto": "overflow-y-auto",
            "scroll": "overflow-y-scroll",
            "visible": "overflow-y-visible",
        }.get(vl)

    if p == "position":
        return {
            "relative": "relative",
            "absolute": "absolute",
            "fixed": "fixed",
            "sticky": "sticky",
            "static": "static",
        }.get(vl)

    # Cursor
    if p == "cursor":
        return {
            "pointer": "cursor-pointer",
            "default": "cursor-default",
            "not-allowed": "cursor-not-allowed",
            "wait": "cursor-wait",
            "move": "cursor-move",
            "text": "cursor-text",
        }.get(vl)

    # z-index
    if p == "z-index":
        try:
            n = int(vl)
            if n in (0, 10, 20, 30, 40, 50):
                return f"z-{n}"
            return f"z-[{n}]"
        except ValueError:
            return None

    # Opacity
    if p == "opacity":
        try:
            f = float(vl)
            return f"opacity-[{f}]" if f != int(f) else f"opacity-{int(f * 100)}"
        except ValueError:
            return None

    # Float
    if p == "float":
        return {
            "left": "float-left",
            "right": "float-right",
            "none": "float-none",
        }.get(vl)
    if p == "clear":
        return {
            "left": "clear-left",
            "right": "clear-right",
            "both": "clear-both",
            "none": "clear-none",
        }.get(vl)

    # Font style
    if p == "font-style":
        return {"italic": "italic", "normal": "not-italic"}.get(vl)

    # Object fit
    if p == "object-fit":
        return {
            "contain": "object-contain",
            "cover": "object-cover",
            "fill": "object-fill",
            "none": "object-none",
            "scale-down": "object-scale-down",
        }.get(vl)

    # Position offsets
    if p in ("top", "right", "bottom", "left", "inset"):
        atom = _spacing_atom(v)
        if atom:
            return _ret(f"{p}-{atom}")
        # Negative values like -80px
        if v.startswith("-") and v[1:].endswith(("px", "rem", "em", "%")):
            return _ret(f"-{p}-[{v[1:]}]")
        return None

    # Box shadow / text-shadow — Tailwind v4-д text-shadow утилит хараахан байхгүй;
    # arbitrary property syntax-аар хадгална.
    if p == "box-shadow":
        if vl == "none":
            return _ret("shadow-none")
        return _ret(f"[box-shadow:{v.replace(' ', '_')}]")
    if p == "text-shadow":
        if vl == "none":
            return _ret("[text-shadow:none]")
        return _ret(f"[text-shadow:{v.replace(' ', '_')}]")

    # Pointer events / user-select
    if p == "pointer-events":
        return {"none": "pointer-events-none", "auto": "pointer-events-auto"}.get(vl)
    if p == "user-select":
        return {
            "none": "select-none",
            "text": "select-text",
            "all": "select-all",
            "auto": "select-auto",
        }.get(vl)

    # Visibility
    if p == "visibility":
        return {"visible": "visible", "hidden": "invisible"}.get(vl)

    # Animation-delay → delay-[Xms]
    if p == "animation-delay":
        if vl.endswith("s") and not vl.endswith("ms"):
            try:
                ms = int(float(vl[:-1]) * 1000)
                return _ret(f"[animation-delay:{ms}ms]")
            except ValueError:
                pass
        return _ret(f"[animation-delay:{vl}]")

    # CSS variable assignments (e.g. --ag-header-background-color: #xxx)
    # These set CSS vars for child components — keep as inline-arbitrary class.
    if p.startswith("--"):
        return _ret(f"[{p}:{v}]")

    # Border-side radius
    if p == "border-top-left-radius":
        if vl == "0":
            return _ret("rounded-tl-none")
        return _ret(f"rounded-tl-[{vl}]")
    if p == "border-top-right-radius":
        if vl == "0":
            return _ret("rounded-tr-none")
        return _ret(f"rounded-tr-[{vl}]")
    if p == "border-bottom-left-radius":
        if vl == "0":
            return _ret("rounded-bl-none")
        return _ret(f"rounded-bl-[{vl}]")
    if p == "border-bottom-right-radius":
        if vl == "0":
            return _ret("rounded-br-none")
        return _ret(f"rounded-br-[{vl}]")

    # Font-family — typically not a utility candidate; map common stacks.
    if p == "font-family":
        if vl == "inherit":
            return _ret("font-[inherit]")
        # Custom font stack — arbitrary class
        return _ret(f"font-[{v.replace(' ', '_').replace(',', ',')}]")

    # Border-color rgba support
    # (handled by border-color above for hex; rgba added here)
    # — already returned None from border-color path; let it fall through

    # Transitions / Transforms — leave for manual review
    return None
