import math

import pyautogui
import pytest

from qtrangeslider import QDoubleSlider
from qtrangeslider.qtcompat.QtCore import QPoint, Qt, QVariantAnimation
from qtrangeslider.qtcompat.QtWidgets import QStyle, QStyleOptionSlider


@pytest.fixture
def dslider(qtbot):
    slider = QDoubleSlider()
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


def _linspace(start, stop, n):
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


@pytest.mark.parametrize("mag", list(range(0, 65, 4)))
def test_float_extremes(dslider, mag, qtbot):
    for _mag in (2 ** mag, 2 ** -mag):
        with qtbot.waitSignal(dslider.rangeChanged):
            dslider.setRange(-_mag, _mag)
        for i in _linspace(-_mag, _mag, 10):
            dslider.setValue(i)
            assert math.isclose(dslider.value(), i, rel_tol=1e-8)


def test_slider_move_signals(dslider, qtbot):

    dslider.setValue(10)
    dslider.show()
    qtbot.waitUntil(dslider.isVisible)

    opt = QStyleOptionSlider()
    dslider.initStyleOption(opt)
    style = dslider.style()
    hrect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle)

    start_pos = dslider.mapToGlobal(hrect.center())
    end_pos = start_pos + QPoint(0, -30)

    with qtbot.waitSignal(dslider.sliderPressed):
        qtbot.mousePress(dslider, Qt.LeftButton, pos=start_pos)

    pyautogui.moveTo(start_pos.x(), start_pos.y())
    pyautogui.mouseDown(button="left")

    animation = QVariantAnimation(startValue=start_pos, endValue=end_pos, duration=50)
    animation.valueChanged.connect(
        lambda v: pyautogui.dragTo(v.x(), v.y(), button="left")
    )

    with qtbot.waitSignals(
        [
            dslider.sliderMoved,
            dslider.valueChanged,
            dslider.sliderReleased,
            animation.finished,
        ],
        timeout=2000,
    ):
        animation.start()
