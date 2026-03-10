"""Symbolic node diagram widget."""

import math
from qtpy.QtWidgets import QWidget, QSizePolicy
from qtpy.QtCore import Qt
from qtpy.QtGui import QPainter, QColor, QPen, QBrush, QFont

# Distinct colours for up to 8 task groups
_TASK_COLORS = [
    QColor(70,  130, 180),   # steel blue
    QColor(204,  85,   0),   # burnt orange
    QColor( 34, 139,  34),   # forest green
    QColor(160, 120,   0),   # dark gold
    QColor(128,   0, 128),   # purple
    QColor(  0, 139, 139),   # dark cyan
    QColor(165,  42,  42),   # brown
    QColor( 80,  80,  80),   # dark grey
]


class NodeDiagramWidget(QWidget):
    """
    Paints a symbolic diagram of a single representative compute node,
    showing CPU-core allocation (coloured by task/thread group) and a
    memory bar.

    Call :meth:`set_layout` whenever the resource parameters change.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._num_nodes       = 1
        self._tasks_per_node  = 1
        self._threads_per_task = 1
        self._mem             = 4.0
        self._mem_unit        = "GB"
        self._sockets         = 1        # visual socket grouping

        self.setMinimumSize(210, 190)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_layout(self, num_nodes: int, tasks_per_node: int,
                   threads_per_task: int, mem: float,
                   mem_unit: str = "GB", sockets: int = 1):
        """Update the diagram.  Safe to call with user-entered values."""
        self._num_nodes        = max(1, int(num_nodes))
        self._tasks_per_node   = max(1, int(tasks_per_node))
        self._threads_per_task = max(1, int(threads_per_task))
        try:
            self._mem = max(0.0, float(mem))
        except (ValueError, TypeError):
            self._mem = 0.0
        self._mem_unit = mem_unit or "GB"
        self._sockets  = max(1, int(sockets))
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw(painter)
        painter.end()

    def _draw(self, p: QPainter):
        W, H = self.width(), self.height()
        M          = 10   # outer margin
        TITLE_H    = 22
        GAP        = 4
        MEM_H      = 22
        SUMMARY_H  = 18
        PAD        = 8    # inner box padding

        # Vertical regions
        title_y   = M
        box_y     = title_y + TITLE_H + GAP
        box_h     = H - box_y - GAP - MEM_H - GAP - SUMMARY_H - M
        mem_y     = box_y + box_h + GAP
        summary_y = mem_y + MEM_H + 2

        box_x = M
        box_w = W - 2 * M

        num_nodes = self._num_nodes
        tasks     = self._tasks_per_node
        threads   = self._threads_per_task
        total_cores = tasks * threads

        # ---- Title -------------------------------------------------------
        p.setFont(QFont("Sans Serif", 9, QFont.Weight.Bold))
        p.setPen(QColor(40, 40, 60))
        title = f"Node  ×{num_nodes}" if num_nodes > 1 else "Node"
        p.drawText(box_x, title_y, box_w, TITLE_H,
                   int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   title)

        # ---- Node chassis ------------------------------------------------
        p.setPen(QPen(QColor(90, 100, 130), 2))
        p.setBrush(QColor(244, 244, 250))
        p.drawRoundedRect(box_x, box_y, box_w, box_h, 7, 7)

        # ---- Socket dividers ---------------------------------------------
        if self._sockets > 1 and box_w > 30:
            p.setPen(QPen(QColor(160, 160, 190), 1, Qt.PenStyle.DashLine))
            for s in range(1, self._sockets):
                sx = box_x + (box_w * s) // self._sockets
                p.drawLine(sx, box_y + 4, sx, box_y + box_h - 4)
            p.setPen(Qt.PenStyle.NoPen)

        # ---- CPU core grid -----------------------------------------------
        MAX_DISP  = 64          # max squares to draw; group above this
        gx = box_x + PAD
        gy = box_y + PAD
        gw = box_w - 2 * PAD
        gh = box_h - 2 * PAD

        if total_cores > 0 and gw > 8 and gh > 8:
            display_n = min(total_cores, MAX_DISP)
            cols, cell = _best_grid(display_n, gw, gh)
            rows = math.ceil(display_n / cols)
            gap  = max(1, min(3, cell // 5))

            act_w = cols * cell + gap * (cols - 1)
            act_h = rows * cell + gap * (rows - 1)
            sx = gx + (gw - act_w) // 2
            sy = gy + (gh - act_h) // 2

            core_i = 0
            for task_i in range(tasks):
                base = _TASK_COLORS[task_i % len(_TASK_COLORS)]
                for th_i in range(threads):
                    if core_i >= MAX_DISP:
                        break
                    row = core_i // cols
                    col = core_i % cols
                    cx  = sx + col * (cell + gap)
                    cy  = sy + row * (cell + gap)

                    # Alternate shade per thread within a task
                    fill = base.lighter(100 + th_i * 12) if th_i % 2 == 0 \
                           else base.lighter(118 + th_i * 8)

                    p.setPen(QPen(base.darker(145), 1))
                    p.setBrush(fill)
                    r = max(1, cell // 4)
                    p.drawRoundedRect(cx, cy, cell, cell, r, r)
                    core_i += 1
                if core_i >= MAX_DISP:
                    break

            if total_cores > MAX_DISP:
                p.setFont(QFont("Sans Serif", 7))
                p.setPen(QColor(110, 110, 110))
                p.drawText(gx, sy + act_h + 2, gw, 14,
                           int(Qt.AlignmentFlag.AlignHCenter),
                           f"… {total_cores} cores total")

        # ---- Memory bar --------------------------------------------------
        LBL_W = 58
        bar_x = box_x + LBL_W + 4
        bar_w = box_w - LBL_W - 4
        bh    = MEM_H - 4

        p.setFont(QFont("Sans Serif", 8))
        p.setPen(QColor(60, 60, 60))
        p.drawText(box_x, mem_y, LBL_W, MEM_H,
                   int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                   "Memory:")

        # background track
        p.setPen(QPen(QColor(155, 155, 155), 1))
        p.setBrush(QColor(210, 210, 210))
        p.drawRoundedRect(bar_x, mem_y + 2, bar_w, bh, 4, 4)

        # fill
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(70, 130, 180, 210))
        p.drawRoundedRect(bar_x + 1, mem_y + 3, bar_w - 2, bh - 2, 3, 3)

        # label on the bar
        p.setPen(QColor(255, 255, 255))
        p.drawText(bar_x, mem_y + 2, bar_w, bh,
                   int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                   f"{self._mem:g} {self._mem_unit}")

        # ---- Summary text ------------------------------------------------
        all_cores = total_cores * num_nodes
        if threads > 1:
            per = (f"{tasks} task{'s' if tasks != 1 else ''} "
                   f"× {threads} threads = {total_cores} cores/node")
        else:
            per = (f"{tasks} task{'s' if tasks != 1 else ''} = "
                   f"{total_cores} core{'s' if total_cores != 1 else ''}/node")

        summary = per + (f"  ({all_cores} total)" if num_nodes > 1 else "")

        p.setFont(QFont("Sans Serif", 8))
        p.setPen(QColor(55, 55, 55))
        p.drawText(box_x, summary_y, box_w, SUMMARY_H,
                   int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter),
                   summary)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _best_grid(n: int, w: int, h: int):
    """Return (cols, cell_px) maximising cell size for *n* items in *w*×*h*."""
    if n <= 0:
        return 1, max(4, min(w, h))
    ratio = max(0.5, w / h) if h > 0 else 1.0
    cols  = max(1, round(math.sqrt(n * ratio)))
    cols  = min(cols, n)
    rows  = math.ceil(n / cols)
    gap   = 2
    cell  = min(
        (w - gap * (cols - 1)) // cols,
        (h - gap * (rows - 1)) // rows,
    )
    return cols, max(4, cell)
