import base64
import hashlib
from typing import Callable


class PFBytes(bytes):
    """This class is used to represent a bytes object in PromptFlow.
    It has all the functionalities of a bytes object,
    and also has some additional methods to help with serialization and deserialization.
    """

    def __new__(cls, value: bytes, *args, **kwargs):
        # Here we must only pass the value to the bytes constructor,
        # otherwise we will get a type error that the constructor doesn't take such args.
        # See https://docs.python.org/3/reference/datamodel.html#object.__new__
        return super().__new__(cls, value)

    def __init__(self, data: bytes, mime_type: str):
        super().__init__()
        # Use this hash to identify this bytes.
        self._hash = hashlib.sha1(data).hexdigest()[:8]
        self._mime_type = mime_type.lower()

    def to_base64(self):
        """Returns the base64 representation of the PFBytes."""

        return base64.b64encode(self).decode("utf-8")


class Image(PFBytes):
    """This class is used to represent an image in PromptFlow. It is a subclass of
    ~promptflow.contracts.multimedia.PFBytes.
    """

    def __init__(self, data: bytes, mime_type: str = "image/*"):
        return super().__init__(data, mime_type)

    def __str__(self):
        return f"Image({self._hash})"

    def __repr__(self) -> str:
        return f"Image({self._hash})"

    def serialize(self, encoder: Callable = None):
        """Serialize the image to a dictionary."""

        return self.__str__() if encoder is None else encoder(self)
