import os
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from xml.dom import minidom

def main():

    parser = ArgumentParser(
        description="Preprocess gold constituency annotations")
    parser.add_argument(
        "-input-file", "--input-file", help="Path to the input file")
    args = parser.parse_args()

    # read tree
    tree = ET.parse(args.input_file)
    root = tree.getroot()

    # simplify features attribute
    visited = []
    segments = root[1]
    for segment in reversed(segments): # reverse so that indexes don't get shifted when removing subelements
        start = segment.get("start")
        end = segment.get("end")
        segment.set("features", "constituent")
        # remove segment if it's duplicated
        if (start, end) in visited:
            segments.remove(segment)
        else:
            visited.append((start, end))

    # write in xml file
    with open(args.input_file[:-4] + "_simplified.xml", "w+") as output_file:
        string = ET.tostring(root, 'unicode')
        output_file.write(string)

if __name__ == "__main__":
    main()