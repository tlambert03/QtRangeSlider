import pytest

from qtrangeslider import QRangeSlider
from qtrangeslider.qtcompat.QtCore import Qt


@pytest.mark.parametrize("orientation", ["Horizontal", "Vertical"])
def test_basic(qtbot, orientation):
    rs = QRangeSlider(getattr(Qt, orientation))
    qtbot.addWidget(rs)


def test_drag_handles(qtbot, qapp):
    rs = QRangeSlider(Qt.Horizontal)
    rs.setRange(0, 99)
    rs.setValue((20, 80))
    rs.setMouseTracking(True)
    qtbot.addWidget(rs)
    rs.show()

    # press the left handle
    opt = rs._getStyleOption()
    pos = rs._handleRects(opt, 0).center()
    with qtbot.waitSignal(rs.sliderPressed):
        qtbot.mousePress(rs, Qt.LeftButton, pos=pos)
    assert rs._pressedControl == ("handle", 0)

    # drag the left handle
    with qtbot.waitSignals([rs.sliderMoved] * 14):
        for _ in range(15):
            pos.setX(pos.x() + 2)
            qtbot.mouseMove(rs.window(), pos)

    with qtbot.waitSignal(rs.sliderReleased):
        qtbot.mouseRelease(rs, Qt.LeftButton)

    # check the values
    assert rs.value()[0] > 30
    assert rs._pressedControl == rs._NULL_CTRL

    # press the right handle
    pos = rs._handleRects(opt, 1).center()
    with qtbot.waitSignal(rs.sliderPressed):
        qtbot.mousePress(rs, Qt.LeftButton, pos=pos)
    assert rs._pressedControl == ("handle", 1)

    # drag the right handle
    with qtbot.waitSignals([rs.sliderMoved] * 14):
        for _ in range(15):
            pos.setX(pos.x() - 2)
            qtbot.mouseMove(rs.window(), pos)
    with qtbot.waitSignal(rs.sliderReleased):
        qtbot.mouseRelease(rs, Qt.LeftButton)

    # check the values
    assert rs.value()[1] < 70
    assert rs._pressedControl == rs._NULL_CTRL
