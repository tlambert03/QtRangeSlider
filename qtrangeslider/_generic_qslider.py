from .qtcompat import QtGui
from .qtcompat.QtCore import QEvent, QPoint, QRect, Qt, Signal
from .qtcompat.QtWidgets import (
    QAbstractSlider,
    QApplication,
    QSlider,
    QStyle,
    QStyleOptionSlider,
    QStylePainter,
)

# from ._qrangeslider import QRangeSlider


class _GenericSlider(QSlider):
    valueChanged = Signal(float)  # type: ignore
    sliderMoved = Signal(float)  # type: ignore
    rangeChanged = Signal(float, float)  # type: ignore

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._minimum = 0.0
        self._maximum = 99.0
        self._pageStep = 10.0
        self._value = 0.0
        self._position = 0.0
        self._singleStep = 1.0
        self._offsetAccumulated = 0.0
        self._blocktracking = False
        self._tickInterval = 0
        self._pressedControl = QStyle.SubControl.SC_None
        self._hoverControl = QStyle.SubControl.SC_None
        self._hoverRect = QRect()
        self._clickOffset = 0
        self.setAttribute(Qt.WA_Hover)

        # for keyboard nav
        self._repeatMultiplier = 1  # TODO
        # for wheel nav
        self._offset_accum = 0.0
        # fraction of total range to scroll when holding Ctrl while scrolling
        self._control_fraction = 0.04

    def value(self) -> float:  # type: ignore
        return self._value

    def setValue(self, value: float) -> None:
        value = self._bound(value)
        if self._value == value and self._position == value:
            return
        self._value = value
        if self._position != value:
            self._position = value
            if self.isSliderDown():
                self.sliderMoved.emit(self._position)  # type: ignore
        self.sliderChange(QAbstractSlider.SliderValueChange)
        self.valueChanged.emit(value)  # type: ignore

    def sliderPosition(self) -> float:  # type: ignore
        return self._position

    def setSliderPosition(self, position: float) -> None:
        position = self._bound(position)
        if position == self._position:
            return
        self._position = position
        if not self.hasTracking():
            self.update()
        if self.isSliderDown():
            self.sliderMoved.emit(position)  # type: ignore
        if self.hasTracking() and not self._blocktracking:
            self.triggerAction(QAbstractSlider.SliderMove)

    def singleStep(self) -> float:  # type: ignore
        return self._singleStep

    def setSingleStep(self, step: float) -> None:
        if step != self._singleStep:
            self._setSteps(step, self._pageStep)

    def pageStep(self) -> float:  # type: ignore
        return self._pageStep

    def setPageStep(self, step: float) -> None:
        if step != self._pageStep:
            self._setSteps(self._singleStep, step)

    def _setSteps(self, single: float, page: float):
        self._singleStep = single
        self._pageStep = page
        self.sliderChange(QAbstractSlider.SliderStepsChange)

    def minimum(self) -> float:  # type: ignore
        return self._minimum

    def setMinimum(self, min: float) -> None:
        self.setRange(min, max(self._maximum, min))

    def maximum(self) -> float:  # type: ignore
        return self._maximum

    def setMaximum(self, max: float) -> None:
        self.setRange(min(self._minimum, max), max)

    def setRange(self, min: float, max_: float) -> None:
        oldMin, self._minimum = self._minimum, min
        oldMax, self._maximum = self._maximum, max(min, max_)

        if oldMin != self._minimum or oldMax != self._maximum:
            self.sliderChange(QAbstractSlider.SliderRangeChange)
            self.rangeChanged.emit(self._minimum, self._maximum)  # type: ignore
            self.setValue(self._value)  # re-bound

    def tickInterval(self) -> float:  # type: ignore
        return self._tickInterval

    def setTickInterval(self, ts: float) -> None:
        self._tickInterval = max(0, ts)  # type: ignore
        self.update()

    def triggerAction(self, action: QAbstractSlider.SliderAction) -> None:
        self._blocktracking = True
        # other actions here
        self.actionTriggered.emit(action)
        self._blocktracking = False
        self.setValue(self._position)

    def initStyleOption(self, option: QStyleOptionSlider) -> None:
        if not option:
            return

        option.initFrom(self)
        option.subControls = QStyle.SubControl.SC_None
        option.activeSubControls = QStyle.SubControl.SC_None
        option.orientation = self.orientation()
        option.tickPosition = self.tickPosition()
        option.upsideDown = (
            self.invertedAppearance() != (option.direction == Qt.RightToLeft)
            if self.orientation() == Qt.Horizontal
            else not self.invertedAppearance()
        )
        option.direction = Qt.LeftToRight  # we use the upsideDown option instead
        # option.sliderValue = self._value  # type: ignore
        # option.singleStep = self._singleStep  # type: ignore
        if self.orientation() == Qt.Horizontal:
            option.state |= QStyle.State_Horizontal
        self._fixStyleOption(option)

    def _fixStyleOption(self, option):
        # scale style option to integer space
        _max = 10000
        option.minimum = 0
        option.maximum = _max
        _range = self._maximum - self._minimum
        option.sliderPosition = (self._position - self._minimum) / _range * _max  # type: ignore
        option.sliderValue = (self._value - self._minimum) / _range * _max  # type: ignore
        option.tickInterval = self._tickInterval / _range * _max  # type: ignore
        option.pageStep = self._pageStep / _range * _max  # type: ignore
        option.singleStep = self._singleStep / _range * _max  # type: ignore

    def _bound(self, value: float) -> float:
        return max(self._minimum, min(self._maximum, value))

    def event(self, ev: QEvent) -> bool:
        is_hover = ev.type() in (QEvent.HoverEnter, QEvent.HoverLeave, QEvent.HoverMove)
        if is_hover and hasattr(ev, "pos"):
            self._updateHoverControl(ev.pos())
        return super().event(ev)

    def _updateHoverControl(self, pos: QPoint) -> bool:
        lastHoverRect = self._hoverRect
        lastHoverControl = self._hoverControl
        doesHover = self.testAttribute(Qt.WA_Hover)
        if lastHoverControl != self._newHoverControl(pos) and doesHover:
            self.update(lastHoverRect)
            self.update(self._hoverRect)
            return True

        return not doesHover

    def _newHoverControl(self, pos: QPoint) -> QStyle.SubControl:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.subControls = QStyle.SC_All

        handleRect = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
        )
        grooveRect = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self
        )
        tickmarksRect = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderTickmarks, self
        )

        if handleRect.contains(pos):
            self._hoverRect = handleRect
            self._hoverControl = QStyle.SC_SliderHandle
        elif grooveRect.contains(pos):
            self._hoverRect = grooveRect
            self._hoverControl = QStyle.SC_SliderGroove
        elif tickmarksRect.contains(pos):
            self._hoverRect = tickmarksRect
            self._hoverControl = QStyle.SC_SliderTickmarks
        else:
            self._hoverRect = QRect()
            self._hoverControl = QStyle.SC_None
        return self._hoverControl

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._minimum == self._maximum or ev.buttons() ^ ev.button():
            ev.ignore()
            return

        ev.accept()
        # FIXME: why not working on other styles?
        # set_buttons = self.style().styleHint(QStyle.SH_Slider_AbsoluteSetButtons)
        set_buttons = Qt.LeftButton | Qt.MiddleButton

        # If the mouse button used is allowed to set the value
        if ev.buttons() & set_buttons == ev.button():
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)

            sliderRect = self.style().subControlRect(
                QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
            )
            center = sliderRect.center() - sliderRect.topLeft()
            self.setSliderPosition(
                self._pixelPosToRangeValue(self._pick(ev.pos() - center))
            )
            self.triggerAction(QSlider.SliderMove)
            self.setRepeatAction(QSlider.SliderNoAction)
            self._pressedControl = QStyle.SC_SliderHandle
            self.update()
        # elif: deal with PageSetButtons
        else:
            ev.ignore()

        if self._pressedControl == QStyle.SC_SliderHandle:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            self.setRepeatAction(QSlider.SliderNoAction)
            sr = self.style().subControlRect(
                QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
            )
            self._clickOffset = self._pick(ev.pos() - sr.topLeft())
            self.update(sr)
            self.setSliderDown(True)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._pressedControl != QStyle.SC_SliderHandle:
            ev.ignore()
            return

        ev.accept()
        newPosition = self._pixelPosToRangeValue(
            self._pick(ev.pos()) - self._clickOffset
        )

        self.setSliderPosition(newPosition)

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self._pressedControl == QStyle.SubControl.SC_None or ev.buttons():
            ev.ignore()
            return

        ev.accept()
        oldPressed = QStyle.SubControl(self._pressedControl)
        self._pressedControl = QStyle.SubControl.SC_None
        self.setRepeatAction(QSlider.SliderNoAction)
        if oldPressed == QStyle.SubControl.SC_SliderHandle:
            self.setSliderDown(False)
        self.update()

    def paintEvent(self, ev: QtGui.QPaintEvent) -> None:
        p = QStylePainter(self)
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderHandle
        if opt.tickPosition != QSlider.NoTicks:
            opt.subControls |= QStyle.SC_SliderTickmarks
        if self._pressedControl:
            opt.activeSubControls = self._pressedControl
            opt.state |= QStyle.State_Sunken
        else:
            opt.activeSubControls = self._hoverControl

        p.drawComplexControl(QStyle.CC_Slider, opt)

    def _pick(self, pt: QPoint) -> int:
        return pt.x() if self.orientation() == Qt.Horizontal else pt.y()

    # from QSliderPrivate.pixelPosToRangeValue
    def _pixelPosToRangeValue(self, pos: int) -> float:
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        gr = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self
        )
        sr = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
        )

        if self.orientation() == Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
        return _sliderValueFromPosition(
            self._minimum,
            self._maximum,
            pos - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown,
        )

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
        steps_to_scroll = 0
        pg_step = self._pageStep

        # in Qt scrolling to the right gives negative values.
        if orientation == Qt.Horizontal:
            delta *= -1
        offset = delta / 120
        if modifiers & Qt.ShiftModifier:
            # Scroll one page regardless of delta:
            steps_to_scroll = _qbound(-pg_step, pg_step, offset * pg_step)
            self._offset_accum = 0
        elif modifiers & Qt.ControlModifier:
            _range = self._maximum - self._minimum
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
            steps_to_scroll = _qbound(-pg_step, pg_step, self._offset_accum)

            self._offset_accum -= self._offset_accum

            if steps_to_scroll == 0:
                # We moved less than a line, but might still have accumulated partial
                # scroll, unless we already are at one of the ends.
                effective_offset = self._offset_accum
                if self.invertedControls():
                    effective_offset *= -1
                if effective_offset > 0 and self._value < self._maximum:
                    return True
                if effective_offset < 0 and self._value < self._minimum:
                    return True
                self._offset_accum = 0
                return False

        if self.invertedControls():
            steps_to_scroll *= -1

        prevValue = self._value
        self._position = self._bound(self._overflowSafeAdd(steps_to_scroll))
        self.triggerAction(QSlider.SliderMove)

        if prevValue == self._value:
            self._offset_accum = 0
            return False
        return True

    def _effectiveSingleStep(self) -> float:
        return self._singleStep * self._repeatMultiplier

    def _overflowSafeAdd(self, add: float) -> float:
        newValue = self._value + add
        if add > 0 and newValue < self._value:
            newValue = self._maximum
        elif add < 0 and newValue > self._value:
            newValue = self._minimum
        return newValue


def _qbound(min_: float, max_: float, value: float) -> float:
    """Return value bounded by min_ and max_."""
    return max(min_, min(max_, value))


def _sliderValueFromPosition(
    min: float, max: float, position: int, span: int, upsideDown: bool = False
) -> float:
    """Converts the given pixel `position` to a value.
    0 maps to the `min` parameter, `span` maps to `max` and other values are
    distributed evenly in-between.

    By default, this function assumes that the maximum value is on the right
    for horizontal items and on the bottom for vertical items. Set the
    `upsideDown` parameter to True to reverse this behavior.
    """

    if span <= 0 or position <= 0:
        return max if upsideDown else min
    if position >= span:
        return min if upsideDown else max
    range = max - min
    tmp = min + position * range / span
    return max - tmp if upsideDown else tmp + min


class QDoubleSlider(_GenericSlider):
    pass


class QDoubleRangeSlider:
    pass


# class QDoubleRangeSlider(QRangeSlider, _GenericSlider):

#     rangeChanged = Signal(float, float)

#     def value(self):
#         """Get current value of the widget as a tuple of integers."""
#         return tuple(float(i) for i in self._value)
