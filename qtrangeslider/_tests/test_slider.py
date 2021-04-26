import pytest

from qtrangeslider import QRangeSlider
from qtrangeslider.qtcompat.QtCore import Qt


@pytest.mark.parametrize("orientation", ["Horizontal", "Vertical"])
def test_basic(qtbot, orientation):
    rs = QRangeSlider(getattr(Qt, orientation))
    qtbot.addWidget(rs)


def test_drag(qtbot, qapp):
    rs = QRangeSlider(Qt.Horizontal)
    rs.setMouseTracking(True)
    qtbot.addWidget(rs)
    rs.show()
    rs.sliderMoved.connect(lambda e: print("moved", e))

    opt = rs._getStyleOption()
    pos = rs._handleRects(opt, 0).center()
    qtbot.mousePress(rs, Qt.LeftButton, pos=pos)
    assert rs._pressedControl == ("handle", 0)

    for _ in range(15):
        pos.setX(pos.x() + 2)
        qtbot.mouseMove(rs.window(), pos)
    qtbot.mouseRelease(rs, Qt.LeftButton)

    assert rs.value() == (35, 80)
    assert rs._pressedControl == rs._NULL_CTRL

    opt = rs._getStyleOption()
    pos = rs._handleRects(opt, 1).center()
    qtbot.mousePress(rs, Qt.LeftButton, pos=pos)
    assert rs._pressedControl == ("handle", 1)

    for _ in range(15):
        pos.setX(pos.x() - 2)
        qtbot.mouseMove(rs.window(), pos)
    qtbot.mouseRelease(rs, Qt.LeftButton)

    assert rs.value() == (35, 65)
    assert rs._pressedControl == rs._NULL_CTRL
