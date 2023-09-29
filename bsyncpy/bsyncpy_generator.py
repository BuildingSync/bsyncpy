"""
BuildingSync to Python Module Generator

This application reads in a BuildingSync.xsd XML Schematron document and
generates a bsyncpy.py Python module that makes it simple to create
BuildingSync.xml documents.

Each BuildingSync element has a cooresponding Python class with the same
name.  The class constructors accept arguments that match the content model of
the cooresponding BuildingSync element, so NumberOfBusinesses accepts an
integer, HistoricalLandmark accepts a boolean, OperatorType accepts a string
like "Owner".

Some BuildingSync elements use the same name in multiple contexts and these
are separated as sub-classes of the context.  For example, Combustion is an
element in both the InstantaneousWaterHeatingSource and DirectTankHeatingSource
elements and this module generator application cannot determine if they
represent the content model (if they were specified as some CombustionType
then they would be).  In these cases the classes are subclasses:

    class DirectTankHeatingSource(BSElement):
        ...
        class Combustion(BSElement):
            pass
        ...

    class InstantaneousWaterHeatingSource(BSElement):
        ...
        class Combustion(BSElement):
            pass
        ...

Instances of these classes can be "added" as if they are containers, and they
can be included in the constructor arguments.  For example a Program() instance
can be added to a Programs() instance:

    >>> programs = Programs()
    >>> p1 = Program(ProgramFundingSource("1234-5553-2322"))
    >>> programs += p1
    >>> print(programs)
    <Programs>
      <Program>
        <ProgramFundingSource>1234-5553-2322</ProgramFundingSource>
      </Program>
    </Programs>

For BuildingSync elements that have attributes such as ID and IDRef, these
values can be provided as keyword arguments like PrimaryContactID(IDRef="121").
There is no validation of ID and IDRef values, which would be to verify that
all the ID values are distinct and an IDRef references an existing identifier
with the correct type.
"""

import sys
import argparse
import logging
from textwrap import dedent
from collections import defaultdict

from lxml import etree
from typing import Any, Dict, List, Set, Tuple, Union

full_name_to_bs_element: Dict[str, "BSElement"] = {}
element_dependencies: Dict[str, Set[str]] = {}

_debugging = 0


def full_element_name(element, element_name) -> str:
    parent = element
    while True:
        parent = parent.getparent()
        if parent is None:
            break
        parent_name = parent.get("name")
        if parent_name:
            element_name = parent_name + "." + element_name
    logging.debug(f"    - full name: %r", element_name)
    return element_name


def register_element(element, bs_element, ename):
    logging.debug(f"register_element {element} {bs_element} {ename}")
    global full_name_to_bs_element

    element_parent_path = [ename]

    parent = element
    while True:
        parent = parent.getparent()
        if parent is None:
            break
        parent_name = parent.get("name")
        if parent_name:
            element_parent_path.append(parent_name)

    full_name = ".".join(reversed(element_parent_path))
    logging.debug(f"    - full_name: {full_name}")

    bs_element.element_name = ename
    bs_element.element_full_name = full_name
    bs_element.element_parent_path = element_parent_path

    # keep track of it in the list of all elements
    full_name_to_bs_element[full_name] = bs_element


def register_dependency(element, dependency):
    global element_dependencies

    if element not in element_dependencies:
        element_dependencies[element] = set()
    if dependency not in element_dependencies:
        element_dependencies[dependency] = set()

    element_dependencies[element].add(dependency)


def topological_sort() -> List[str]:
    """perform topological sort on element dependencies."""
    global element_dependencies

    result: List[str] = []

    pending = list(element_dependencies.items())
    emitted: List[str] = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            element, deps = entry
            deps.difference_update(set((element,)), emitted)
            if deps:
                next_pending.append(entry)
            else:
                result.append(element)
                emitted.append(element)
                next_emitted.append(element)
        if not next_emitted:
            raise ValueError(f"cyclic dependancy detected: {element}")
        pending = next_pending
        emitted = next_emitted

    return result


class BSElement:
    """A instance of this object is a summary of the BuildingSync element
    components, enough to turn it into a Python class definition.
    """

    element_name: str
    element_type: str
    element_docstring: str
    element_attributes: List[Tuple[str, str]]  # attribute name, type
    element_enumerations: List[str]
    element_children: List[Tuple[str, str]]  # child element name, type
    element_union: List[str]
    element_subclasses: List["BSElement"]

    def __init__(self, element) -> None:
        self.element_name = "?????"
        self.element_full_name = "?????"
        self.element_short_name = "?????"
        self.element_type = ""
        self.element_docstring = ""
        self.element_attributes = []
        self.element_enumerations = []
        self.element_children = []
        self.element_union = []
        self.element_subclasses = []

    def do_classes(self, f=sys.stdout, indent=0) -> None:
        skip_pass = False

        if self.element_type.startswith("auc:"):
            element_type_class = self.element_type[4:]
        else:
            element_type_class = "BSElement"
        f.write("    " * indent + f"class {self.element_name}({element_type_class}):\n")

        if self.element_docstring:
            f.write("    " * indent + f'    """{self.element_docstring}\n')
            f.write("    " * indent + f'    """\n')
            skip_pass = True

        if self.element_type and (not self.element_type.startswith("auc:")):
            f.write("    " * indent + f"    element_type = {repr(self.element_type)}\n")
            skip_pass = True

        if self.element_enumerations:
            f.write(
                "    " * indent
                + f"    element_enumerations = {repr(self.element_enumerations)}\n"
            )
            skip_pass = True

        for subclass in self.element_subclasses:
            subclass.do_classes(f, indent + 1)
            skip_pass = True

        if not skip_pass:
            f.write("    " * indent + f"    pass\n")
        f.write("\n")

    def do_children(self, f=sys.stdout) -> None:
        if self.element_attributes:
            f.write(f"{self.element_short_name}.element_attributes = [\n")
            for attribute_name, attribute_type in self.element_attributes:
                f.write(f"    {repr(attribute_name)},  # {attribute_type}\n")
            f.write(f"    ]\n")
        if self.element_children:
            f.write(f"{self.element_short_name}.element_children = [\n")
            for child_name, child_type in self.element_children:
                f.write(f"    ({repr(child_name)}, {child_type} ),\n")
            f.write(f"    ]\n")
        if self.element_union:
            f.write(f"{self.element_short_name}.element_union = [\n")
            for union_type in self.element_union:
                f.write(f"    {union_type},\n")
            f.write(f"    ]\n")
        for subclass in self.element_subclasses:
            subclass.do_children(f)

    def write(self, f=sys.stdout, indent=0) -> None:
        self.do_classes(f, indent)
        self.do_children(f)
        f.write("\n")


def do_simpleType(element) -> BSElement:
    logging.debug(f"simpleType {element} {element.get('name')}")

    element_ref = element.get("ref")
    if element_ref:
        logging.debug(f"    - elsewhere: {element_ref}")
        return

    bs_element = BSElement(element)

    element_name = element.get("name")
    if element_name:
        logging.debug(f"    - here: {element_name}")
        register_element(element, bs_element, element_name)

    for i, child in enumerate(element):
        logging.debug(f"    [{i}] {child}")
        if child.tag == "annotation":
            logging.debug("        - annotation")
            bs_element.element_docstring = child[0].text

        elif child.tag == "restriction":
            restriction = child
            restriction_base = restriction.get("base")
            bs_element.element_type = restriction_base
            if restriction_base in ("xs:decimal", "xs:float"):
                logging.debug("        - decimal")
            elif restriction_base == "xs:string":
                if len(restriction) == 0:
                    logging.debug("    - no other restrictions")
                elif restriction[0].tag == "pattern":
                    logging.debug("    - pattern")
                else:
                    enumerations = []
                    for enum in restriction:
                        if enum.tag != "enumeration":
                            raise RuntimeError(f"enumeration expected: {enum}")
                        enumerations.append(enum.get("value"))
                    logging.debug(f"    - enumerations: {enumerations}")

                    bs_element.element_enumerations = enumerations
            else:
                raise RuntimeError(
                    f"unknown restriction base: {restriction_base} {child}"
                )

        elif child.tag == "union":
            union_member_types = child.get("memberTypes").split()
            logging.debug("        - union: {union_member_types}")
            for union_type in union_member_types:
                if union_type.startswith("auc:"):
                    bs_element.element_union.append(union_type[4:])
                else:
                    raise RuntimeError(f"union out of scope: {union_type}")

        else:
            raise RuntimeError(f"unrecognized child of a simple type: {child}")

    return bs_element


def do_complexType(element) -> BSElement:
    logging.debug(f"complexType {element} {element.get('name')}")

    element_ref = element.get("ref")
    if element_ref:
        logging.debug(f"    - elsewhere: {element_ref}")
        return

    bs_element = BSElement(element)

    element_name = element.get("name")
    if element_name:
        logging.debug(f"    - here: {element_name}")
        register_element(element, bs_element, element_name)

    if len(element) == 0:
        logging.debug("    - no content")

    simple_content = choice = sequence = None
    for i, child in enumerate(element):
        logging.debug(f"    [{i}] {child}")
        if child.tag == "annotation":
            logging.debug("        - annotation")
            bs_element.element_docstring = child[0].text

        elif child.tag == "attribute":
            attribute_name = child.get("name")
            if attribute_name:
                logging.debug(f"        - attribute: {attribute_name}")

            attribute_type = child.get("type")
            if attribute_type:
                logging.debug(f"        - attribute type: {attribute_type}")
                if attribute_type.startswith("xs:"):
                    attribute_type = attribute_type[3:]

            attribute_use = child.get("use")
            if attribute_use:
                logging.debug(f"        - attribute use: {attribute_use}")

            attribute_ref = child.get("ref")
            if attribute_ref:
                logging.debug(f"        - attribute reference: {attribute_ref}")
                if attribute_ref.startswith("auc:"):
                    attribute_ref = attribute_ref[4:]

            if attribute_name and attribute_type:
                bs_element.element_attributes.append((attribute_name, attribute_type))
            elif attribute_ref:
                bs_element.element_attributes.append((attribute_ref, attribute_ref))
            else:
                logging.debug("    - punt")

        elif child.tag == "simpleContent":
            if simple_content or choice or sequence:
                raise RuntimeError("unexpected simpleContent/choice/sequence")
            simple_content = child

        elif child.tag == "choice":
            if simple_content or choice or sequence:
                raise RuntimeError("unexpected simpleContent/choice/sequence")
            choice = child

        elif child.tag == "sequence":
            if simple_content or choice or sequence:
                raise RuntimeError("unexpected simpleContent/choice/sequence")
            sequence = child
        else:
            raise RuntimeError(f"unrecognized child of a complex type: {child}")

    if simple_content is not None:
        logging.debug("    simple content!")

        for i, child in enumerate(simple_content):
            logging.debug(f"    s [{i}] {child}")
            if child.tag == "extension":
                bs_element.element_type = child.get("base")
                if len(child) != 0:
                    logging.debug("        - more to do ***")
            else:
                raise RuntimeError(f"unrecognized child of simple content: {child}")

    elif choice is not None:
        logging.debug("    choice!")
        for i, child in enumerate(choice):
            child_name = child.get("name")
            child_ref = child.get("ref")
            logging.debug(f"    c [{i}] {child} {child_name} {child_ref}")
            if not child_name:
                child_name = child_ref[4:]

            choice_element = do_element(child)
            logging.debug(f"        - choice_element: {choice_element.element_name}")

            bs_element.element_children.append(
                (child_name, choice_element.element_full_name)
            )

    elif sequence is not None:
        logging.debug("    sequence!")
        for i, child in enumerate(sequence):
            logging.debug(f"    s [{i}] {child} {child.get('name')}")

            if child.tag == "element":
                child_name = child.get("name")
                child_ref = child.get("ref")

                if child_name and child_ref:
                    logging.debug(f"        - here {child_name} refers to {child_ref}")
                    if child_ref.startswith("auc:"):
                        child_type_name = child_ref[4:]
                        bs_element.element_children.append(
                            (child_name, child_type_name)
                        )
                    else:
                        logging.debug("        - punt")

                elif child_name:
                    logging.debug("        - seems to be here")
                    logging.debug(f"+1 {child_name}")
                    child_element = do_element(child)
                    logging.debug(f"-1 {child_name}")

                    bs_element.element_children.append(
                        (child_name, child_element.element_full_name)
                    )

                elif child_ref:
                    logging.debug(f"        - no name, refers to {child_ref}")

                    if child_ref.startswith("auc:"):
                        child_type_name = child_ref[4:]
                        bs_element.element_children.append(
                            (child_type_name, child_type_name)
                        )
                    else:
                        logging.debug("        - punt")

                else:
                    raise RuntimeError("resolve element with no name or reference")

            elif child.tag == "choice":
                logging.debug("        - embedded choice")
                for j, subchild in enumerate(child):
                    logging.debug(f"        c [{j}] {subchild} {subchild.get('name')}")
                    if subchild.tag == "element":
                        logging.debug(f"        c+")
                        subchild_element = do_element(subchild)
                        logging.debug(f"        c-")

                        subchild_name = subchild.get("name")
                        subchild_ref = subchild.get("ref")

                        if subchild_name and subchild_ref:
                            logging.debug(
                                f"            - here {subchild_name} refers to {subchild_ref}"
                            )
                            if subchild_ref.startswith("auc:"):
                                subchild_type_name = child_ref[4:]
                                bs_element.element_children.append(
                                    (subchild_name, subchild_type_name)
                                )
                            else:
                                logging.debug("            - punt")

                        elif subchild_name:
                            logging.debug(f"            - seems to be here")
                            bs_element.element_children.append(
                                (subchild_name, subchild_element.element_full_name)
                            )

                        elif subchild_ref:
                            logging.debug(
                                f"            - no name, refers to {subchild_ref}"
                            )

                            if subchild_ref.startswith("auc:"):
                                subchild_type_name = subchild_ref[4:]
                                bs_element.element_children.append(
                                    (subchild_type_name, subchild_type_name)
                                )
                            else:
                                logging.debug("            - punt")

                        else:
                            raise RuntimeError(
                                "resolve element with no name or reference"
                            )

                    elif subchild.tag == "sequence":
                        logging.debug(f"        - sequence {subchild} ***")
                        for i, grandchild in enumerate(subchild):
                            grandchild_name = grandchild.get("name")
                            grandchild_ref = grandchild.get("ref")
                            logging.debug(
                                f"            s [{i}] {grandchild} {grandchild_name} {grandchild_ref}"
                            )

                            grandchild_element = do_element(grandchild)
                            if grandchild_ref.startswith("auc:"):
                                grandchild_type_name = grandchild_ref[4:]
                                bs_element.element_children.append(
                                    (grandchild_type_name, grandchild_type_name)
                                )
                            else:
                                logging.debug("            - punt")
                    else:
                        raise RuntimeError(f"unrecognized child of a choice: {child}")

            else:
                raise RuntimeError(f"unrecognized child of a sequence: {child}")

    else:
        logging.debug(f"    empty")

    return bs_element


def do_element(element) -> BSElement:
    logging.debug(f"element {element} {element.get('name')}")

    element_name = element.get("name")
    if element_name:
        logging.debug(f"    - here: {element_name}")

    element_type = element.get("type")
    if element_type:
        logging.debug(f"    - type: {element_type}")

    element_ref = element.get("ref")
    if element_ref:
        logging.debug(f"    - elsewhere: {element_ref}")
        if element_ref.startswith("auc:"):
            element_type = element_ref
            element_name = element_ref[4:]
        else:
            raise RuntimeError("oof!")

    element_docstring = ""

    simple_type = complex_type = None
    for i, child in enumerate(element):
        logging.debug(f"    [{i}] {child}")
        if child.tag == "annotation":
            logging.debug("        - annotation")
            element_docstring = child[0].text
        elif child.tag == "simpleType":
            simple_type = child
        elif child.tag == "complexType":
            complex_type = child
        else:
            raise RuntimeError(f"unrecognized child of a element: {child}")

    if simple_type is not None:
        logging.debug(f"    - simple type {simple_type[0]}")
        logging.debug(f"+2 {element_name}")
        bs_element = do_simpleType(simple_type)
        logging.debug(f"-2 {element_name}")

    elif complex_type is not None:
        logging.debug("    - complex type")
        logging.debug(f"+3 {element_name}")
        bs_element = do_complexType(complex_type)
        logging.debug(f"-3 {element_name}")

    else:
        logging.debug(f"    - reference type: {element_type}")

        bs_element = BSElement(element)
        bs_element.element_type = element_type

    bs_element.element_docstring = element_docstring

    register_element(element, bs_element, element_name)

    return bs_element


def do_attribute(element) -> BSElement:
    logging.debug(f"attribute {element} {element.get('name')}")


#
#   __main__
#

parser = argparse.ArgumentParser()

# needs an XSD file name
parser.add_argument("schema", type=str, help="schema file name")
parser.add_argument(
    "--debug",
    help="turn on debugging",
    action="store_true",
)

args = parser.parse_args()

# turn on debugging
if args.debug:
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("args: {!r}".format(args))

# parse the XML Schema document and get the root element
doc = etree.parse(args.schema)
root = doc.getroot()

# simplify the element names by pulling out the local name
for elem in root.getiterator():
    elem.tag = etree.QName(elem).localname
etree.cleanup_namespaces(root)

# loop through the root elements and register them
for child in root:
    # import gbxml
    if child.tag == "import":
        pass

    elif child.tag == "annotation":
        pass

    elif child.tag == "attribute":
        do_attribute(child)

    elif child.tag == "element":
        do_element(child)

    elif child.tag == "simpleType":
        do_simpleType(child)

    elif child.tag == "complexType":
        do_complexType(child)

    else:
        raise RuntimeError(f"what is this? {child}")

#
#   Find shortest distinct names
#

names_to_bs_element_sets = defaultdict(set)

# Create sets of elements that share a common path from themselves up to the
# root.  For example, with elements A.B.C and A.D.C, ('C',) will contain two
# elements, ('C', 'B') and ('C', 'D') will each contain one.
for bs_element in full_name_to_bs_element.values():
    element_parent_path = bs_element.element_parent_path
    for i in range(len(element_parent_path)):
        element_name_tuple = tuple(element_parent_path[: i + 1])
        names_to_bs_element_sets[element_name_tuple].add(bs_element)

if _debugging:
    print("")
    print("----- names to element sets -----")
    print("")
    for i, (k, v) in enumerate(names_to_bs_element_sets.items()):
        print(f"    [{i}] {k} {len(v)} {v}")
        if len(v) > 1:
            for bs_element in v:
                print(f"        {bs_element.element_parent_path} {bs_element}")


# dict of shortened names
short_name_to_bs_element = {}

# Find the 'root' elements which appear at the top level of the schema document
# and therefore have a path length of one.  There is no shorter version of these
# names.
for bs_element in full_name_to_bs_element.values():
    element_parent_path = bs_element.element_parent_path
    if len(element_parent_path) == 1:
        bs_element.element_short_name = bs_element_name = element_parent_path[0]
        short_name_to_bs_element[bs_element_name] = bs_element
        logging.debug(f"--0 {bs_element_name} {bs_element}")

# Now make a second pass through the elements and find the shortest distinct
# path by looking for the element set that has only one element.
for bs_element in full_name_to_bs_element.values():
    element_parent_path = bs_element.element_parent_path

    # skip over the elements that have already been managed
    if len(element_parent_path) == 1:
        continue

    for i in range(1, len(element_parent_path) + 1):
        element_name_tuple = tuple(element_parent_path[:i])
        bs_element.element_short_name = bs_element_name = ".".join(
            reversed(element_name_tuple)
        )

        # look for the set of elements that share this name
        bs_element_set = names_to_bs_element_sets[element_name_tuple]
        if len(bs_element_set) > 1:
            logging.debug(
                f"--{i}     {bs_element_name} element {element_name_tuple} - try again"
            )
            continue

        # for this element name to be unique its parent name also has to be
        # unique, which isn't always the case
        parent_name_tuple = element_name_tuple[1:]
        parent_element_name = ".".join(reversed(parent_name_tuple))

        # if the parent name is already established in the first pass then
        # use it.  This prevents the loop from not finding any distinct names
        # when the child name has the same name as the parent like
        # ScenarioType.ScenarioType
        if parent_element_name in short_name_to_bs_element:
            logging.debug(
                f"--{i}     {bs_element_name} parent {parent_name_tuple} - established"
            )
        else:
            parent_element_set = names_to_bs_element_sets[parent_name_tuple]
            if len(parent_element_set) > 1:
                logging.debug(
                    f"--{i}     {bs_element_name} parent {parent_name_tuple} - try again"
                )
                continue

        # found a good short name
        short_name_to_bs_element[bs_element_name] = bs_element
        logging.debug(f"--{i} {bs_element_name} {bs_element}")
        break
    else:
        raise RuntimeError(f"no distinct path: {element_parent_path}")

#
#   Resolve parent/child subclasses
#

for bs_element in full_name_to_bs_element.values():
    bs_element_name = bs_element.element_short_name
    if "." in bs_element.element_short_name:
        parent_name = bs_element_name[: bs_element_name.rfind(".")]

        logging.debug(f"{parent_name} parent of {bs_element_name}")
        parent_element = short_name_to_bs_element[parent_name]
        parent_element.element_subclasses.append(bs_element)
    else:
        logging.debug(f"{bs_element_name} has no parent")

#
#   Find Element Dependencies
#

for bs_element in full_name_to_bs_element.values():
    bs_element_name = bs_element.element_short_name

    # resolve the parent type and register the dependency
    if bs_element.element_type.startswith("auc:"):
        parent_type = bs_element.element_type[4:]
        logging.debug(f"{bs_element_name} is a subtype of {parent_type}")
        if parent_type not in short_name_to_bs_element:
            raise KeyError(parent_type)
        register_dependency(bs_element_name, parent_type)

    # look through each of the children, resolve their type and register
    # the dependency
    new_element_children = []
    for child_name, child_type in bs_element.element_children:
        # if the type has the "auc:" prefix it should already be a correct
        # short name for the type
        if child_type.startswith("auc:"):
            child_type = child_type[4:]
            logging.debug(f"{bs_element_name} has child {child_name} type {child_type}")
            if child_type not in short_name_to_bs_element:
                raise KeyError(child_type)
        else:
            logging.debug(
                f"{bs_element_name} has child {child_name} of type {child_type}"
            )

            # this might already be a short name
            if child_type in short_name_to_bs_element:
                pass
            # this might be a full name, change it to its short name
            elif child_type in full_name_to_bs_element:
                child_type = full_name_to_bs_element[child_type].element_short_name
                logging.debug(f"    - short name {child_type}")
            else:
                raise KeyError(child_type)

        register_dependency(bs_element_name, child_type)
        new_element_children.append((child_name, child_type))

    # some of the children may have changed so use the new list
    bs_element.element_children = new_element_children

    # resolve the union types which should already be short names
    for union_type in bs_element.element_union:
        logging.debug(f"{bs_element_name} is a union containing {union_type}")
        if union_type not in short_name_to_bs_element:
            raise KeyError(union_type)
        register_dependency(bs_element_name, union_type)

if _debugging:
    print("")
    print("----- element dependencies -----")
    print("")
    for i, (k, v) in enumerate(element_dependencies.items()):
        print(f"    [{i}] {k} {v}")

#
#   Topological sort of the dependencies
#

sorted_dependancies = topological_sort()

#
#   Create an output file with the header
#

with open("bsync.py", "w") as bspy_file:
    with open("bsyncpy_header.py") as bspy_header:
        bspy_file.write(bspy_header.read())

    bspy_file.write(f"\n")

    for bs_element_name in sorted_dependancies:
        if "." in bs_element_name:
            continue
        bs_element = short_name_to_bs_element[bs_element_name]
        bspy_file.write(f"# {bs_element.element_full_name}\n")
        bs_element.write(bspy_file)
