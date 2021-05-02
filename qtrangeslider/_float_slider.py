from ._hooked import _HookedSlider
from ._qrangeslider import QRangeSlider
from .qtcompat.QtCore import Signal


class QDoubleSlider(_HookedSlider):

    valueChanged = Signal(float)
    rangeChanged = Signal(float, float)
    sliderMoved = Signal(float)
    _multiplier = 1

    def __init__(self, *args):
        super().__init__(*args)
        self._multiplier = 10 ** 2
        self.setMinimum(0)
        self.setMaximum(99)
        self.setSingleStep(1)
        self.setPageStep(10)
        super().sliderMoved.connect(
            lambda e: self.sliderMoved.emit(self._post_get_hook(e))
        )

    def decimals(self) -> int:
        """This property holds the precision of the slider, in decimals."""
        import math

        return int(math.log10(self._multiplier))

    def setDecimals(self, prec: int):
        """This property holds the precision of the slider, in decimals

        Sets how many decimals the slider uses for displaying and interpreting doubles.
        """
        previous = self._multiplier
        self._multiplier = 10 ** int(prec)
        ratio = self._multiplier / previous

        if ratio != 1:
            self.blockSignals(True)
            try:
                newmin = self.minimum() * ratio
                newmax = self.maximum() * ratio
                newval = self.value() * ratio
                newstep = self.singleStep() * ratio
                newpage = self.pageStep() * ratio
                self.setRange(newmin, newmax)
                self.setValue(newval)
                self.setSingleStep(newstep)
                self.setPageStep(newpage)
            except OverflowError as err:
                self._multiplier = previous
                raise OverflowError(
                    f"Cannot use {prec} decimals with a range of {newmin}-"
                    f"{newmax}. If you need this feature, please open a feature"
                    " request at github."
                ) from err
            self.blockSignals(False)

    def _post_get_hook(self, value: int) -> float:
        return value / self._multiplier

    def _pre_set_hook(self, value: float) -> int:
        return int(value * self._multiplier)

    def sliderChange(self, change) -> None:
        if change == self.SliderValueChange:
            self.valueChanged.emit(self.value())
        return super().sliderChange(change)


class QDoubleRangeSlider(QRangeSlider, QDoubleSlider):
    rangeChanged = Signal(float, float)


# def _update_precision(self, minimum=None, maximum=None, step=None):
#     """Called when min/max/step is changed.

#     _precision is the factor that converts from integer representation in the slider
#     widget, to the actual float representation needed.
#     """
#     orig = self._precision

#     if minimum is not None or maximum is not None:
#         _min = minimum or self.minimum()
#         _max = maximum or self.maximum()

#         # make sure val * precision is within int32 overflow limit for Qt
#         val = max([abs(_min), abs(_max)])
#         while abs(self._precision * val) >= 2 ** 32 // 2:
#             self._precision *= 0.1
#     elif step:
#         while step < (1 / self._precision):
#             self._precision *= 10

#     ratio = self._precision / orig
#     if ratio != 1:
#         self.setValue([i * ratio for i in self.value()])
#         if not step:
#             self.setMaximum(self.maximum() * ratio)
#             self.setMinimum(self.minimum() * ratio)
