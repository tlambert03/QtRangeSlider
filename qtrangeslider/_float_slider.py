from typing import Tuple

from ._hooked import QSlider, _HookedSlider
from ._qrangeslider import QRangeSlider
from .qtcompat.QtCore import Signal

# class QDoubleSlider(QSlider):


#     def value(self):
#         return self._private_val_to_public_val(super().value())

#     def setValue(self, val) -> None:
#         super().setValue(self._public_val_to_private_val(val))

#     def sliderPosition(self):
#         return self._private_val_to_public_val(super().sliderPosition())

#     def setSliderPosition(self, val) -> None:
#         super().setSliderPosition(self._public_val_to_private_val(val))

#     def tickInterval(self):
#         return self._private_fraction_to_public_val(super().tickInterval())

#     def setTickInterval(self, val):
#         super().setTickInterval(self._public_val_to_private_fraction(val))

#     def pageStep(self):
#         return self._private_fraction_to_public_val(super().pageStep())

#     def setPageStep(self, val):
#         super().setPageStep(self._public_val_to_private_fraction(val))

#     def singleStep(self):
#         return self._private_fraction_to_public_val(super().singleStep())

#     def setSingleStep(self, val):
#         super().setSingleStep(self._public_val_to_private_fraction(val))

#     def mouseMoveEvent(self, e):
#         old = self.sliderPosition()
#         super().mouseMoveEvent(e)
#         new = self.sliderPosition()
#         if new != old:
#             self.sliderMoved.emit(new)

#     def sliderChange(self, change):
#         if change == self.SliderValueChange:
#             self.valueChanged.emit(self.value())
#         elif change == self.SliderRangeChange:
#             self.rangeChanged.emit(self.minimum(), self.maximum())
#         super().sliderChange(change)

#     def _bound(self, val):
#         return max(self._data_min, min(self._data_max, val))

#     def _public_val_to_private_val(self, val):
#         val = self._bound(val)
#         if self._data_max == self._data_min:
#             return self._MIN
#         frac = (val - self._data_min) / (self._data_max - self._data_min)
#         return frac * self._SPAN + self._MIN

#     def _private_val_to_public_val(self, val):
#         frac = (val - self._MIN) / self._SPAN
#         val = frac * (self._data_max - self._data_min) + self._data_min
#         return val

#     @property
#     def _scalar(self):
#         return self._SPAN / (self._data_max - self._data_min)

#     def _public_val_to_private_fraction(self, val):
#         return val * self._scalar

#     def _private_fraction_to_public_val(self, frac):
#         return frac / self._scalar


class QDoubleSlider(_HookedSlider):

    valueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    sliderMoved = Signal(float)

    _MIN: int = -int(1e9)
    _MAX: int = int(1e9)
    _SPAN = _MAX - _MIN

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data_min = QSlider.minimum(self)
        self._data_max = QSlider.maximum(self)
        QSlider.setRange(self, self._MIN, self._MAX)
        QSlider.setValue(self, self._pre_set_hook(0))

    def value(self):
        return self._post_get_hook(QSlider.value(self))

    def setValue(self, val) -> None:
        QSlider.setValue(self, self._pre_set_hook(val))

    def singleStep(self):
        return self._private_fraction_to_public_val(super().singleStep())

    def setSingleStep(self, val):
        super().setSingleStep(self._public_val_to_private_fraction(val))

    @property
    def _scalar(self):
        return self._SPAN / (self._data_max - self._data_min)

    def _public_val_to_private_fraction(self, val):
        return val * self._scalar

    def _private_fraction_to_public_val(self, frac):
        return frac / self._scalar

    def minimum(self):
        return self._data_min

    def setMinimum(self, min) -> None:
        self.setRange(min, max(self._data_max, min))

    def maximum(self):
        return self._data_max

    def setMaximum(self, max) -> None:
        self.setRange(min(self._data_min, max), max)

    def setRange(self, min: float, max: float) -> None:
        _val = self.value()
        _dm, self._data_min = self._data_min, min
        _dm, self._data_max = self._data_max, max
        if self._data_min != _dm or self._data_max != _dm:
            self.rangeChanged.emit(self._data_min, self._data_max)
            self.setValue(_val)  # re-bound
            if self.value() != _val:
                self.sliderChange(self.SliderValueChange)

    def _post_get_hook(self, val):
        frac = (val - self._MIN) / self._SPAN
        val = frac * (self._data_max - self._data_min) + self._data_min
        return val

    def _pre_set_hook(self, val):
        val = self._bound(val)
        if self._data_max == self._data_min:
            return self._MIN
        frac = (val - self._data_min) / (self._data_max - self._data_min)
        return int(frac * self._SPAN + self._MIN)

    def _bound(self, val):
        return max(self._data_min, min(self._data_max, val))

    def mouseMoveEvent(self, e):
        old = self.sliderPosition()
        super().mouseMoveEvent(e)
        new = self.sliderPosition()
        if new != old:
            self.sliderMoved.emit(new)

    def sliderChange(self, change):
        if change == self.SliderValueChange:
            self.valueChanged.emit(self.value())
        elif change == self.SliderRangeChange:
            self.rangeChanged.emit(self.minimum(), self.maximum())
        super().sliderChange(change)


class QDoubleRangeSlider(QRangeSlider, QDoubleSlider):
    rangeChanged = Signal(float, float)

    def value(self) -> Tuple[float, ...]:
        """Get current value of the widget as a tuple of integers."""
        return tuple(float(i) for i in super().value())
