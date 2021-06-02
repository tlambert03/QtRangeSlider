from typing import List, Sequence, Tuple, Union

from ._generic_qslider import CC_SLIDER, SC_GROOVE, SC_HANDLE, SC_NONE, _GenericSlider
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
from .qtcompat.QtWidgets import QSlider, QStyle, QStyleOptionSlider, QStylePainter

ControlType = Tuple[str, int]

SC_BAR = QStyle.SubControl.SC_ScrollBarSubPage


class QRangeSlider(_GenericSlider[Tuple[float, ...]]):
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

    def _fixStyleOption(self, option):
        pass

    @property
    def _optSliderPositions(self):
        return [self._to_qinteger_space(p - self._minimum) for p in self._position]

    def _getBarColor(self):
        return self._style.brush(self._styleOption)

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

    def _draw_handle(self, painter, opt):
        if self._should_draw_bar:
            self._drawBar(painter, opt)

        opt.subControls = SC_HANDLE
        hidx = -1
        pidx = -1
        if self._pressedControl and self._pressedControl == SC_HANDLE:
            pidx = self._pressedIndex
        else:
            if self._hoverControl == SC_HANDLE:
                hidx = self._hoverIndex
        for idx, pos in enumerate(self._optSliderPositions):
            opt.sliderPosition = pos
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
        opt = self._styleOption
        self._pressedControl, self._pressedIndex = self._getControlAtPos(pos, opt)

    def _setClickOffset(self, pos):
        if self._pressedControl == SC_BAR:
            self._clickOffset = self._pixelPosToRangeValue(self._pick(pos))
            self._sldPosAtPress = tuple(self._position)
        elif self._pressedControl == SC_HANDLE:
            hr = self._handleRect(self._pressedIndex)
            self._clickOffset = self._pick(pos - hr.topLeft())

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._pressedControl == SC_BAR:
            ev.accept()
            delta = self._clickOffset - self._pixelPosToRangeValue(self._pick(ev.pos()))
            self._offsetAllPositions(-delta, self._sldPosAtPress)
        else:
            super().mouseMoveEvent(ev)

    def _handleRect(self, handle_index: int, opt: QStyleOptionSlider = None) -> QRect:
        """Return the QRect for all handles."""
        opt = opt or self._styleOption
        opt.sliderPosition = self._optSliderPositions[handle_index]
        return self.style().subControlRect(CC_SLIDER, opt, SC_HANDLE, self)

    def _barRect(self, opt: QStyleOptionSlider) -> QRect:
        """Return the QRect for the bar between the outer handles."""
        r_groove = self.style().subControlRect(CC_SLIDER, opt, SC_GROOVE, self)
        r_bar = QRectF(r_groove)
        hdl_low, hdl_high = self._handleRect(0, opt), self._handleRect(-1, opt)

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
        self, pos: QPoint, opt: QStyleOptionSlider = None
    ) -> Tuple[QStyle.SubControl, int]:
        """Update self._pressedControl based on ev.pos()."""
        opt = opt or self._styleOption

        if isinstance(pos, QPointF):
            pos = pos.toPoint()

        for i in range(len(self._position)):
            if self._handleRect(i, opt).contains(pos):
                return (SC_HANDLE, i)

        click_pos = self._pixelPosToRangeValue(self._pick(pos))
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

    def _execute_scroll(self, steps_to_scroll, modifiers):
        if modifiers & Qt.AltModifier:
            self._spreadAllPositions(shrink=steps_to_scroll < 0)
        else:
            self._offsetAllPositions(steps_to_scroll)
        self.triggerAction(QSlider.SliderMove)

    def _has_scroll_space_left(self, offset):
        return (offset > 0 and max(self._value) < self._maximum) or (
            offset < 0 and min(self._value) < self._minimum
        )

    def _spreadAllPositions(self, shrink=False, gain=1.1, ref=None) -> None:
        if ref is None:
            ref = self._position
        # if self._bar_is_rigid:  # TODO

        if shrink:
            gain = 1 / gain
        center = abs(ref[-1] + ref[0]) / 2
        self.setSliderPosition([((i - center) * gain) + center for i in ref])


# QRangeSlider.__doc__ += "\n" + textwrap.indent(QSlider.__doc__, "    ")


class QDoubleRangeSlider(QRangeSlider):
    def value(self) -> Tuple[int, ...]:
        """Get current value of the widget as a tuple of integers."""
        return tuple(float(v) for v in self._value)
