from qtrangeslider import (
    QDoubleRangeSlider,
    QDoubleSlider,
    QLabeledDoubleRangeSlider,
    QLabeledDoubleSlider,
)
from qtrangeslider.qtcompat.QtCore import Qt
from qtrangeslider.qtcompat.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

app = QApplication([])
ORIENTATION = Qt.Vertical

sld0 = QDoubleSlider(ORIENTATION)
sld0.setValue(50)
sld0.setPageStep(1)

sld1 = QLabeledDoubleSlider(ORIENTATION)
sld1.setRange(0, 1)
sld1.setValue(0.5)
sld1.setSingleStep(0.01)

sld2 = QDoubleRangeSlider(ORIENTATION)
sld2.setRange(0, 1)
sld2.setValue((0.2, 0.8))
sld2.setSingleStep(0.01)

sld3 = QLabeledDoubleRangeSlider(ORIENTATION)


w = QWidget()
w.setLayout(QVBoxLayout() if ORIENTATION == Qt.Horizontal else QHBoxLayout())
w.show()
w.resize(600, 300)

for sld in (sld0, sld1, sld2, sld3):
    w.layout().addWidget(QLabel(sld.__class__.__name__))
    w.layout().addWidget(sld)

    for sig in (
        "valueChanged",
        "rangeChanged",
        "sliderMoved",
        "sliderPressed",
        "sliderReleased",
    ):

        def _print(e=None, sld=sld, sig=sig):
            print(f"{sld.__class__.__name__}.{sig}", e or "")

        getattr(sld, sig).connect(_print)

app.exec_()
