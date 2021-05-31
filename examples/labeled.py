from qtrangeslider._labeled import (
    QLabeledDoubleRangeSlider,
    QLabeledDoubleSlider,
    QLabeledRangeSlider,
    QLabeledSlider,
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

ORIENTATION = Qt.Horizontal

sld0 = QLabeledSlider(ORIENTATION)
sld0.setRange(0, 500)
sld0.setValue(300)


sld1 = QLabeledDoubleSlider(ORIENTATION)
sld1.setRange(0, 1)
sld1.setValue(0.5)
sld1.setSingleStep(0.1)

sld2 = QLabeledRangeSlider(ORIENTATION)
sld2.setValue((20, 60))

sld3 = QLabeledDoubleRangeSlider(ORIENTATION)
sld3.setRange(0, 1)
sld3.setValue((0.2, 0.7))


w = QWidget()
w.setLayout(QVBoxLayout() if ORIENTATION == Qt.Horizontal else QHBoxLayout())


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

w.show()
w.resize(500, 150)
app.exec_()
