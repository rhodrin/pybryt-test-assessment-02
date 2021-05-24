import pybryt

ref = pybryt.ReferenceImplementation.compile("test_ref.ipynb")
ref.dump("test_ref.pkl")
