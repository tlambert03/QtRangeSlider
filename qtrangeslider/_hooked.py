from .qtcompat.QtWidgets import QSlider


class _HookedSlider(QSlider):
    def _post_get_hook(self, value):
        return value

    def _pre_set_hook(self, value):
        return value

    def value(self):
        return self._post_get_hook(super().value())

    def setValue(self, value) -> None:
        super().setValue(self._pre_set_hook(value))

    def minimum(self):
        return self._post_get_hook(super().minimum())

    def setMinimum(self, minimum):
        super().setMinimum(self._pre_set_hook(minimum))

    def maximum(self):
        return self._post_get_hook(super().maximum())

    def setMaximum(self, maximum):
        super().setMaximum(self._pre_set_hook(maximum))

    def setRange(self, min: float, max: float) -> None:
        super().setRange(self._pre_set_hook(min), self._pre_set_hook(max))
