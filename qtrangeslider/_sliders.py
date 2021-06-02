from typing import Tuple

from ._generic_range_slider import _GenericRangeSlider
from ._generic_slider import _GenericSlider
from .qtcompat.QtCore import Signal


class QDoubleSlider(_GenericSlider[float]):
    def value(self):
        return float(self._value)


# mostly just an example... use QSlider instead.
class QIntSlider(_GenericSlider[int]):
    valueChanged = Signal(int)

    def value(self):
        return int(round(self._value))

    def _bound(self, value) -> int:
        return int(round(super()._bound(value)))


class QRangeSlider(_GenericRangeSlider):
    pass


class QDoubleRangeSlider(QRangeSlider):
    def value(self) -> Tuple[int, ...]:
        """Get current value of the widget as a tuple of integers."""
        return tuple(float(v) for v in self._value)


# QRangeSlider.__doc__ += "\n" + textwrap.indent(QSlider.__doc__, "    ")
