import textwrap
from typing import List, Sequence, Tuple, Union

from ._generic_qslider import (
    CC_SLIDER,
    SC_GROOVE,
    SC_HANDLE,
    SC_NONE,
    SC_TICKMARKS,
    _GenericSlider,
)
from ._style import RangeSliderStyle, update_styles_from_stylesheet
from .qtcompat import QtGui
from .qtcompat.QtCore import (
    Property,
    QEvent,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    Qt,
    Signal,
)
from .qtcompat.QtWidgets import (
    QApplication,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QStylePainter,
)

ControlType = Tuple[str, int]

SC_BAR = QStyle.SubControl.SC_ScrollBarSubPage


class QRangeSlider(_GenericSlider):
    """MultiHandle Range Slider widget.

    Same API as QSlider, but `value`, `setValue`, `sliderPosition`, and
    `setSliderPosition` are all sequences of integers.

    The `valueChanged` and `sliderMoved` signals also both emit a tuple of
    integers.
    """

    # Emitted when the slider value has changed, with the new slider values
    valueChanged = Signal(tuple)

    # Emitted when sliderDown is true and the slider moves
    # This usually happens when the user is dragging the slider
    # The value is the positions of *all* handles.
    sliderMoved = Signal(tuple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # list of values
        self._value: List[int] = [20, 80]

        # list of current positions of each handle. same length as _value
        # If tracking is enabled (the default) this will be identical to _value
        self._position: List[int] = [20, 80]

        # which handle is being pressed/hovered
        self._pressedIndex = 0
        self._hoverIndex = 0

        # whether bar length is constant when dragging the bar
        # if False, the bar can shorten when dragged beyond min/max
        self._bar_is_rigid = True
        # whether clicking on the bar moves all handles, or just the nearest handle
        self._bar_moves_all = True
        self._should_draw_bar = True

        # color
        self._style = RangeSliderStyle()
        self.setStyleSheet("")
        update_styles_from_stylesheet(self)

    # ###############  Public API  #######################

    def setStyleSheet(self, styleSheet: str) -> None:
        # sub-page styles render on top of the lower sliders and don't work here.
        override = f"""
            \n{type(self).__name__}::sub-page:horizontal {{background: none}}
            \n{type(self).__name__}::sub-page:vertical {{background: none}}
        """
        return super().setStyleSheet(styleSheet + override)

    def value(self) -> Tuple[int, ...]:
        """Get current value of the widget as a tuple of integers."""
        return tuple(self._value)

    # def setValue(self, val: Sequence[int]) -> None:
    #     """Set current value of the widget with a sequence of integers.

    #     The number of handles will be equal to the length of the sequence
    #     """
    #     if not (isinstance(val, abc.Sequence) and len(val) >= 2):
    #         raise ValueError("value must be iterable of len >= 2")
    #     val = [self._bound(v) for v in val]
    #     if self._value == val and self._position == val:
    #         return
    #     self._value[:] = val[:]
    #     if self._position != val:
    #         self._position = val
    #         if self.isSliderDown():
    #             self.sliderMoved.emit(tuple(self._position))

    #     self.sliderChange(QSlider.SliderValueChange)
    #     self.valueChanged.emit(self.value())

    def barIsRigid(self) -> bool:
        """Whether bar length is constant when dragging the bar.

        If False, the bar can shorten when dragged beyond min/max. Default is True.
        """
        return self._bar_is_rigid

    def setBarIsRigid(self, val: bool = True) -> None:
        """Whether bar length is constant when dragging the bar.

        If False, the bar can shorten when dragged beyond min/max. Default is True.
        """
        self._bar_is_rigid = bool(val)

    def barMovesAllHandles(self) -> bool:
        """Whether clicking on the bar moves all handles (default), or just the nearest."""
        return self._bar_moves_all

    def setBarMovesAllHandles(self, val: bool = True) -> None:
        """Whether clicking on the bar moves all handles (default), or just the nearest."""
        self._bar_moves_all = bool(val)

    def barIsVisible(self) -> bool:
        """Whether to show the bar between the first and last handle."""
        return self._should_draw_bar

    def setBarVisible(self, val: bool = True) -> None:
        """Whether to show the bar between the first and last handle."""
        self._should_draw_bar = bool(val)

    def hideBar(self) -> None:
        self.setBarVisible(False)

    def showBar(self) -> None:
        self.setBarVisible(True)

    def sliderPosition(self) -> Tuple[int, ...]:
        """Get current value of the widget as a tuple of integers.

        If tracking is enabled (the default) this will be identical to value().
        """
        return tuple(self._position)

    def setSliderPosition(self, pos: Union[int, Sequence[int]], index=None) -> None:
        """Set current position of the handles with a sequence of integers.

        If `pos` is a sequence, it must have the same length as `value()`.
        If it is a scalar, index will be
        """
        if isinstance(pos, (list, tuple)):
            val_len = len(self.value())
            if len(pos) != val_len:
                msg = f"'sliderPosition' must have same length as 'value()' ({val_len})"
                raise ValueError(msg)

            for idx, p in enumerate(pos):
                self._position[idx] = self._bound(p, idx)
        else:
            idx = self._pressedIndex if index is None else index
            self._position[idx] = self._bound(pos, idx)
        self._updateSliderMove()

    # ###############  Implementation Details  #######################

    def _setPosition(self, val):
        self._position = list(val)

    def _bound(self, value, index=None):
        pos = super()._bound(value)
        if index is not None:
            pos = self._neighbor_bound(pos, index)
        return pos

    def _neighbor_bound(self, val, index):
        # make sure we don't go lower than any preceding index:
        min_dist = self.singleStep()
        _lst = self._position
        if index > 0:
            val = max(_lst[index - 1] + min_dist, val)
        # make sure we don't go higher than any following index:
        if index < (len(_lst) - 1):
            val = min(_lst[index + 1] - min_dist, val)
        return val

    def _offsetAllPositions(self, offset: int, ref=None) -> None:
        if ref is None:
            ref = self._position
        if self._bar_is_rigid:
            # NOTE: This assumes monotonically increasing slider positions
            if offset > 0 and ref[-1] + offset > self.maximum():
                offset = self.maximum() - ref[-1]
            elif ref[0] + offset < self.minimum():
                offset = self.minimum() - ref[0]
        self.setSliderPosition([i + offset for i in ref])

    def _spreadAllPositions(self, shrink=False, gain=1.1, ref=None) -> None:
        if ref is None:
            ref = self._position
        # if self._bar_is_rigid:  # TODO

        if shrink:
            gain = 1 / gain
        center = abs(ref[-1] + ref[0]) / 2
        self.setSliderPosition([((i - center) * gain) + center for i in ref])

    def _getStyleOption(self) -> QStyleOptionSlider:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        return opt

    def _fixStyleOption(self, opt):
        opt.sliderValue = 0
        opt.sliderPosition = 0

        opt.minimum = int(self._minimum)
        opt.maximum = int(self._maximum)
        # opt.tickInterval = self._tickInterval / _range * _max  # type: ignore
        # opt.pageStep = self._pageStep / _range * _max  # type: ignore
        # opt.singleStep = self._singleStep / _range * _max  # type: ignore

    def _getBarColor(self):
        return self._style.brush(self._getStyleOption())

    def _setBarColor(self, color):
        self._style.brush_active = color

    barColor = Property(QtGui.QBrush, _getBarColor, _setBarColor)

    def _drawBar(self, painter: QStylePainter, opt: QStyleOptionSlider):

        brush = self._style.brush(opt)

        r_bar = self._barRect(opt)
        if isinstance(brush, QtGui.QGradient):
            brush.setStart(r_bar.topLeft())
            brush.setFinalStop(r_bar.bottomRight())

        painter.setPen(self._style.pen(opt))
        painter.setBrush(brush)
        painter.drawRect(r_bar)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        """Paint the slider."""
        # initialize painter and options
        painter = QStylePainter(self)
        opt = self._getStyleOption()

        # draw groove and ticks
        opt.subControls = SC_GROOVE | SC_TICKMARKS
        painter.drawComplexControl(CC_SLIDER, opt)

        if self._should_draw_bar:
            self._drawBar(painter, opt)

        # draw handles
        opt.subControls = SC_HANDLE
        hidx = -1
        pidx = -1
        if self._pressedControl and self._pressedControl == SC_HANDLE:
            pidx = self._pressedIndex
        else:
            if self._hoverControl == SC_HANDLE:
                hidx = self._hoverIndex
        for idx, pos in enumerate(self._position):
            opt.sliderPosition = int(pos)
            if idx == pidx:  # make pressed handles appear sunken
                opt.state |= QStyle.State_Sunken
            else:
                opt.state = opt.state & ~QStyle.State_Sunken
            opt.activeSubControls = SC_HANDLE if idx == hidx else SC_NONE
            painter.drawComplexControl(CC_SLIDER, opt)

    def event(self, ev: QEvent) -> bool:
        if ev.type() == QEvent.StyleChange:
            update_styles_from_stylesheet(self)
        return super().event(ev)

    def _updateHoverControl(self, pos):
        old_hover = self._hoverControl, self._hoverIndex
        self._hoverControl, self._hoverIndex = self._getControlAtPos(pos)
        if (self._hoverControl, self._hoverIndex) != old_hover:
            self.update()

    def _updatePressedControl(self, pos):
        opt = self._getStyleOption()
        self._pressedControl, self._pressedIndex = self._getControlAtPos(pos, opt, True)

    def _setClickOffset(self, pos):
        if self._pressedControl == SC_BAR:
            self._clickOffset = self._pixelPosToRangeValue(self._pick(pos))
            self._sldPosAtPress = tuple(self._position)
        elif self._pressedControl == SC_HANDLE:
            hr = self._handleRects(handle_index=self._pressedIndex)
            self._clickOffset = self._pick(pos - hr.topLeft())

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._pressedControl == SC_BAR:
            ev.accept()
            delta = self._clickOffset - self._pixelPosToRangeValue(self._pick(ev.pos()))
            self._offsetAllPositions(-delta, self._sldPosAtPress)
        else:
            super().mouseMoveEvent(ev)

    def _handleRects(
        self, opt: QStyleOptionSlider = None, handle_index: int = None
    ) -> QRect:
        """Return the QRect for all handles."""
        if opt is None:
            opt = self._getStyleOption()

        style = self.style().proxy()

        if handle_index is not None:  # get specific handle rect
            opt.sliderPosition = int(self._position[handle_index])
            return style.subControlRect(CC_SLIDER, opt, SC_HANDLE, self)
        else:
            rects = []
            for p in self._position:
                opt.sliderPosition = int(p)
                r = style.subControlRect(CC_SLIDER, opt, SC_HANDLE, self)
                rects.append(r)
            return rects

    def _grooveRect(self, opt: QStyleOptionSlider) -> QRect:
        """Return the QRect for the slider groove."""
        style = self.style().proxy()
        return style.subControlRect(CC_SLIDER, opt, SC_GROOVE, self)

    def _barRect(self, opt: QStyleOptionSlider, r_groove: QRect = None) -> QRect:
        """Return the QRect for the bar between the outer handles."""
        if r_groove is None:
            r_groove = self._grooveRect(opt)
        r_bar = QRectF(r_groove)
        hdl_low, *_, hdl_high = self._handleRects(opt)

        thickness = self._style.thickness(opt)
        offset = self._style.offset(opt)

        if opt.orientation == Qt.Horizontal:
            r_bar.setTop(r_bar.center().y() - thickness / 2 + offset)
            r_bar.setHeight(thickness)
            r_bar.setLeft(hdl_low.center().x())
            r_bar.setRight(hdl_high.center().x())
        else:
            r_bar.setLeft(r_bar.center().x() - thickness / 2 + offset)
            r_bar.setWidth(thickness)
            r_bar.setBottom(hdl_low.center().y())
            r_bar.setTop(hdl_high.center().y())

        return r_bar

    # TODO: this is very much tied to mousepress... not a generic "get control"
    def _getControlAtPos(
        self, pos: QPoint, opt: QStyleOptionSlider = None, closest_handle=False
    ) -> Tuple[QStyle.SubControl, int]:
        """Update self._pressedControl based on ev.pos()."""
        if not opt:
            opt = self._getStyleOption()

        if isinstance(pos, QPointF):
            pos = pos.toPoint()

        for i, hdl in enumerate(self._handleRects(opt)):
            if hdl.contains(pos):
                return (SC_HANDLE, i)  # TODO: use enum for 'handle'

        click_pos = self._pixelPosToRangeValue(self._pick(pos), opt)
        for i, p in enumerate(self._position):
            if p > click_pos:
                if i > 0:
                    # the click was in an internal segment
                    if self._bar_moves_all:
                        return (SC_BAR, i)
                    avg = (self._position[i - 1] + self._position[i]) / 2
                    return (SC_HANDLE, i - 1 if click_pos < avg else i)
                # the click was below the minimum slider
                return (SC_HANDLE, 0)

        # the click was above the maximum slider
        return (SC_HANDLE, len(self._position) - 1)

        # return (SC_NONE, 0) # FIXME: case of position outside of widget

    # from QSliderPrivate::pixelPosToRangeValue
    def _pixelPosToRangeValue(self, pos: int, opt: QStyleOptionSlider = None) -> int:
        if not opt:
            opt = self._getStyleOption()
        groove_rect = self._grooveRect(opt)
        handle_rect = self._handleRects(opt, 0)
        if self.orientation() == Qt.Horizontal:
            sliderLength = handle_rect.width()
            sliderMin = groove_rect.x()
            sliderMax = groove_rect.right() - sliderLength + 1
        else:
            sliderLength = handle_rect.height()
            sliderMin = groove_rect.y()
            sliderMax = groove_rect.bottom() - sliderLength + 1
        return QStyle.sliderValueFromPosition(
            opt.minimum,
            opt.maximum,
            pos - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown,
        )

    def _pick(self, pt: QPoint) -> int:
        return pt.x() if self.orientation() == Qt.Horizontal else pt.y()

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        e.ignore()
        vertical = bool(e.angleDelta().y())
        delta = e.angleDelta().y() if vertical else e.angleDelta().x()
        if e.inverted():
            delta *= -1

        orientation = Qt.Vertical if vertical else Qt.Horizontal
        if self._scrollByDelta(orientation, e.modifiers(), delta):
            e.accept()

    def _scrollByDelta(self, orientation, modifiers, delta: int) -> bool:
        steps_to_scroll = 0.0
        pg_step = self.pageStep()

        # in Qt scrolling to the right gives negative values.
        if orientation == Qt.Horizontal:
            delta *= -1
        offset = delta / 120
        if modifiers & Qt.ShiftModifier:
            # Scroll one page regardless of delta:
            steps_to_scroll = max(-pg_step, min(pg_step, int(offset * pg_step)))
            self._offset_accum = 0
        elif modifiers & Qt.ControlModifier:
            # Scroll one page regardless of delta:
            _range = self.maximum() - self.minimum()

            steps_to_scroll = offset * _range * self._control_fraction
            self._offset_accum = 0
        else:
            # Calculate how many lines to scroll. Depending on what delta is (and
            # offset), we might end up with a fraction (e.g. scroll 1.3 lines). We can
            # only scroll whole lines, so we keep the reminder until next event.
            wheel_scroll_lines = QApplication.wheelScrollLines()
            steps_to_scrollF = wheel_scroll_lines * offset * self._effectiveSingleStep()

            # Check if wheel changed direction since last event:
            if self._offset_accum != 0 and (offset / self._offset_accum) < 0:
                self._offset_accum = 0

            self._offset_accum += steps_to_scrollF

            # Don't scroll more than one page in any case:
            steps_to_scroll = max(-pg_step, min(pg_step, int(self._offset_accum)))

            self._offset_accum -= int(self._offset_accum)

            if steps_to_scroll == 0:
                # We moved less than a line, but might still have accumulated partial
                # scroll, unless we already are at one of the ends.
                effective_offset = self._offset_accum
                if self.invertedControls():
                    effective_offset *= -1
                if effective_offset > 0 and max(self._value) < self.maximum():
                    return True
                if effective_offset < 0 and min(self._value) < self.minimum():
                    return True
                self._offset_accum = 0
                return False

        if self.invertedControls():
            steps_to_scroll *= -1

        _prev_value = self.value()

        if modifiers & Qt.AltModifier:
            self._spreadAllPositions(shrink=steps_to_scroll < 0)
        else:
            self._offsetAllPositions(steps_to_scroll)
        self.triggerAction(QSlider.SliderMove)

        if _prev_value == self.value():
            self._offset_accum = 0
            return False
        return True

    def _effectiveSingleStep(self) -> int:
        return self.singleStep() * self._repeatMultiplier

    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        return  # TODO


QRangeSlider.__doc__ += "\n" + textwrap.indent(QSlider.__doc__, "    ")
