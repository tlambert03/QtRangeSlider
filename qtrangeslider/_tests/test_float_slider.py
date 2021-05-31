import math

import pytest

from qtrangeslider._generic_qslider import QDoubleSlider
from qtrangeslider.qtcompat.QtCore import QEvent, QPoint, QPointF, Qt
from qtrangeslider.qtcompat.QtGui import QHoverEvent, QMouseEvent, QWheelEvent
from qtrangeslider.qtcompat.QtWidgets import QStyle, QStyleOptionSlider


@pytest.fixture(params=[Qt.Horizontal, Qt.Vertical])
def dslider(qtbot, request):
    slider = QDoubleSlider(request.param)
    qtbot.addWidget(slider)
    assert slider.value() == 0
    assert slider.minimum() == 0
    assert slider.maximum() == 99
    return slider


def test_change_floatslider_range(dslider: QDoubleSlider, qtbot):
    with qtbot.waitSignals([dslider.rangeChanged, dslider.valueChanged]):
        dslider.setMinimum(10)

    assert dslider.value() == 10 == dslider.minimum()
    assert dslider.maximum() == 99

    with qtbot.waitSignal(dslider.rangeChanged):
        dslider.setMaximum(90)
    assert dslider.value() == 10 == dslider.minimum()
    assert dslider.maximum() == 90

    with qtbot.waitSignals([dslider.rangeChanged, dslider.valueChanged]):
        dslider.setRange(20, 40)
    assert dslider.value() == 20 == dslider.minimum()
    assert dslider.maximum() == 40

    with qtbot.waitSignal(dslider.valueChanged):
        dslider.setValue(30)
    assert dslider.value() == 30

    with qtbot.waitSignals([dslider.rangeChanged, dslider.valueChanged]):
        dslider.setMaximum(25)
    assert dslider.value() == 25 == dslider.maximum()
    assert dslider.minimum() == 20


def test_float_values(dslider: QDoubleSlider, qtbot):
    with qtbot.waitSignal(dslider.rangeChanged):
        dslider.setRange(0.25, 0.75)
    assert dslider.minimum() == 0.25
    assert dslider.maximum() == 0.75

    with qtbot.waitSignal(dslider.valueChanged):
        dslider.setValue(0.55)
    assert dslider.value() == 0.55

    with qtbot.waitSignal(dslider.valueChanged):
        dslider.setValue(1.55)
    assert dslider.value() == 0.75 == dslider.maximum()


def test_ticks(dslider: QDoubleSlider, qtbot):
    dslider.setTickInterval(0.3)
    assert dslider.tickInterval() == 0.3
    dslider.setTickPosition(dslider.TicksAbove)
    dslider.show()


def test_show(dslider: QDoubleSlider, qtbot):
    dslider.show()


def test_press_move_release(dslider: QDoubleSlider, qtbot, qapp):
    assert dslider._pressedControl == QStyle.SubControl.SC_None

    opt = QStyleOptionSlider()
    dslider.initStyleOption(opt)
    style = dslider.style()
    hrect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle)
    handle_pos = dslider.mapToGlobal(hrect.center())

    with qtbot.waitSignal(dslider.sliderPressed):
        qtbot.mousePress(dslider, Qt.LeftButton, pos=handle_pos)

    assert dslider._pressedControl == QStyle.SubControl.SC_SliderHandle
    # dslider.show()
    # qapp.processEvents()
    # dslider.hide()

    with qtbot.waitSignals([dslider.sliderMoved, dslider.valueChanged]):
        shift = QPoint(0, -8) if dslider.orientation() == Qt.Vertical else QPoint(8, 0)
        ev = QMouseEvent(
            QEvent.MouseMove,
            handle_pos + shift,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        dslider.mouseMoveEvent(ev)

    with qtbot.waitSignal(dslider.sliderReleased):
        qtbot.mouseRelease(dslider, Qt.LeftButton, pos=handle_pos)

    assert dslider._pressedControl == QStyle.SubControl.SC_None

    dslider.show()
    with qtbot.waitSignal(dslider.sliderPressed):
        qtbot.mousePress(dslider, Qt.LeftButton, pos=handle_pos)


def test_hover(dslider: QDoubleSlider):

    opt = QStyleOptionSlider()
    dslider.initStyleOption(opt)
    style = dslider.style()
    hrect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle)
    handle_pos = dslider.mapToGlobal(hrect.center())

    assert dslider._hoverControl == QStyle.SubControl.SC_None

    dslider.event(QHoverEvent(QEvent.HoverEnter, handle_pos, QPointF()))
    assert dslider._hoverControl == QStyle.SubControl.SC_SliderHandle

    dslider.event(QHoverEvent(QEvent.HoverLeave, QPointF(-1000, -1000), handle_pos))
    assert dslider._hoverControl == QStyle.SubControl.SC_None


def test_wheel(dslider: QDoubleSlider, qtbot, qapp):
    ev = QWheelEvent(
        QPointF(),
        QPointF(),
        QPoint(-120, -120),
        QPoint(-120, -120),
        12,
        Qt.Vertical,
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollBegin,
        False,
        Qt.MouseEventSynthesizedByQt,
    )
    with qtbot.waitSignal(dslider.valueChanged):
        dslider.wheelEvent(ev)

    ev = QWheelEvent(
        QPointF(),
        QPointF(),
        QPoint(),
        QPoint(),
        12,
        Qt.Vertical,
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollUpdate,
        False,
        Qt.MouseEventSynthesizedByQt,
    )
    dslider.wheelEvent(ev)


def test_position(dslider: QDoubleSlider, qtbot):
    dslider.setSliderPosition(21.2)
    assert dslider.sliderPosition() == 21.2


def test_steps(dslider: QDoubleSlider, qtbot):
    dslider.setSingleStep(0.1)
    assert dslider.singleStep() == 0.1

    dslider.setSingleStep(1.5e20)
    assert dslider.singleStep() == 1.5e20

    dslider.setPageStep(0.2)
    assert dslider.pageStep() == 0.2

    dslider.setPageStep(1.5e30)
    assert dslider.pageStep() == 1.5e30


def _linspace(start, stop, n):
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


@pytest.mark.parametrize("mag", list(range(4, 37, 4)) + list(range(-4, -37, -4)))
def test_slider_extremes(dslider, mag, qtbot):
    dslider.setRange(10, 20)
    _mag = 10 ** mag
    with qtbot.waitSignal(dslider.rangeChanged):
        dslider.setRange(-_mag, _mag)
    for i in _linspace(-_mag, _mag, 10):
        dslider.setValue(i)
        assert math.isclose(dslider.value(), i, rel_tol=1e-8)
