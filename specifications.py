from decimal import Decimal


# ---------------------------------------------------------------
# Clase base y combinadores: AND (&), OR (|), NOT (~)
# ---------------------------------------------------------------
class Specification:
    def is_satisfied_by(self, order):
        raise NotImplementedError

    def __and__(self, other):
        return AndSpec(self, other)

    def __or__(self, other):
        return OrSpec(self, other)

    def __invert__(self):
        return NotSpec(self)


class AndSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return (self.left.is_satisfied_by(order)
                and self.right.is_satisfied_by(order))


class OrSpec(Specification):
    def __init__(self, left, right):
        self.left, self.right = left, right

    def is_satisfied_by(self, order):
        return (self.left.is_satisfied_by(order)
                or self.right.is_satisfied_by(order))


class NotSpec(Specification):
    def __init__(self, spec):
        self.spec = spec

    def is_satisfied_by(self, order):
        return not self.spec.is_satisfied_by(order)


# ---------------------------------------------------------------
# Specifications concretas
# ---------------------------------------------------------------
class MinimumAmountSpec(Specification):
    """Total ESTRICTAMENTE mayor al umbral (>, no >=)."""

    def __init__(self, threshold):
        self.threshold = threshold

    def is_satisfied_by(self, order):
        return order.total.amount > self.threshold


class VIPCustomerSpec(Specification):
    """El cliente del pedido es VIP."""

    def is_satisfied_by(self, order):
        return order.customer.is_vip


class MinimumUnitsSpec(Specification):
    """El pedido tiene al menos N unidades (>=)."""

    def __init__(self, minimum):
        self.minimum = minimum

    def is_satisfied_by(self, order):
        return order.units >= self.minimum


class ActivePromotionSpec(Specification):
    """El pedido tiene una promoción activa."""

    def is_satisfied_by(self, order):
        return order.has_promotion


# ---------------------------------------------------------------
# Reglas de descuento
# ---------------------------------------------------------------
# 10 %: total > 500, cliente VIP, al menos 4 unidades y SIN promoción.
ten_percent = (
    MinimumAmountSpec(Decimal("500"))
    & VIPCustomerSpec()
    & MinimumUnitsSpec(4)
    & ~ActivePromotionSpec()
)

# 5 %: total > 5000 y SIN promoción.
five_percent = (
    MinimumAmountSpec(Decimal("5000"))
    & ~ActivePromotionSpec()
)

# Combinación con OR: califica a algún descuento.
any_discount = ten_percent | five_percent


def discount_rate(order):
    """Devuelve la tasa de descuento. Si se cumplen ambas, aplica 10 % primero."""
    if ten_percent.is_satisfied_by(order):
        return Decimal("0.10")
    if five_percent.is_satisfied_by(order):
        return Decimal("0.05")
    return Decimal("0")
