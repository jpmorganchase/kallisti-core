import inspect


class Singleton(type):
    # _instances is organized first by class and then by arguments.
    # for a class with:
    # class Foo:
    #   def __init__(self, a, b):
    #       pass
    # The _instances can look like:
    # { Foo :
    #   {dict_items([('self', None), ('a', 1), ('b', 0)]): foo_instance1},
    #   {dict_items([('self', None), ('a', 1), ('b', 2)]): foo_instance2}}
    #
    _instances = {}

    def __call__(cls, *args, **kwargs):
        insts_by_args = cls._instances.setdefault(cls, {})
        call_args = inspect.getcallargs(cls.__init__, None, *args, **kwargs)
        items = tuple((k, v) for k, v in call_args.items() if v)
        key = frozenset(items)
        inst = insts_by_args.get(key)
        if not inst:
            inst = super(Singleton, cls).__call__(*args, **kwargs)
            insts_by_args[key] = inst
        return inst
