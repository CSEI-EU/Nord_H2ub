class UnsupportedStructure(ValueError):
    """The input uses a SpineOpt structure the replica does not reproduce exactly.

    Raised instead of building a model that would silently differ from SpineOpt's.
    """
