__all__ = ["increment", "Add"]


def increment(a):
    a += 1
    return a


class Add:

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def execute(self):
        return self.a + self.b
