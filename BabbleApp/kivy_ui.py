"""
Shared Kivy UI building blocks for the Babble App.

Importing this module configures Kivy, so it must be imported before any other ``kivy`` module
(it is the first Kivy import in every GUI module of the app).
"""

import os
import weakref

# --- Kivy configuration (must happen before kivy.core.window is imported) -----------------------
os.environ.setdefault("KIVY_NO_ARGS", "1")  # Don't let Kivy swallow our command line arguments
os.environ.setdefault("KIVY_LOG_MODE", "MIXED")  # Don't hijack stderr / the root logger (logger.py does that)

from utils.misc_utils import is_android, bg_color_clear, bg_color_highlight

from kivy.config import Config

if not is_android:
    Config.set("graphics", "width", "960")
    Config.set("graphics", "height", "860")
    Config.set("graphics", "minimum_width", "480")
    Config.set("graphics", "minimum_height", "480")
    Config.set("kivy", "exit_on_escape", "0")
# Disable the red multitouch-emulation dots on right click
Config.set("input", "mouse", "mouse,multitouch_on_demand")

import cv2
import numpy as np
from kivy.clock import Clock
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, Triangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.stacklayout import StackLayout
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

BUTTON_COLOR = "#539e8a"
TEXT_COLOR = "#F0F0F0"
INPUT_BG = "#F0F0F0"
INPUT_FG = "#000000"
ROW_HEIGHT = dp(34)
SPACING = dp(6)
PADDING = dp(8)
FONT_SIZE = sp(14)


def rgba(hex_color):
    return get_color_from_hex(hex_color)


# --- Fonts ---------------------------------------------------------------------------------------
# Kivy's bundled Roboto has no CJK glyphs, so the Chinese locales (and the language picker, which
# always lists them) would render as boxes. Use a system font with wide coverage when one exists.
_FONT_CANDIDATES = [
    # Windows
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyh.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    # Android
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/NotoSansSC-Regular.otf",
    "/system/fonts/DroidSansFallback.ttf",
]


def setup_fonts():
    """Replace Kivy's default font with a system font that covers CJK + Cyrillic, if available."""
    override = os.environ.get("BABBLE_FONT")
    for path in ([override] if override else []) + _FONT_CANDIDATES:
        if path and os.path.isfile(path):
            try:
                LabelBase.register(DEFAULT_FONT, path)
                return path
            except Exception:
                continue
    return None


# --- Panels --------------------------------------------------------------------------------------
def paint_background(widget, hex_color):
    """Give a layout a solid background colour that follows its position and size."""
    with widget.canvas.before:
        color = Color(*rgba(hex_color))
        rect = Rectangle(pos=widget.pos, size=widget.size)

    def _update(*_):
        rect.pos = widget.pos
        rect.size = widget.size

    widget.bind(pos=_update, size=_update)
    widget._bg_color_instruction = color
    return widget


class Panel(BoxLayout):
    """Vertical box with a background colour, used in place of sg.Column(background_color=...)."""

    def __init__(self, bg=bg_color_highlight, auto_height=False, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", PADDING)
        kwargs.setdefault("spacing", SPACING)
        if auto_height:
            kwargs["size_hint_y"] = None
        super().__init__(**kwargs)
        paint_background(self, bg)
        if auto_height:
            self.bind(minimum_height=self.setter("height"))


def row(*widgets, bg=None):
    """A row of widgets that wraps onto further lines when the window is too narrow (e.g. phones)."""
    layout = StackLayout(
        orientation="lr-tb", size_hint_y=None, spacing=SPACING, padding=(0, 0)
    )
    layout.bind(minimum_height=layout.setter("height"))
    for w in widgets:
        if w is not None:
            layout.add_widget(w)
    if bg:
        paint_background(layout, bg)
    return layout


def spacer(width=None, height=None):
    return Widget(
        size_hint=(None if width else 1, None if height is not None else 1),
        width=width or 0,
        height=height or 0,
    )


# --- Tooltips (desktop only; there's no hover on touch screens) ----------------------------------
class _TooltipManager:
    DELAY = 0.6

    def __init__(self):
        self.widgets = []  # list of (weakref(widget), text)
        self.label = None
        self.current = None
        self.pending = None
        self.bound = False

    def register(self, widget, text):
        if not text or is_android:
            return
        self.widgets.append((weakref.ref(widget), text))
        if not self.bound:
            Window.bind(mouse_pos=self.on_mouse_pos)
            self.bound = True

    def _find(self, pos):
        alive = []
        found = None
        for ref, text in self.widgets:
            w = ref()
            if w is None:
                continue
            alive.append((ref, text))
            if found is None and w.get_root_window() is not None and w.opacity > 0:
                if w.collide_point(*w.to_widget(*pos)):
                    found = (w, text)
        self.widgets = alive
        return found

    def on_mouse_pos(self, window, pos):
        if not window.focus:
            return
        found = self._find(pos)
        target = found[0] if found else None
        if target is self.current:
            if self.label is not None:
                self._place(pos)
            return
        self.hide()
        self.current = target
        if found:
            self.pending = Clock.schedule_once(lambda dt: self.show(found[1]), self.DELAY)

    def show(self, text):
        self.label = Label(
            text=text,
            size_hint=(None, None),
            color=rgba(INPUT_FG),
            font_size=sp(13),
            padding=(dp(6), dp(4)),
            halign="left",
        )
        self.label.text_size = (dp(360), None)
        self.label.texture_update()
        self.label.text_size = (min(dp(360), self.label.texture_size[0]), None)
        self.label.texture_update()
        self.label.size = self.label.texture_size
        paint_background(self.label, "#FFFFE0")
        Window.add_widget(self.label)
        self._place(Window.mouse_pos)

    def _place(self, pos):
        x = min(pos[0] + dp(12), Window.width - self.label.width)
        y = pos[1] - self.label.height - dp(12)
        if y < 0:
            y = pos[1] + dp(16)
        self.label.pos = (max(0, x), y)

    def hide(self):
        if self.pending is not None:
            self.pending.cancel()
            self.pending = None
        if self.label is not None:
            Window.remove_widget(self.label)
            self.label = None
        self.current = None


tooltips = _TooltipManager()


def with_tooltip(widget, text):
    tooltips.register(widget, text)
    return widget


# --- Basic widgets ------------------------------------------------------------------------------
def _fit_width(widget, extra=dp(16), min_width=0):
    def _update(*_):
        widget.width = max(min_width, widget.texture_size[0] + extra)

    widget.bind(texture_size=_update)
    _update()


def label(text, bg=None, color=TEXT_COLOR, tooltip=None, bold=False, **kwargs):
    """Single-line label sized to its text."""
    lbl = Label(
        text=text,
        size_hint=(None, None),
        height=ROW_HEIGHT,
        color=rgba(color),
        font_size=FONT_SIZE,
        bold=bold,
        halign="left",
        valign="middle",
        **kwargs,
    )
    _fit_width(lbl, extra=dp(8) if not bg else dp(16))
    if bg:
        paint_background(lbl, bg)
    return with_tooltip(lbl, tooltip)


def wrapping_label(text, color=TEXT_COLOR, halign="left", **kwargs):
    """Label that fills the available width and wraps long text."""
    lbl = Label(
        text=text,
        size_hint=(1, None),
        color=rgba(color),
        font_size=FONT_SIZE,
        halign=halign,
        valign="middle",
        **kwargs,
    )
    lbl.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))
    lbl.bind(texture_size=lambda w, v: setattr(w, "height", max(ROW_HEIGHT, v[1])))
    return lbl


def section_header(text):
    return wrapping_label(text, bold=True)


def button(text, on_press=None, color=BUTTON_COLOR, tooltip=None, disabled=False, **kwargs):
    btn = Button(
        text=text,
        size_hint=(None, None),
        height=ROW_HEIGHT,
        font_size=FONT_SIZE,
        background_normal="",
        background_down="",
        background_color=rgba(color),
        disabled=disabled,
        **kwargs,
    )
    _fit_width(btn, extra=dp(24))

    def _press_feedback(instance, state):
        base = rgba(color)
        factor = 0.75 if state == "down" else 1.0
        instance.background_color = [base[0] * factor, base[1] * factor, base[2] * factor, base[3]]

    btn.bind(state=_press_feedback)
    if on_press:
        btn.bind(on_release=lambda *_: on_press())
    return with_tooltip(btn, tooltip)


class ValidatedTextInput(TextInput):
    """TextInput that rejects keystrokes producing text the ``validator`` doesn't accept.

    Replaces the old FreeSimpleGUI pattern of trimming the last character after an invalid edit.
    """

    def __init__(self, validator=None, **kwargs):
        self.validator = validator
        super().__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if self.validator is not None and not from_undo:
            if self.selection_text:
                start, end = sorted((self.selection_from, self.selection_to))
            else:
                start = end = self.cursor_index()
            candidate = self.text[:start] + substring + self.text[end:]
            if not self.validator(candidate):
                return
            if self.selection_text:
                # insert_text() doesn't replace the selection by itself; do it so the result
                # is exactly the candidate that was validated.
                self.delete_selection()
        return super().insert_text(substring, from_undo=from_undo)


def text_input(text, on_change=None, chars=20, validator=None, tooltip=None, **kwargs):
    """Single-line text box. ``on_change(new_text)`` is called on every edit."""
    ti = ValidatedTextInput(
        validator=validator,
        text="" if text is None else str(text),
        multiline=False,
        write_tab=False,
        size_hint=(None, None),
        height=ROW_HEIGHT,
        width=dp(14 + chars * 8.5),
        font_size=FONT_SIZE,
        background_color=rgba(INPUT_BG),
        foreground_color=rgba(INPUT_FG),
        **kwargs,
    )

    # Vertically centre the text using the real line height of the active font, so descenders
    # (e.g. "_") aren't clipped with taller fonts such as the CJK fallbacks.
    def _pad(*_):
        ti.padding = [dp(6), max(dp(1), (ti.height - ti.line_height) / 2)]

    ti.bind(height=_pad, line_height=_pad)
    _pad()
    if on_change:
        ti.bind(text=lambda inst, value: on_change(value))
    return with_tooltip(ti, tooltip)


def set_text_silently(widget, text, handler_owner, flag="_suppress_events"):
    """Set a TextInput's text without running the owner's change callbacks."""
    setattr(handler_owner, flag, True)
    try:
        widget.text = str(text)
    finally:
        setattr(handler_owner, flag, False)


def checkbox(text, active, on_change=None, tooltip=None, bg=None):
    """Checkbox with a clickable caption (caption may be empty)."""
    box = BoxLayout(orientation="horizontal", size_hint=(None, None), height=ROW_HEIGHT, spacing=dp(2))
    cb = CheckBox(active=bool(active), size_hint=(None, 1), width=dp(30), color=rgba(TEXT_COLOR))
    box.add_widget(cb)
    if text:
        lbl = Label(text=text, size_hint=(None, 1), color=rgba(TEXT_COLOR), font_size=FONT_SIZE)
        _fit_width(lbl, extra=dp(4))
        box.add_widget(lbl)

        def _toggle(instance, touch):
            if instance.collide_point(*touch.pos) and not cb.disabled:
                cb.active = not cb.active
                return True

        lbl.bind(on_touch_down=_toggle)

        def _resize(*_):
            box.width = cb.width + lbl.width + box.spacing

        lbl.bind(width=_resize)
        _resize()
    else:
        box.width = cb.width
    if bg:
        paint_background(box, bg)
    if on_change:
        cb.bind(active=lambda inst, value: on_change(value))
    box.checkbox = cb
    return with_tooltip(box, tooltip)


class _DarkSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = rgba("#3a383a")
        self.height = ROW_HEIGHT
        self.font_size = FONT_SIZE


def spinner(values, text, on_change=None, tooltip=None, width=None):
    """Drop-down selector (replacement for sg.OptionMenu)."""
    values = [str(v) for v in values]
    sp_ = Spinner(
        text=str(text),
        values=values,
        size_hint=(None, None),
        height=ROW_HEIGHT,
        font_size=FONT_SIZE,
        option_cls=_DarkSpinnerOption,
        background_normal="",
        background_color=rgba("#5a585a"),
        sync_height=True,
    )
    if width:
        sp_.width = width
    else:
        probe = Label(font_size=FONT_SIZE)
        widest = 0
        for v in values + [str(text)]:
            probe.text = v
            probe.texture_update()
            widest = max(widest, probe.texture_size[0])
        sp_.width = widest + dp(36)
    if on_change:
        sp_.bind(text=lambda inst, value: on_change(value))
    return with_tooltip(sp_, tooltip)


class ComboInput(BoxLayout):
    """Editable text box with a drop-down list of suggestions (replacement for sg.InputCombo)."""

    def __init__(self, values, text, chars=24, tooltip=None, on_change=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(None, None), height=ROW_HEIGHT, **kwargs)
        self.input = text_input(text, chars=chars, on_change=on_change)
        self.arrow = Button(
            size_hint=(None, 1),
            width=dp(28),
            background_normal="",
            background_color=rgba("#d0d0d0"),
        )
        with self.arrow.canvas.after:
            Color(0.2, 0.2, 0.2, 1)
            self._tri = Triangle()
        self.arrow.bind(pos=self._draw_arrow, size=self._draw_arrow)
        self.arrow.bind(on_release=self.open_dropdown)
        self.add_widget(self.input)
        self.add_widget(self.arrow)
        self.width = self.input.width + self.arrow.width
        self.values = list(values)
        with_tooltip(self.input, tooltip)

    def _draw_arrow(self, *_):
        cx, cy = self.arrow.center
        s = dp(5)
        self._tri.points = [cx - s, cy + s / 2, cx + s, cy + s / 2, cx, cy - s / 2]

    @property
    def text(self):
        return self.input.text

    @text.setter
    def text(self, value):
        self.input.text = "" if value is None else str(value)

    def open_dropdown(self, *_):
        dd = DropDown(max_height=dp(320))
        for v in self.values:
            opt = _DarkSpinnerOption(text=str(v), size_hint_y=None)
            opt.bind(on_release=lambda btn: dd.select(btn.text))
            dd.add_widget(opt)
        if not self.values:
            dd.add_widget(_DarkSpinnerOption(text="-", size_hint_y=None, disabled=True))
        dd.bind(on_select=lambda inst, value: setattr(self.input, "text", value))
        dd.auto_width = False
        dd.width = max(self.width, dp(240))
        dd.open(self)


def slider(min_value, max_value, value, on_change=None, tooltip=None, width=dp(260), step=1):
    s = Slider(
        min=min_value,
        max=max_value,
        value=value,
        step=step,
        size_hint=(None, None),
        height=ROW_HEIGHT,
        width=width,
    )
    if on_change:
        s.bind(value=lambda inst, v: on_change(v))
    return with_tooltip(s, tooltip)


def choose_folder(start_path, on_selected, title="Select folder"):
    """Folder picker popup (replacement for sg.FolderBrowse). Works on desktop and Android."""
    start = start_path if start_path and os.path.isdir(start_path) else os.getcwd()
    start = os.path.abspath(start)
    content = BoxLayout(orientation="vertical", spacing=SPACING)
    chooser = FileChooserListView(path=start, dirselect=True, filters=[lambda folder, name: os.path.isdir(os.path.join(folder, name))])
    content.add_widget(chooser)
    buttons = BoxLayout(size_hint_y=None, height=ROW_HEIGHT, spacing=SPACING)
    popup = Popup(title=title, content=content, size_hint=(0.9, 0.9))

    def _ok(*_):
        chosen = chooser.selection[0] if chooser.selection else chooser.path
        popup.dismiss()
        # Keep paths relative to the app folder where possible, like the default model path.
        try:
            rel = os.path.relpath(chosen, os.getcwd())
            if not rel.startswith(".."):
                chosen = rel
        except ValueError:  # Different drive on Windows
            pass
        on_selected(chosen.replace("\\", "/"))

    ok = Button(text="OK", background_normal="", background_color=rgba(BUTTON_COLOR))
    ok.bind(on_release=_ok)
    cancel = Button(text="Cancel")
    cancel.bind(on_release=lambda *_: popup.dismiss())
    buttons.add_widget(ok)
    buttons.add_widget(cancel)
    content.add_widget(buttons)
    popup.open()


# --- Image display -------------------------------------------------------------------------------
def frame_to_texture(frame, texture=None):
    """Upload an OpenCV image (BGR or grayscale) into a Kivy texture, reusing ``texture`` if possible."""
    if frame.ndim == 2:
        rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    elif frame.shape[2] == 4:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
    else:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    if texture is None or texture.size != (w, h):
        texture = Texture.create(size=(w, h), colorfmt="rgb")
        # OpenCV images are top-down, OpenGL textures are bottom-up.
        texture.flip_vertical()
    texture.blit_buffer(np.ascontiguousarray(rgb).tobytes(), colorfmt="rgb", bufferfmt="ubyte")
    return texture


class FrameView(Image):
    """Displays camera frames, scaled to fit while keeping aspect ratio (replacement for sg.Image)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("fit_mode", "contain")
        super().__init__(**kwargs)
        self._tex = None
        self.opacity = 0  # An Image without a texture renders as a white box; hide until a frame arrives

    def show_frame(self, frame):
        tex = frame_to_texture(frame, self._tex)
        if tex is not self._tex:
            self._tex = tex
            self.texture = tex
            self.opacity = 1
        else:
            self.canvas.ask_update()


class ROISelector(Widget):
    """Shows the full camera frame and lets the user drag out the mouth crop rectangle.

    Replacement for the sg.Graph used for cropping. Coordinates passed to ``on_select`` are in
    image pixels with the origin at the top-left, matching what the old Graph produced.
    """

    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self.on_select = on_select
        self._tex = None
        self._img_size = None
        self.start = None  # (x, y) image pixel coordinates
        self.end = None
        with self.canvas:
            Color(1, 1, 1, 1)
            self._rect = Rectangle()
            Color(*rgba("#6f4ca1"))
            self._sel = Line(width=dp(1.5))
        self.bind(pos=self._redraw, size=self._redraw)

    # geometry helpers
    def _layout(self):
        if not self._img_size:
            return None
        w, h = self._img_size
        s = min(self.width / w, self.height / h) if w and h else 0
        if s <= 0:
            return None
        ox = self.x + (self.width - w * s) / 2
        top = self.top
        return s, ox, top

    def _to_image(self, x, y):
        geo = self._layout()
        if geo is None:
            return None
        s, ox, top = geo
        w, h = self._img_size
        px = min(max((x - ox) / s, 0), w)
        py = min(max((top - y) / s, 0), h)
        return int(round(px)), int(round(py))

    def _to_widget(self, px, py):
        s, ox, top = self._layout()
        return ox + px * s, top - py * s

    def _redraw(self, *_):
        geo = self._layout()
        if geo is None:
            self._rect.size = (0, 0)
            self._sel.points = []
            return
        s, ox, top = geo
        w, h = self._img_size
        self._rect.texture = self._tex
        self._rect.pos = (ox, top - h * s)
        self._rect.size = (w * s, h * s)
        if self.start and self.end:
            x0, y0 = self._to_widget(*self.start)
            x1, y1 = self._to_widget(*self.end)
            self._sel.rectangle = (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        else:
            self._sel.points = []

    def show_frame(self, frame):
        self._tex = frame_to_texture(frame, self._tex)
        self._img_size = self._tex.size
        self._redraw()

    @property
    def image_size(self):
        return self._img_size

    # touch handling
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self._img_size is None:
            return super().on_touch_down(touch)
        if touch.is_mouse_scrolling:
            return False
        pt = self._to_image(*touch.pos)
        if pt is None:
            return False
        touch.grab(self)
        self.start = pt
        self.end = pt
        self._redraw()
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        pt = self._to_image(*touch.pos)
        if pt is not None:
            self.end = pt
            self._redraw()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        pt = self._to_image(*touch.pos)
        if pt is not None:
            self.end = pt
        self._redraw()
        if self.start and self.end:
            (x0, y0), (x1, y1) = self.start, self.end
            if abs(x0 - x1) != 0 and abs(y0 - y1) != 0:
                self.on_select(min(x0, x1), min(y0, y1), abs(x0 - x1), abs(y0 - y1))
        return True


def show_widget(container, widget, visible):
    """Attach/detach ``widget`` from ``container`` to emulate sg's ``update(visible=...)``."""
    if visible and widget.parent is None:
        container.add_widget(widget)
    elif not visible and widget.parent is not None:
        widget.parent.remove_widget(widget)
