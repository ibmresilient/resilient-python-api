import os

major_minor_version = "27.1"

# Write the co3/__version__.py file to contain the calculated version number.
bldno = os.getenv("BUILD_NUMBER")

if not bldno:
    raise Exception("BUILD_NUMBER environment variable not specified")

version = "{}.{}".format(major_minor_version, bldno)

with open("resilient_circuits/version.txt", "w") as vf:
    vf.write(version)

