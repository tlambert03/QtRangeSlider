from qtrangeslider._labeled import (
    QLabeledDoubleRangeSlider,
    QLabeledDoubleSlider,
    QLabeledRangeSlider,
    QLabeledSlider,
)
from qtrangeslider.qtcompat.QtCore import Qt
from qtrangeslider.qtcompat.QtWidgets import QApplication, QVBoxLayout, QWidget

app = QApplication([])

w = QWidget()
qls = QLabeledSlider(Qt.Horizontal)
qls.valueChanged.connect(lambda e: print("qls valueChanged", e))
qls.setRange(0, 500)
qls.setValue(300)


qlds = QLabeledDoubleSlider(Qt.Horizontal)
qlds.valueChanged.connect(lambda e: print("qlds valueChanged", e))
qlds.setRange(0, 1)
qlds.setValue(0.5)

qlrs = QLabeledRangeSlider()
qlrs.valueChanged.connect(lambda e: print("qlrs valueChanged", e))
qlrs.setValue((20, 60))

qldrs = QLabeledDoubleRangeSlider()
qldrs.valueChanged.connect(lambda e: print("qlrs valueChanged", e))
qldrs.setRange(0, 1)
qldrs.setValue((0.2, 0.7))


w.setLayout(QVBoxLayout())
w.layout().addWidget(qls)
w.layout().addWidget(qlds)
w.layout().addWidget(qlrs)
w.layout().addWidget(qldrs)
w.show()
w.resize(500, 150)
app.exec_()
