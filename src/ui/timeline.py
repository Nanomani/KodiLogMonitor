# ui/timeline.py
"""
Vertical timeline strip - a thin canvas that shows a colour-coded overview
of the log from top (oldest line) to bottom (newest line).

Each displayed line maps to a proportional pixel row; consecutive lines that
share the same log level are merged into a single coloured rectangle.
A lightweight outline rectangle marks the currently visible viewport.

Clicking or dragging the strip scrolls the text area to that position and
activates pause mode so the view stays put.
"""
import re
import tkinter as tk
from datetime import datetime

from config import (
    LOG_COLORS,
    COLOR_BG_MAIN,
    COLOR_BG_TIPS,
    COLOR_TEXT_TIPS,
    COLOR_TIMELINE_VIEWPORT,   # dedicated color for the viewport overlay outline
)
from languages import LANGS

# Severity order used to pick the dominant colour when a pixel bucket spans
# lines of mixed levels.  Higher value wins.
_PRIORITY = {"error": 4, "warning": 3, "info": 2, "debug": 1}

# Minimum guaranteed pixel height for high-severity segments so they remain
# visible even on very long logs where proportional mapping gives < 1 px.
_MIN_SEG_H = {"error": 3, "warning": 2}

# Maps log tag → LANGS key for the hover tooltip label.
# The actual translated string is resolved at runtime via self.current_lang.
_TAG_TO_LANG_KEY = {"error": "err", "warning": "warn", "info": "info", "debug": "debug"}

# Captures the full Kodi timestamp: "YYYY-MM-DD HH:MM:SS.mmm"
_TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})")


def _extract_ts(text):
    """Return the timestamp string from a log line, or None if not found."""
    m = _TS_RE.search(text)
    return m.group(1) if m else None


def _parse_ts(ts_str):
    """Parse a Kodi timestamp string to a datetime object, or None."""
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        return None

# Width of the coloured segment area in logical pixels (before DPI scaling).
# sc() will multiply by self.scale: 14 px on FHD (scale=0.50), 28 px on 4K (scale=1).
_STRIP_WIDTH    = 28

# Extra canvas pixels added on each side beyond the segment area so that the
# viewport overlay border always falls in an empty zone and stays visible even
# when the viewport is at the very top or bottom of the strip.
_STRIP_OVERHANG = 2


class TimelineMixin:
    """
    Mixin that adds the vertical timeline strip to KodiLogMonitor.

    Depends on (provided by the main class via other mixins):
      self.root             – tk / CTk root window
      self.main_container   – CTkFrame that holds txt_area + scrollbars
      self.txt_area         – tk.Text log widget
      self.v_scroll         – CTkScrollbar (vertical)
      self.is_paused        – tk.BooleanVar
      self.update_button_colors() – syncs the pause-button colour (optional)
    """

    # ── Setup ─────────────────────────────────────────────────────────────

    def timeline_setup(self):
        """
        Create the timeline canvas widget and bind events.
        Must be called from _build_main_area, after main_container exists
        but before txt_area is gridded (so column indices are correct).
        """
        self._timeline_data       = []    # list[str|None]:      one tag per displayed line
        self._timeline_timestamps = []    # list[str|None]:      timestamp string (or None for orphans)
        self._timeline_first_ts   = None  # datetime|None:       first event's timestamp
        self._timeline_draw_pending = False
        self._tl_tip_last_idx     = -1   # cache: avoids re-parsing on same position

        self.timeline_canvas = tk.Canvas(
            self.main_container,
            # Total canvas width = segment area + 2 × overhang.
            # DPI-aware: 18 px on FHD (scale=0.50), 36 px on 4K (scale=1.0).
            width=self.sc(_STRIP_WIDTH + 2 * _STRIP_OVERHANG),
            bg=COLOR_BG_MAIN,
            highlightthickness=0,
            cursor="hand2",
        )

        self.timeline_canvas.bind("<Button-1>",  self._timeline_on_click)
        self.timeline_canvas.bind("<B1-Motion>", self._timeline_on_drag)
        self.timeline_canvas.bind("<Configure>", self._timeline_on_resize)
        self.timeline_canvas.bind("<Motion>",    self._timeline_on_hover)
        self.timeline_canvas.bind("<Leave>",     self._timeline_hide_tip)

        # Tooltip Toplevel - created once, shown/hidden on hover
        self._tl_tip = tk.Toplevel(self.root)
        self._tl_tip.withdraw()
        self._tl_tip.overrideredirect(True)
        self._tl_tip.configure(bg=COLOR_BG_TIPS)
        self._tl_tip_label = tk.Label(
            self._tl_tip,
            text="",
            bg=COLOR_BG_TIPS,
            fg=COLOR_TEXT_TIPS,
            font=(self._mono_font, 10),
            padx=6,
            pady=4,
            justify="left",
        )
        self._tl_tip_label.pack()

    # ── Public data API ───────────────────────────────────────────────────

    def timeline_rebuild(self, valid_data):
        """
        Full rebuild from the list of (text, tag) tuples passed to bulk_insert.
        Call this right after bulk_insert has populated the text widget.
        """
        self._timeline_data       = []
        self._timeline_timestamps = []
        self._timeline_first_ts   = None
        self._tl_tip_last_idx     = -1

        for text, tag in valid_data:
            self._timeline_data.append(tag)
            ts_str = _extract_ts(text)
            self._timeline_timestamps.append(ts_str)
            if ts_str is not None and self._timeline_first_ts is None:
                self._timeline_first_ts = _parse_ts(ts_str)

        self._timeline_schedule_draw()

    def timeline_append(self, batch):
        """
        Incremental append for live-tail updates.
        Call after append_batch_to_gui with the same batch list.
        """
        for text, tag in batch:
            self._timeline_data.append(tag)
            ts_str = _extract_ts(text)
            self._timeline_timestamps.append(ts_str)
            if ts_str is not None and self._timeline_first_ts is None:
                self._timeline_first_ts = _parse_ts(ts_str)
        self._timeline_schedule_draw()

    def timeline_clear(self):
        """
        Reset the strip (new file loaded, filters cleared, or no results).
        """
        self._timeline_data       = []
        self._timeline_timestamps = []
        self._timeline_first_ts   = None
        self._tl_tip_last_idx     = -1
        self._timeline_hide_tip()
        try:
            self.timeline_canvas.delete("all")
        except Exception:
            pass

    # ── Rendering ─────────────────────────────────────────────────────────

    def _timeline_schedule_draw(self):
        """
        Collapse multiple rapid rebuild/append calls into a single deferred
        redraw (50 ms).  Prevents hammering the canvas during a burst of lines.
        """
        if self._timeline_draw_pending:
            return
        self._timeline_draw_pending = True
        self.root.after(50, self._timeline_do_draw)

    def _timeline_do_draw(self):
        self._timeline_draw_pending = False
        self._timeline_draw()

    def _timeline_draw(self):
        """
        Render colour segments onto the canvas, then draw the viewport indicator.

        Algorithm
        ---------
        Pass 1 - proportional rendering:
          For each pixel row y, compute which slice of _timeline_data it covers,
          pick the highest-severity colour in that slice, then merge consecutive
          same-colour rows into one rectangle.

        Pass 2 - minimum-height guarantee:
          High-severity segments (error ≥ 3 px, warning ≥ 2 px) are overdrawn on
          top if their natural proportional height is below the threshold.  This
          ensures isolated events remain visible on very long logs.
        """
        canvas = self.timeline_canvas
        try:
            h = canvas.winfo_height()
            w = canvas.winfo_width()
        except Exception:
            return

        if h <= 1 or w <= 1:
            return

        n = len(self._timeline_data)
        canvas.delete("segments")          # remove previous colour blocks only

        if n == 0:
            canvas.delete("all")
            return

        # Segments are drawn only in the inner zone, leaving _STRIP_OVERHANG px
        # empty on each side so the viewport overlay borders are always visible.
        overhang = self.sc(_STRIP_OVERHANG)
        seg_x0   = overhang
        seg_x1   = w - overhang

        # ── Pass 1: proportional colour runs ──────────────────────────────
        prev_color    = None
        prev_priority = 0
        prev_y        = 0
        high_segs     = []   # (y_top, y_bot, color, priority) for overdraw pass

        for y in range(h):
            i_start = int(y       * n / h)
            i_end   = int((y + 1) * n / h)
            # Guarantee at least one element per bucket
            if i_end <= i_start:
                i_end = i_start + 1
            if i_end > n:
                i_end = n

            color, priority = self._timeline_bucket_color(i_start, i_end)

            if color != prev_color:
                # Flush the previous run
                if prev_color is not None and prev_y < y:
                    canvas.create_rectangle(
                        seg_x0, prev_y, seg_x1, y,
                        fill=prev_color, outline="",
                        tags="segments",
                    )
                    if prev_priority >= 3:           # warning or error
                        high_segs.append((prev_y, y, prev_color, prev_priority))
                prev_color    = color
                prev_priority = priority
                prev_y        = y

        # Flush the last run
        if prev_color is not None and prev_y < h:
            canvas.create_rectangle(
                seg_x0, prev_y, seg_x1, h,
                fill=prev_color, outline="",
                tags="segments",
            )
            if prev_priority >= 3:
                high_segs.append((prev_y, h, prev_color, prev_priority))

        # ── Pass 2: overdraw high-severity segments below minimum height ──
        for y_top, y_bot, color, priority in high_segs:
            tag_name  = "error" if priority >= 4 else "warning"
            min_h     = _MIN_SEG_H.get(tag_name, 1)
            nat_h     = y_bot - y_top
            if nat_h < min_h:
                center    = (y_top + y_bot) // 2
                new_top   = max(0,     center - min_h // 2)
                new_bot   = min(h - 1, new_top + min_h)
                canvas.create_rectangle(
                    seg_x0, new_top, seg_x1, new_bot,
                    fill=color, outline="",
                    tags="segments",
                )

        # Draw the viewport indicator on top of the colour blocks
        self._timeline_draw_viewport()

    def _timeline_bucket_color(self, i_start, i_end):
        """
        Return (fill_colour, priority) for a bucket [i_start, i_end) of
        _timeline_data.  Uses the highest-severity log level found in the range.
        Orphan / continuation lines (tag=None) count as background (priority 0).
        """
        best_priority = -1
        best_tag      = None
        for tag in self._timeline_data[i_start:i_end]:
            p = _PRIORITY.get(tag, 0)
            if p > best_priority:
                best_priority = p
                best_tag      = tag

        if best_tag is None:
            return COLOR_BG_MAIN, 0                  # blend into background
        return LOG_COLORS.get(best_tag, COLOR_BG_MAIN), best_priority

    def _timeline_draw_viewport(self, *_):
        """
        Draw (or refresh) the viewport outline rectangle.
        Colour: COLOR_TIMELINE_VIEWPORT (dedicated, easy to change in config.py).
        Width:  DPI-aware - 1 px on FHD (scale=0.50), 2 px on 4K (scale=1.0),
                with a floor of 1 px so the outline is never invisible.
        """
        canvas = self.timeline_canvas
        try:
            top, bottom = self.txt_area.yview()
            h = canvas.winfo_height()
            w = canvas.winfo_width()
        except Exception:
            return

        y_top = max(0,     int(top    * h))
        y_bot = min(h - 1, int(bottom * h))
        if y_bot - y_top < 4:                        # minimum visible height
            y_bot = y_top + 4

        border_w = max(2, self.sc(4))                # 2 px FHD, 4 px 4K
        # Inset by half the border width so the stroke is not clipped by the
        # canvas edges (tkinter centers the stroke on the rectangle coordinates).
        # The canvas is _STRIP_OVERHANG px wider on each side than the segment
        # zone, so the vertical borders of the overlay fall in the empty margin
        # and stay visible regardless of the log content behind them.
        inset    = border_w // 2

        canvas.delete("viewport")
        canvas.create_rectangle(
            inset, y_top, w - 1 - inset, y_bot,
            outline=COLOR_TIMELINE_VIEWPORT,
            fill="",
            width=border_w,
            tags="viewport",
        )

    # ── Interaction ───────────────────────────────────────────────────────

    def _timeline_on_click(self, event):
        self._timeline_scroll_to(event.y)

    def _timeline_on_drag(self, event):
        self._timeline_scroll_to(event.y)

    def _timeline_scroll_to(self, y_pixel):
        """
        Scroll the log to the line proportional to y_pixel, then activate pause
        so the view stays still.
        """
        n = len(self._timeline_data)
        if n == 0:
            return
        try:
            h = self.timeline_canvas.winfo_height()
            if h <= 0:
                return
            fraction = max(0.0, min(1.0, y_pixel / h))
            line_num = max(1, min(n, int(fraction * n) + 1))

            self.txt_area.see(f"{line_num}.0")
            self.txt_area.mark_set(tk.INSERT, f"{line_num}.0")

            # Activate pause so the view stays at the clicked position
            if not self.is_paused.get():
                self.is_paused.set(True)
                if hasattr(self, "update_button_colors"):
                    self.update_button_colors()
        except Exception:
            pass

    def _timeline_on_resize(self, event):
        """Canvas resized - redraw immediately (no debounce needed here)."""
        if not self._timeline_draw_pending:
            self._timeline_draw()

    # ── Scroll sync ───────────────────────────────────────────────────────

    def _timeline_yscroll(self, *args):
        """
        Wrapper for txt_area's yscrollcommand.
        Forwards to the scrollbar AND refreshes the viewport indicator so the
        outline rectangle stays in sync as the user scrolls.
        """
        self.v_scroll.set(*args)
        self._timeline_draw_viewport()

    # ── Tooltip ───────────────────────────────────────────────────────────

    def _timeline_on_hover(self, event):
        """
        Show a tooltip with the timestamp and elapsed time of the log line
        under the cursor.  Uses _tl_tip_last_idx to skip re-computation when
        the mouse stays on the same logical line bucket.
        """
        n = len(self._timeline_data)
        if n == 0:
            self._timeline_hide_tip()
            return

        try:
            h = self.timeline_canvas.winfo_height()
            if h <= 0:
                return
        except Exception:
            return

        # Map pixel y → line index
        fraction = max(0.0, min(1.0, event.y / h))
        idx = max(0, min(n - 1, int(fraction * n)))

        # Avoid re-computing if hovering the same bucket as last time
        if idx == self._tl_tip_last_idx:
            # Just reposition the already-visible tooltip
            self._tl_tip_reposition(event)
            return
        self._tl_tip_last_idx = idx

        # Find the nearest line in [idx..n) that has a timestamp
        ts_str = None
        for i in range(idx, n):
            if self._timeline_timestamps[i] is not None:
                ts_str = self._timeline_timestamps[i]
                break
        # If not found forward, try backward
        if ts_str is None:
            for i in range(idx - 1, -1, -1):
                if self._timeline_timestamps[i] is not None:
                    ts_str = self._timeline_timestamps[i]
                    break

        if ts_str is None:
            self._timeline_hide_tip()
            return

        # Build tooltip text - level label first, then timestamp, then elapsed
        tag   = self._timeline_data[idx] if idx < len(self._timeline_data) else None
        label = None
        if tag:
            lang_key = _TAG_TO_LANG_KEY.get(tag)
            if lang_key:
                l_ui  = LANGS.get(self.current_lang.get(), LANGS["EN"])
                label = l_ui.get(lang_key)
        lines = []
        if label:
            lines.append(label)
        lines.append(ts_str)
        if self._timeline_first_ts is not None:
            dt = _parse_ts(ts_str)
            if dt is not None:
                delta = dt - self._timeline_first_ts
                total_seconds = int(delta.total_seconds())
                if total_seconds < 0:
                    total_seconds = 0
                h_val, rem = divmod(total_seconds, 3600)
                m_val, s_val = divmod(rem, 60)
                if h_val:
                    elapsed = f"+{h_val}h {m_val:02d}m {s_val:02d}s"
                elif m_val:
                    elapsed = f"+{m_val}m {s_val:02d}s"
                else:
                    elapsed = f"+{s_val}s"
                lines.append(elapsed)

        self._tl_tip_label.configure(text="\n".join(lines))
        self._tl_tip_reposition(event)
        self._tl_tip.deiconify()
        self._tl_tip.lift()

    def _tl_tip_reposition(self, event):
        """Move the tooltip window near the cursor without flickering."""
        try:
            x = self.timeline_canvas.winfo_rootx() + self.timeline_canvas.winfo_width() + 4
            y = self.timeline_canvas.winfo_rooty() + event.y - 10
            self._tl_tip.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _timeline_hide_tip(self, event=None):
        """Hide the tooltip and reset the position cache."""
        self._tl_tip_last_idx = -1
        try:
            self._tl_tip.withdraw()
        except Exception:
            pass
