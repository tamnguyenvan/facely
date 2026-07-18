# FRONTEND.md — Facely UI/UX Design System

> Covers: Design Language · Layout · Tkinter Components · Theme Tokens · UI State Machine

---

## 1. Design Language

### Aesthetic Direction

**Industrial Precision** — the UI evokes a professional security/surveillance workstation.
Not sci-fi. Not consumer. Clean, dense, information-first.

| Attribute | Decision |
|---|---|
| **Mood** | Operator terminal — calm authority |
| **Density** | High-information, no wasted space |
| **Motion** | Minimal: status transitions, confidence bar fill only |
| **Typography** | `Consolas` / `Courier New` for data values; `Segoe UI` for labels |
| **Color** | Charcoal base, cool grey surfaces, electric cyan accent |

---

## 2. Color Design Tokens

```python
# app/ui/theme.py

COLORS = {
    # ── Backgrounds
    "bg_root":      "#0D0F11",   # deepest background
    "bg_panel":     "#141618",   # panel surfaces
    "bg_card":      "#1C1F23",   # card / list item
    "bg_elevated":  "#23272C",   # dropdowns, tooltips

    # ── Borders
    "border":       "#2A2F36",   # default border
    "border_focus": "#00B4D8",   # focused input border

    # ── Text
    "text_primary":   "#E8EDF2",
    "text_secondary": "#7A8899",
    "text_muted":     "#4A5568",
    "text_accent":    "#00B4D8",   # cyan accent

    # ── Status
    "success":      "#2DD4BF",   # recognized match
    "warning":      "#F59E0B",   # low confidence
    "danger":       "#EF4444",   # unknown / error
    "info":         "#60A5FA",   # informational

    # ── Interactive
    "btn_primary":      "#00B4D8",
    "btn_primary_hover":"#0096B5",
    "btn_danger":       "#DC2626",
    "btn_danger_hover": "#B91C1C",
    "btn_surface":      "#23272C",
    "btn_surface_hover":"#2D3340",

    # ── Camera overlay
    "bbox_match":   "#2DD4BF",   # teal — recognized
    "bbox_unknown": "#EF4444",   # red — unknown
    "label_bg":     "#00000099", # translucent black
}

FONTS = {
    "display":    ("Segoe UI Semibold", 13),
    "label":      ("Segoe UI", 11),
    "small":      ("Segoe UI", 9),
    "mono":       ("Consolas", 11),
    "mono_large": ("Consolas", 14),
    "status":     ("Consolas", 10),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 20,
    "xl": 32,
}
```

---

## 3. Main Window Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ● Facely  v1.0.0          [ArcFace ▼]  [● ONLINE]   [✕]       │  ← TitleBar (custom, draggable)
├───────────────────────────────────────────┬──────────────────────────┤
│                                           │  IDENTITY PANEL          │
│         CAMERA CANVAS                     │  ┌────────────────────┐  │
│         1280 × 720                        │  │  Register Face      │  │
│                                           │  │  Name: [          ] │  │
│   ┌───────────────────────────────────┐   │  │  ID:   [          ] │  │
│   │  [Live Camera Feed]               │   │  │  [● Capture]        │  │
│   │                                   │   │  └────────────────────┘  │
│   │     ┌──────────┐                  │   │  ─────────────────────   │
│   │     │ Alice    │  ████████░░ 0.87 │   │  KNOWN IDENTITIES        │
│   │     └──────────┘                  │   │  ┌────────────────────┐  │
│   │                                   │   │  │ Alice     A1F3B2   │  │
│   └───────────────────────────────────┘   │  │ Bob       B2E9C4   │  │
│                                           │  │ ...                 │  │
├───────────────────────────────────────────┤  └────────────────────┘  │
│  CONTROL BAR                              │  [🗑 Delete Selected]    │
│  [▶ Start Camera]  [⏹ Stop]  Model:[▼]  FPS: 28  Latency: 19ms     │
└───────────────────────────────────────────┴──────────────────────────┘
```

**Window size:** 1380 × 820 px (non-resizable by default; resizable optional)
**Layout engine:** `grid` with three rows:

```
Row 0  →  TitleBar         (height: 36px, sticky EW)
Row 1  →  MainArea         (weight: 1, stretches vertically)
  Col 0 → CameraPanel      (weight: 3)
  Col 1 → IdentityPanel    (weight: 1, fixed 340px)
Row 2  →  StatusBar        (height: 36px, sticky EW)
```

---

## 4. Component Breakdown

### 4.1 `AppWindow` — Root Container

```python
# app/ui/app_window.py
"""
- Overrides default Tkinter title bar with custom dark title bar
- Sets wm_overrideredirect(True) + custom drag logic
- Wires all child panels to services
- Starts UI polling loop (root.after(30, _poll))
"""
```

Key responsibilities:
- Instantiate all services and panels, inject dependencies
- `root.after(30, self._poll)` — pull results from `result_queue` at 33 FPS
- Apply `ttk.Style` from `theme.py` before any widget creation

---

### 4.2 `CameraPanel` — Live Feed Canvas

```python
# app/ui/camera_panel.py
"""
Uses: tkinter.Canvas
Frame pipeline:
  1. Receive BGR frame from RecognitionService result
  2. Convert BGR → RGB → PIL.Image → ImageTk.PhotoImage
  3. canvas.create_image(0, 0, anchor=NW, image=photo)
  4. Draw overlays via Overlay renderer
"""
```

**Performance note:** `PhotoImage` is kept as instance variable to prevent GC.

---

### 4.3 `Overlay` — Bounding Box Renderer

```python
# app/ui/overlay.py

def draw_face_result(canvas, result: dict) -> None:
    """
    result: { bbox, name, score }

    Drawing order:
    1. Rounded rectangle (bbox) — teal if match, red if unknown
    2. Semi-transparent label background
    3. Name text (white, Consolas 11)
    4. Confidence bar (filled proportional to score, color-coded)
    5. Score text (e.g. "0.87")
    """
```

**Confidence bar color mapping:**

| Score | Color |
|---|---|
| ≥ 0.80 | `#2DD4BF` (teal — high confidence) |
| 0.55–0.79 | `#F59E0B` (amber — acceptable) |
| < 0.55 | `#EF4444` (red — unknown) |

---

### 4.4 `ControlPanel` — Bottom Status Bar

```python
# app/ui/control_panel.py
"""
Widgets:
  - [▶ Start Camera] / [⏹ Stop] toggle button
  - Model selector: ttk.Combobox with options ["ArcFace", "SFace", "DeepFace"]
  - FPS counter label (updates every 60 frames)
  - Latency label (ms, updates per frame)
  - Status dot (● green=running, ● red=stopped, ● amber=switching)
"""
```

**Model switch flow:**
1. Combobox `<<ComboboxSelected>>`
2. Show amber status dot + "Switching model…" text
3. Call `recognition_service.set_model()` in a background thread
4. On completion callback → restore green dot

---

### 4.5 `IdentityPanel` — Right Sidebar

```python
# app/ui/identity_panel.py
"""
Sections:
  1. Registration Form
       - Name entry (validated: non-empty, max 64 chars)
       - Person ID entry (optional; auto-generated if blank)
       - [● Capture] button → triggers 5-frame capture sequence

  2. Capture Progress (hidden until capture starts)
       - ttk.Progressbar, value 0-5 during capture
       - "Capturing… 3/5" label

  3. Known Identities List
       - ttk.Treeview, columns: Name | ID | Registered
       - Alternating row colors for readability
       - Scrollbar on right

  4. Action buttons
       - [🗑 Delete Selected] — confirmation dialog before delete
"""
```

---

### 4.6 `TitleBar` — Custom Window Chrome

```python
# app/ui/app_window.py  (inner class or section)
"""
- Frame height: 36px, bg_root color
- Left: app icon (16×16) + "Facely" text
- Center: model name badge (updates on model switch)
- Right: minimize [─], close [✕] buttons
- Draggable: bind <ButtonPress-1> + <B1-Motion> to move wm_geometry
"""
```

---

## 5. ttk Style Configuration

```python
# app/ui/theme.py  (continued)

def apply_theme(root) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")   # best base for dark theming

    # ── Frame / LabelFrame
    style.configure("TFrame",      background=COLORS["bg_panel"])
    style.configure("Card.TFrame", background=COLORS["bg_card"],
                    relief="flat", borderwidth=1)

    # ── Labels
    style.configure("TLabel",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["label"])
    style.configure("Muted.TLabel",
                    foreground=COLORS["text_muted"])
    style.configure("Accent.TLabel",
                    foreground=COLORS["text_accent"],
                    font=FONTS["mono"])

    # ── Buttons
    style.configure("Primary.TButton",
                    background=COLORS["btn_primary"],
                    foreground="#000000",
                    font=FONTS["display"],
                    padding=(12, 6))
    style.map("Primary.TButton",
              background=[("active", COLORS["btn_primary_hover"])])

    style.configure("Danger.TButton",
                    background=COLORS["btn_danger"],
                    foreground="#FFFFFF",
                    font=FONTS["label"],
                    padding=(10, 5))

    style.configure("Surface.TButton",
                    background=COLORS["btn_surface"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["label"],
                    padding=(10, 5))

    # ── Entry
    style.configure("TEntry",
                    fieldbackground=COLORS["bg_elevated"],
                    foreground=COLORS["text_primary"],
                    insertcolor=COLORS["text_accent"],
                    bordercolor=COLORS["border"],
                    font=FONTS["mono"])

    # ── Combobox
    style.configure("TCombobox",
                    fieldbackground=COLORS["bg_elevated"],
                    foreground=COLORS["text_primary"],
                    selectbackground=COLORS["bg_elevated"],
                    font=FONTS["mono"])

    # ── Treeview
    style.configure("Treeview",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_primary"],
                    fieldbackground=COLORS["bg_card"],
                    rowheight=28,
                    font=FONTS["label"])
    style.configure("Treeview.Heading",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["text_secondary"],
                    font=FONTS["small"])
    style.map("Treeview",
              background=[("selected", COLORS["bg_elevated"])],
              foreground=[("selected", COLORS["text_accent"])])

    # ── Progressbar
    style.configure("Horizontal.TProgressbar",
                    troughcolor=COLORS["bg_elevated"],
                    background=COLORS["success"],
                    thickness=4)

    # ── Scrollbar
    style.configure("Vertical.TScrollbar",
                    background=COLORS["bg_elevated"],
                    troughcolor=COLORS["bg_panel"],
                    arrowcolor=COLORS["text_muted"],
                    width=8)

    # ── Root window background
    root.configure(bg=COLORS["bg_root"])
```

---

## 6. UI State Machine

```
                    ┌──────────┐
                    │  IDLE    │  (app start, no camera)
                    └────┬─────┘
                         │ [▶ Start Camera]
                    ┌────▼─────┐
                    │ STARTING │  (camera init in progress)
                    └────┬─────┘
                         │ success
              ┌──────────▼──────────┐
              │     RECOGNIZING     │  (main operational state)
              │  [live feed active] │
              └──┬────────┬─────────┘
                 │        │ model combobox changed
       [⏹ Stop] │        ▼
                 │  ┌──────────────┐
                 │  │  SWITCHING   │  (model swap in progress)
                 │  └──────┬───────┘
                 │         │ swap complete
                 │         └──────────────────┐
                 │                            │
                 ▼                            ▼
          ┌──────────┐                ┌──────────────┐
          │ STOPPED  │                │  RECOGNIZING │
          └──────────┘                └──────────────┘
```

**Per-state UI changes:**

| State | Camera Canvas | Start/Stop | Model Selector | Status Dot |
|---|---|---|---|---|
| IDLE | Black placeholder | ▶ Start (enabled) | enabled | ● grey |
| STARTING | Spinner / "Initializing…" | disabled | disabled | ● amber |
| RECOGNIZING | Live feed + overlays | ⏹ Stop (enabled) | enabled | ● green |
| SWITCHING | Last frame frozen | disabled | disabled | ● amber |
| STOPPED | Frozen last frame | ▶ Start (enabled) | enabled | ● red |

---

## 7. Registration UX Flow

```
User clicks [● Capture]
    │
    ▼
Validation: name not empty?
    │ fail → shake animation on entry, red border, tooltip "Name required"
    │ pass ↓
    ▼
Button changes to [● Capturing… 1/5]
Progressbar appears (0 → 5 fill animated)
    │
    ▼  (5 frames captured via RegistrationService)
    ├── success → Treeview row appended, success toast notification
    └── failure → error toast "No face detected — please try again"
```

---

## 8. Notification Toast

A lightweight non-blocking notification widget:

```python
# app/ui/app_window.py

def show_toast(root, message: str, level: str = "info",
               duration_ms: int = 3000) -> None:
    """
    Levels: 'info' | 'success' | 'warning' | 'error'
    Appears at bottom-right of window, fades out after duration_ms.
    """
    color_map = {
        "info":    COLORS["info"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "error":   COLORS["danger"],
    }
    # Create toplevel-less label overlay using place() geometry
    # Animate opacity via alpha attribute (Windows/macOS)
```

---

## 9. Accessibility & UX Conventions

- All buttons have keyboard focus support (`takefocus=True`)
- `Tab` order follows visual top-to-bottom, left-to-right
- Error states show inline text (not just color) for accessibility
- Minimum button size: 32px height
- Treeview rows: 28px height for comfortable touch/click targets
- Delete action always requires confirmation dialog (destructive operations)
- Camera and model selector disabled during transitions (prevents double-click race)