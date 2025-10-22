import xml.etree.ElementTree as ET
import sys

# List of input coverage XML files
files = sys.argv[1:]

output_file = "coverage.xml"

# parse the first file as the base
tree = ET.parse(files[0])
root = tree.getroot()

packages = root.find("packages")
sources = root.find("sources")

total_lines_valid = int(root.attrib.get("lines-valid", 0))
total_lines_covered = int(root.attrib.get("lines-covered", 0))
total_branches_valid = int(root.attrib.get("branches-valid", 0))
total_branches_covered = int(root.attrib.get("branches-covered", 0))

# track sources to avoid duplicates
seen_sources = {s.text for s in sources}

# merge the rest of the files
for coverage_file in files[1:]:
    tree = ET.parse(coverage_file)
    root_element = tree.getroot()

    # merge sources
    for source in root_element.find("sources"):
        if source.text not in seen_sources:
            sources.append(source)
            seen_sources.add(source.text)

    # merge packages
    for package in root_element.find("packages"):
        packages.append(package)

    # update totals
    total_lines_valid += int(root_element.attrib.get("lines-valid", 0))
    total_lines_covered += int(root_element.attrib.get("lines-covered", 0))
    total_branches_valid += int(root_element.attrib.get("branches-valid", 0))
    total_branches_covered += int(root_element.attrib.get("branches-covered", 0))

# update coverage root attributes
root.set("lines-valid", str(total_lines_valid))
root.set("lines-covered", str(total_lines_covered))
root.set("branches-valid", str(total_branches_valid))
root.set("branches-covered", str(total_branches_covered))

# recompute rates
line_rate = total_lines_covered / total_lines_valid if total_lines_valid else 0.0
branch_rate = total_branches_covered / total_branches_valid if total_branches_valid else 0.0

root.set("line-rate", f"{line_rate:.4f}")
root.set("branch-rate", f"{branch_rate:.4f}")

# Write merged XML
tree.write(output_file, encoding="utf-8", xml_declaration=True)
print(f"Merged coverage written to {output_file}")
