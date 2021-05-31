from qtrangeslider import QRangeSlider
from qtrangeslider._float_slider import QDoubleRangeSlider, QDoubleSlider
from qtrangeslider.qtcompat.QtCore import Qt
from qtrangeslider.qtcompat.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

app = QApplication([])

w = QWidget()

sld1 = QDoubleSlider(Qt.Horizontal)
sld2 = QDoubleRangeSlider(Qt.Horizontal)
sld3 = QRangeSlider(Qt.Horizontal)

sld1.valueChanged.connect(lambda e: print("doubslider valuechanged", e))
sld1.setValue(40)

sld2.setMaximum(1)
sld2.setValue((0.2, 0.8))
sld2.setSingleStep(0.01)
sld2.valueChanged.connect(lambda e: print("valueChanged", e))
sld2.sliderMoved.connect(lambda e: print("sliderMoved", e))
sld2.rangeChanged.connect(lambda e, f: print("rangeChanged", (e, f)))

w.setLayout(QVBoxLayout())
w.layout().addWidget(sld1)
w.layout().addWidget(QLabel("double rangeslider"))
w.layout().addWidget(sld2)
w.layout().addWidget(QLabel("rangeslider"))
w.layout().addWidget(sld3)
w.show()
w.resize(500, 150)
app.exec_()
