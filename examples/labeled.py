from qtrangeslider._labeled import QLabeledRangeSlider
from qtrangeslider.qtcompat.QtCore import Qt
from qtrangeslider.qtcompat.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget

app = QApplication([])

w = QWidget()
sld = QLabeledRangeSlider()

sld.setRange(0, 500)
sld.setValue((100, 400))
w.setLayout(QVBoxLayout())
w.layout().addWidget(sld)
w.layout().addWidget(QSlider(Qt.Horizontal))
w.show()
w.resize(500, 150)
app.exec_()
