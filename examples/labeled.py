from qtrangeslider._labeled import (
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
qlrs.setValue((100, 400))


w.setLayout(QVBoxLayout())
w.layout().addWidget(qls)
w.layout().addWidget(qlds)
w.layout().addWidget(qlrs)
w.show()
w.resize(500, 150)
app.exec_()
