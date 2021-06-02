import pytest

from qtrangeslider import QRangeSlider
from qtrangeslider._generic_qslider import _GenericSlider
from qtrangeslider.qtcompat.QtCore import QEvent, QPoint, QPointF, Qt
from qtrangeslider.qtcompat.QtGui import QMouseEvent, QWheelEvent


def _mouse_event(pos=QPointF(), type_=QEvent.MouseMove):
    """Create a mouse event of `type_` at `pos`."""
    return QMouseEvent(type_, QPointF(pos), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)


def _wheel_event(arc):
    """Create a wheel event with `arc`."""
    return QWheelEvent(
        QPointF(),
        QPointF(),
        QPoint(arc, arc),
        QPoint(arc, arc),
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollBegin,
        False,
        Qt.MouseEventSynthesizedByQt,
    )


def _linspace(start, stop, n):
    h = (stop - start) / (n - 1)
    for i in range(n):
        yield start + h * i


@pytest.fixture(params=[Qt.Horizontal, Qt.Vertical])
def orientation(request):
    return request.param


START_MI_MAX_VAL = (0, 99, (0, 99))
TEST_SLIDERS = [_GenericSlider, QRangeSlider]
RANGE_TYPES = {QRangeSlider}


def _assert_value_in_range(sld):
    val = sld.value()
    if isinstance(val, (int, float)):
        val = (val,)
    assert all(sld.minimum() <= v <= sld.maximum() for v in val)


@pytest.fixture(params=TEST_SLIDERS)
def sld(request, qtbot, orientation):
    Cls = request.param
    slider = Cls(orientation)
    slider.setRange(*START_MI_MAX_VAL[:2])
    slider.setValue(START_MI_MAX_VAL[2])
    qtbot.addWidget(slider)
    assert (slider.minimum(), slider.maximum(), slider.value()) == START_MI_MAX_VAL

    # def assert_val_type():
    #     type_ = float
    #     if Cls in RANGE_TYPES:
    #         assert all([isinstance(i, type_) for i in slider.value()])  # sourcery skip
    #     else:
    #         assert isinstance(slider.value(), type_)

    def assert_val_eq(val):
        assert slider.value() == val if Cls in RANGE_TYPES else val[0]

    def _cb_val_is(expect):
        """Use in check_params_cbs to assert that valueChanged is called as expected.

        truncates non-range types to the first value
        """

        def check_emitted_values(values):
            return values == expect if Cls in RANGE_TYPES else expect[0]

        return check_emitted_values

    # slider.assert_val_type = assert_val_type
    # slider.assert_val_eq = assert_val_eq
    slider.cb_val_is = _cb_val_is

    if Cls not in RANGE_TYPES:
        superset = slider.setValue

        def _safe_set(val):
            superset(val[0] if isinstance(val, tuple) else val)

        slider.setValue = _safe_set

    _assert_value_in_range(slider)
    yield slider
    _assert_value_in_range(slider)


def called_with(*expected_result):
    """Use in check_params_cbs to assert that a callback is called as expected.

    e.g. `called_with(20, 50)` returns a callback that checks that the callback
    is called with the arguments (20, 50)
    """

    def check_emitted_values(*values):
        return values == expected_result

    return check_emitted_values


def test_change_floatslider_range(sld: _GenericSlider, qtbot):
    BOTH = [sld.rangeChanged, sld.valueChanged]

    for signals, checks, funcname, args in [
        (BOTH, [called_with(10, 99), sld.cb_val_is((10, 99))], "setMinimum", (10,)),
        ([sld.rangeChanged], [called_with(10, 90)], "setMaximum", (90,)),
        (BOTH, [called_with(20, 40), sld.cb_val_is((20, 40))], "setRange", (20, 40)),
        ([sld.valueChanged], [sld.cb_val_is((30, 38))], "setValue", ((30, 38),)),
        (BOTH, [called_with(20, 25), sld.cb_val_is((25, 25))], "setMaximum", (25,)),
        ([sld.valueChanged], [sld.cb_val_is((23, 24))], "setValue", ((23, 24),)),
    ]:
        with qtbot.waitSignals(signals, check_params_cbs=checks):
            getattr(sld, funcname)(*args)
        _assert_value_in_range(sld)


def test_float_values(sld: _GenericSlider, qtbot):
    for signals, checks, funcname, args in [
        ([sld.rangeChanged], [called_with(0.1, 0.9)], "setRange", (0.1, 0.9)),
        ([sld.valueChanged], [sld.cb_val_is((0.4, 0.6))], "setValue", ((0.4, 0.6),)),
        ([sld.valueChanged], [sld.cb_val_is((0.1, 0.9))], "setValue", ((0, 1.9),)),
    ]:
        with qtbot.waitSignals(signals, check_params_cbs=checks):
            getattr(sld, funcname)(*args)
        _assert_value_in_range(sld)


# def test_ticks(gslider: _GenericSlider, qtbot):
#     gslider.setTickInterval(0.3)
#     assert gslider.tickInterval() == 0.3
#     gslider.setTickPosition(gslider.TicksAbove)
#     gslider.show()


# def test_show(gslider, qtbot):
#     gslider.show()


# def test_press_move_release(gslider: _GenericSlider, qtbot):
#     assert gslider._pressedControl == QStyle.SubControl.SC_None

#     opt = QStyleOptionSlider()
#     gslider.initStyleOption(opt)
#     style = gslider.style()
#     hrect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle)
#     handle_pos = gslider.mapToGlobal(hrect.center())

#     with qtbot.waitSignal(gslider.sliderPressed):
#         qtbot.mousePress(gslider, Qt.LeftButton, pos=handle_pos)

#     assert gslider._pressedControl == QStyle.SubControl.SC_SliderHandle

#     with qtbot.waitSignals([gslider.sliderMoved, gslider.valueChanged]):
#         shift = QPoint(0, -8) if gslider.orientation() == Qt.Vertical else QPoint(8, 0)
#         gslider.mouseMoveEvent(_mouse_event(handle_pos + shift))

#     with qtbot.waitSignal(gslider.sliderReleased):
#         qtbot.mouseRelease(gslider, Qt.LeftButton, pos=handle_pos)

#     assert gslider._pressedControl == QStyle.SubControl.SC_None

#     gslider.show()
#     with qtbot.waitSignal(gslider.sliderPressed):
#         qtbot.mousePress(gslider, Qt.LeftButton, pos=handle_pos)


# def test_hover(gslider: _GenericSlider):

#     opt = QStyleOptionSlider()
#     gslider.initStyleOption(opt)
#     style = gslider.style()
#     hrect = style.subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle)
#     handle_pos = QPointF(gslider.mapToGlobal(hrect.center()))

#     assert gslider._hoverControl == QStyle.SubControl.SC_None

#     gslider.event(QHoverEvent(QEvent.HoverEnter, handle_pos, QPointF()))
#     assert gslider._hoverControl == QStyle.SubControl.SC_SliderHandle

#     gslider.event(QHoverEvent(QEvent.HoverLeave, QPointF(-1000, -1000), handle_pos))
#     assert gslider._hoverControl == QStyle.SubControl.SC_None


# def test_wheel(gslider: _GenericSlider, qtbot):
#     with qtbot.waitSignal(gslider.valueChanged):
#         gslider.wheelEvent(_wheel_event(120))

#     gslider.wheelEvent(_wheel_event(0))


# def test_position(gslider: _GenericSlider, qtbot):
#     gslider.setSliderPosition(21.2)
#     assert gslider.sliderPosition() == 21.2


# def test_steps(gslider: _GenericSlider, qtbot):
#     gslider.setSingleStep(0.1)
#     assert gslider.singleStep() == 0.1

#     gslider.setSingleStep(1.5e20)
#     assert gslider.singleStep() == 1.5e20

#     gslider.setPageStep(0.2)
#     assert gslider.pageStep() == 0.2

#     gslider.setPageStep(1.5e30)
#     assert gslider.pageStep() == 1.5e30


# @pytest.mark.parametrize("mag", list(range(4, 37, 4)) + list(range(-4, -37, -4)))
# def test_slider_extremes(gslider: _GenericSlider, mag, qtbot):
#     _mag = 10 ** mag
#     with qtbot.waitSignal(gslider.rangeChanged):
#         gslider.setRange(-_mag, _mag)
#     for i in _linspace(-_mag, _mag, 10):
#         gslider.setValue(i)
#         assert math.isclose(gslider.value(), i, rel_tol=1e-8)
