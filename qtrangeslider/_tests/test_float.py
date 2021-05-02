import pytest

from qtrangeslider import QDoubleSlider


def test_double_slider(qtbot):
    ds = QDoubleSlider()
    qtbot.addWidget(ds)
    ds.setMinimum(10)
    ds.setMaximum(99)
    ds.setValue(40)
    ds.setSingleStep(1)
    assert ds.minimum() == 10
    assert ds.maximum() == 99
    assert ds.value() == 40.0
    assert ds.singleStep() == 1

    ds.setDecimals(2)
    assert ds.value() == 40.0
    assert isinstance(ds.value(), float)

    ds.setValue(42.3456)
    assert ds.value() == 42.34  # because of decimals
    assert isinstance(ds.value(), float)

    ds.setDecimals(4)
    assert ds.value() == 42.34
    assert ds.minimum() == 10
    assert ds.maximum() == 99
    assert ds.singleStep() == 1

    ds.setDecimals(6)
    assert ds.value() == 42.34
    assert ds.minimum() == 10
    assert ds.maximum() == 99
    assert ds.singleStep() == 1

    with pytest.raises(OverflowError) as err:
        ds.setDecimals(8)
        assert "open a feature request" in str(err)

    assert ds.value() == 42.34
    assert ds.minimum() == 10
    assert ds.maximum() == 99
    assert ds.singleStep() == 1


def test_double_slider_small(qtbot):
    ds = QDoubleSlider()
    qtbot.addWidget(ds)
    ds.setMaximum(1)
    ds.setDecimals(8)
    ds.setValue(0.5)
    assert ds.minimum() == 0
    assert ds.maximum() == 1
    assert ds.value() == 0.5

    ds.setValue(0.72644353)
    assert ds.value() == 0.72644353


def test_double_slider_big(qtbot):
    ds = QDoubleSlider()
    qtbot.addWidget(ds)
    ds.setDecimals(-6)
    assert ds._multiplier == 1e-6
    assert ds.decimals() == -6
    ds.setMaximum(5e14)
    assert ds.minimum() == 0
    assert ds.maximum() == 5e14
    assert ds.value() == 0
    ds.setValue(1.432e10)
    assert ds.value() == 1.432e10
