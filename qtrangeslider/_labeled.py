from enum import Enum
from functools import partial

from ._qrangeslider import QRangeSlider
from .qtcompat.QtCore import QEnum, QPoint, QSize, Qt, Signal
from .qtcompat.QtGui import QFontMetrics
from .qtcompat.QtWidgets import (
    QAbstractSlider,
    QHBoxLayout,
    QSlider,
    QSpinBox,
    QStyle,
    QStyleOptionSpinBox,
    QVBoxLayout,
    QWidget,
)


class LabelPosition(Enum):
    NoLabel = 0
    LabelsAbove = 1
    LabelsBelow = 2
    LabelsRight = 1
    LabelsLeft = 2


class QLabeledSlider(QAbstractSlider):
    def __init__(self, *args) -> None:
        parent = None
        orientation = Qt.Horizontal
        if len(args) == 2:
            orientation, parent = args
        elif args:
            if isinstance(args[0], QWidget):
                parent = args[0]
            else:
                orientation = args[0]

        super().__init__(parent)

        self._slider = QSlider()
        self._label = QSpinBox()
        self._label.setButtonSymbols(QSpinBox.NoButtons)
        self._label.setStyleSheet("background:transparent; border: 0;")

        self.valueChanged.connect(self._slider.setValue)
        self.valueChanged.connect(self._label.setValue)
        self.rangeChanged.connect(self._slider.setRange)
        self.rangeChanged.connect(self._label.setRange)

        self._slider.valueChanged.connect(self.setValue)
        self._label.editingFinished.connect(lambda: self.setValue(self._label.value()))
        self.setOrientation(orientation)

    def setOrientation(self, orientation):
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        self._slider.setOrientation(orientation)
        if orientation == Qt.Vertical:
            layout = QVBoxLayout()
            layout.addWidget(self._slider, alignment=Qt.AlignHCenter)
            layout.addWidget(self._label, alignment=Qt.AlignHCenter)
            self._label.setAlignment(Qt.AlignCenter)
            layout.setSpacing(1)
        else:
            layout = QHBoxLayout()
            layout.addWidget(self._slider)
            layout.addWidget(self._label)
            self._label.setAlignment(Qt.AlignRight)
            layout.setSpacing(10)

        old_layout = self.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class QLabeledRangeSlider(QAbstractSlider):
    valueChanged = Signal(tuple)

    LabelPosition = QEnum(LabelPosition)

    def __init__(self, *args) -> None:
        parent = None
        orientation = Qt.Horizontal
        if len(args) == 2:
            orientation, parent = args
        elif args:
            if isinstance(args[0], QWidget):
                parent = args[0]
            else:
                orientation = args[0]

        super().__init__(parent)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._handle_labels = []
        self._label_position = self.LabelPosition.LabelsAbove
        self._edges_show_range = False

        self._slider = QRangeSlider()
        self._min_label = SliderLabel(
            self._slider, alignment=Qt.AlignLeft, connect=self._min_label_edited
        )
        self._max_label = SliderLabel(
            self._slider, alignment=Qt.AlignRight, connect=self._max_label_edited
        )

        self._slider.valueChanged.connect(self._on_value_changed)
        self.rangeChanged.connect(self._on_range_changed)

        self._on_value_changed(self._slider.value())
        self._on_range_changed(self._slider.minimum(), self._slider.maximum())
        self.setOrientation(orientation)

    def _reposition_labels(self):
        if not self._handle_labels:
            return
        handle_rect = self._slider._handleRects(None, 0)
        label = self._handle_labels[0]
        if self.orientation() == Qt.Horizontal:
            if self._label_position == self.LabelPosition.LabelsBelow:
                shift = QPoint((label.width() / 2) - 1, -handle_rect.height() + 8)
            else:
                shift = QPoint((label.width() / 2) - 1, handle_rect.height() + 8)
        else:
            if self._label_position == self.LabelPosition.LabelsLeft:
                shift = QPoint(handle_rect.width() + 12, (label.height() / 2) - 1)
            else:
                shift = QPoint(-handle_rect.width() + 8, (label.height() / 2) - 1)

        for label, rect in zip(self._handle_labels, self._slider._handleRects()):
            pos = rect.center() - shift
            label.move(self._slider.mapToParent(pos))
            label.clearFocus()

    def _min_label_edited(self, val):
        if self._edges_show_range:
            self.setMinimum(val)
        else:
            v = list(self._slider.value())
            v[0] = val
            self.setValue(v)

    def _max_label_edited(self, val):
        if self._edges_show_range:
            self.setmaximum(val)
        else:
            v = list(self._slider.value())
            v[-1] = val
            self.setValue(v)

    def _on_value_changed(self, v):
        if not self._edges_show_range:
            self._min_label.setValue(v[0])
            self._max_label.setValue(v[-1])

        if len(v) != len(self._handle_labels):
            for lbl in self._handle_labels:
                lbl.setParent(None)
                lbl.deleteLater()
            self._handle_labels.clear()
            for n, val in enumerate(self._slider.value()):
                _cb = partial(self._slider._setSliderPositionAt, n)
                s = SliderLabel(self._slider, parent=self, connect=_cb)
                s.setValue(val)
                self._handle_labels.append(s)
        else:
            for val, label in zip(v, self._handle_labels):
                label.setValue(val)
        self._reposition_labels()

    def _on_range_changed(self, min, max):
        self._slider.setRange(min, max)
        for lbl in self._handle_labels:
            lbl.setRange(min, max)
        if self._edges_show_range:
            self._min_label.setValue(min)
            self._max_label.setValue(max)

    def value(self):
        return self._slider.value()

    def setValue(self, v: int) -> None:
        self._slider.setValue(v)
        self.sliderChange(QSlider.SliderValueChange)
        self.valueChanged.emit(tuple(self._slider.value()))

    def setOrientation(self, orientation):
        """Set orientation, value will be 'horizontal' or 'vertical'."""

        self._slider.setOrientation(orientation)
        if orientation == Qt.Vertical:
            layout = QVBoxLayout()
            layout.setSpacing(1)
            layout.addWidget(self._max_label)
            layout.addWidget(self._slider)
            layout.addWidget(self._min_label)
            # TODO: set margins based on label width
            if self._label_position == self.LabelPosition.LabelsLeft:
                marg = (30, 0, 0, 0)
            elif self._label_position == self.LabelPosition.NoLabel:
                marg = (0, 0, 0, 0)
            else:
                marg = (0, 0, 20, 0)
            layout.setAlignment(Qt.AlignCenter)
        else:
            layout = QHBoxLayout()
            layout.setSpacing(7)
            if self._label_position == self.LabelPosition.LabelsBelow:
                marg = (0, 0, 0, 25)
            elif self._label_position == self.LabelPosition.NoLabel:
                marg = (0, 0, 0, 0)
            else:
                marg = (0, 25, 0, 0)
            layout.addWidget(self._min_label)
            layout.addWidget(self._slider)
            layout.addWidget(self._max_label)

        # remove old layout
        old_layout = self.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        self.setLayout(layout)
        layout.setContentsMargins(*marg)
        super().setOrientation(orientation)

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self._reposition_labels()


class SliderLabel(QSpinBox):
    def __init__(
        self, slider: QSlider, parent=None, alignment=Qt.AlignCenter, connect=None
    ) -> None:
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.ClickFocus)
        # TODO: slider labels on top should have min/max set to the value of the
        # other label

        self.setRange(slider.minimum(), slider.maximum())
        slider.rangeChanged.connect(self.setRange)
        slider.rangeChanged.connect(self._update_max_size)
        self.setAlignment(alignment)
        self.setButtonSymbols(QSpinBox.NoButtons)
        self.setStyleSheet("background:transparent; border: 0;")
        if connect is not None:
            self.editingFinished.connect(lambda: connect(self.value()))
        self.editingFinished.connect(self.clearFocus)
        self._update_max_size()

    def _update_max_size(self):
        # fontmetrics to measure the width of text
        fm = QFontMetrics(self.font())
        h = self.sizeHint().height()
        fixed_content = self.prefix() + self.suffix() + " "

        # determine width based on min/max/specialValue
        s = self.textFromValue(self.minimum())[:18] + fixed_content
        w = max(0, fm.horizontalAdvance(s))
        s = self.textFromValue(self.maximum())[:18] + fixed_content
        w = max(w, fm.horizontalAdvance(s))
        if self.specialValueText():
            w = max(w, fm.horizontalAdvance(self.specialValueText()))
        w += 3  # cursor blinking space

        # get the final size hint
        opt = QStyleOptionSpinBox()
        self.initStyleOption(opt)
        size = self.style().sizeFromContents(QStyle.CT_SpinBox, opt, QSize(w, h), self)
        self.setFixedSize(size)

    def setMaximum(self, max: int) -> None:
        super().setMaximum(max)
        self._update_size()

    def setMinimum(self, min: int) -> None:
        super().setMinimum(min)
        self._update_size()
