"""
BuildingSync Python Module

This module contains class names for each of the BuildingSync elements to make
it easier to build BuildingSync XML files.
"""

import datetime
from lxml import etree

from typing import Any, List, Tuple


class BSElement:
    element_type: str = ""
    element_attributes: List[str] = []
    element_enumerations: List[str] = []
    element_children: List[Tuple[str, type]] = []
    element_union: List[type] = []

    def __init__(self, *args, **kwargs):
        """Create an instance of a BuildingSync element."""
        self._children_by_name = dict(self.element_children)
        self._children_values = {}
        self._text = None

        if args:
            arg_value = args[0]
            if self.element_enumerations:
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if args[0] not in self.element_enumerations:
                    raise ValueError("invalid enumeration")
                self._text = args[0]

            elif self.element_union:
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                for subtype in self.element_union:
                    try:
                        value = subtype(args[0])
                        self._text = value._text
                        break
                    except (ValueError, TypeError):
                        pass
                else:
                    raise ValueError("invalid argument")

            elif self.element_type == "xs:boolean":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, bool):
                    raise TypeError("boolean expected")
                self._text = "true" if args[0] else "false"

            elif self.element_type == "xs:integer" or self.element_type == "xs:int":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                self._text = f"{arg_value:d}"

            elif self.element_type == "xs:nonNegativeInteger":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                if arg_value < 0:
                    raise ValueError("non-negative integer expected")
                self._text = f"{arg_value:d}"

            elif self.element_type == "xs:decimal":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, float):
                    raise TypeError("decimal (float) expected")
                self._text = f"{arg_value:f}"

            elif self.element_type == "xs:float":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, float):
                    raise TypeError("float expected")
                self._text = f"{arg_value:G}"

            elif self.element_type == "xs:string":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, str):
                    raise TypeError("string expected")
                self._text = arg_value

            elif self.element_type == "xs:date":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, datetime.date):
                    raise TypeError("datetime.date expected")
                self._text = arg_value.isoformat()

            elif self.element_type == "xs:time":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, datetime.time):
                    raise TypeError("datetime.time expected")
                self._text = arg_value.isoformat()

            elif self.element_type == "xs:dateTime":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, datetime.datetime):
                    raise TypeError("datetime.datetime expected")
                self._text = arg_value.isoformat()

            elif self.element_type == "xs:gMonthDay":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, datetime.date):
                    raise TypeError("datetime.date expected")
                self._text = arg_value.strftime("--%m-%d")

            elif self.element_type == "xs:gYear":
                if len(args) > 1:
                    raise RuntimeError("too many arguments")
                if not isinstance(arg_value, int):
                    raise TypeError("integer expected")
                self._text = f"{arg_value:d}"

            else:
                # add the args as child elements
                for arg_value in args:
                    self += arg_value

        self._attributes = kwargs

    def __getattr__(self, attr):
        """Get the value of a child element."""
        if attr.startswith("_"):
            return object.__getattribute__(self, attr)

        # make sure the attribute exists and it has been given a value
        if attr not in self._children_by_name:
            raise AttributeError(
                f"{repr(self.__class__.__name__)} object has no child {repr(attr)}"
            )
        if attr not in self._children_values:
            raise ValueError(f"{repr(attr)} not set")

        # most of the time the elements are provided once, so returning the
        # one that was provided is easier, but if there is more than one
        # this returns the entire list
        values = self._children_values[attr]
        if len(values) == 1:
            return values[0]
        else:
            return values

    def __setattr__(self, attr, value):
        """Set the value of a child element."""
        if attr.startswith("_"):
            return super().__setattr__(attr, value)

        # make sure the attribute exists and the value is the correct type
        if attr not in self._children_by_name:
            raise AttributeError(
                f"{repr(self.__class__.__name__)} object has no child {repr(attr)}"
            )
        if not isinstance(value, self._children_by_name[attr]):
            raise ValueError(
                f"{repr(attr)} invalid type, expecting {self._children_by_name[attr]}"
            )

        # setting an attribute value is an error if there is already a value
        # that has been set
        if attr in self._children_values:
            raise ValueError(f"{repr(attr)} already set")

        # save the value
        self._children_values[attr] = [value]

    def __add__(self, value):
        """Add an element value by finding the child element name with the
        correct class.  Return this element so other child element values can
        be added like 'thing + Child1() + Child2()'.
        """
        for child_name, child_type in self.element_children:
            if isinstance(value, child_type):
                break
        else:
            child_type_names = list(
                child_type.__name__ for child_name, child_type in self.element_children
            )
            raise ValueError(f"expecting one of: {', '.join(child_type_names)}")

        # if this child already has a value, add this to the end
        if child_name in self._children_values:
            self._children_values[child_name].append(value)
        else:
            self._children_values[child_name] = [value]

        return self

    def __iadd__(self, value) -> None:
        """Statment form of 'add'."""
        return self + value

    def set(self, attr: str, value: str) -> None:
        """Set an XML attribute value for the element."""
        assert isinstance(value, str)
        self._attributes[attr] = value

    def __setitem__(self, item: str, value: str) -> None:
        """Array form 'element[attr] = value' of 'element.set(attr, value)."""
        assert isinstance(value, str)
        self._attributes[item] = value

    def get(self, attr: str) -> Any:
        """Return an XML attribute value for the element."""
        return self._attributes[attr]

    def __getitem__(self, item: str) -> str:
        """Array form of 'element.get(attr)'."""
        return self._attributes[item]

    def toxml(self, root=None, child_name=None) -> Any:
        """Return an ElementTree element.  If the root is provided the element
        will be a child of the root (a subelement).  If the child_name is
        provided it will be used for the element name, otherwise it defaults
        to the class name.
        """
        # if child name was provided, this element was part of a complex type
        # where the element name doesn't match the element type name
        element_name = child_name or self.__class__.__name__

        # if no root was provided, make one, otherwise this is a child
        # element of the root
        if root is None:
            myroot = etree.Element(element_name)
        else:
            myroot = etree.SubElement(root, element_name)

        # maybe I have a value
        if self._text:
            myroot.text = str(self._text)

        # maybe I have attributes
        for k, v in self._attributes.items():
            myroot.set(k, v)

        # maybe I have children
        for child_name, child_type in self.element_children:
            for child_value in self._children_values.get(child_name, []):
                child_value.toxml(myroot, child_name)

        # return this "root" element
        return myroot

    def __str__(self):
        """Convert the element into a string."""
        return etree.tostring(self.toxml(), pretty_print=True).decode()
