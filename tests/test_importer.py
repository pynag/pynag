import unittest
import tempfile
import os.path
import os

from pynag.Utils import importer

class TestPynagImporter(unittest.TestCase):
    def setUp(self):
        filename = tempfile.mktemp()
        self.filename = filename
    
    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
    
    def test_parse_csv_string(self):
        objects = importer.parse_csv_string(_TYPICAL_TESTCASE)
        self.assertEqual(2, len(objects))
        self.assertEqual('generic-service', objects[0]['use'])
        self.assertEqual('generic-host', objects[1]['use'])
    
    def test_parse_csv_string_empty(self):    
        objects = importer.parse_csv_string('')
        self.assertEqual([], objects)
    
    def test_parse_csv_file(self):
        with open(self.filename, 'w') as f:
            f.write(_TYPICAL_TESTCASE)
        objects_from_file = importer.parse_csv_file(self.filename)
        objects_from_string = importer.parse_csv_string(_TYPICAL_TESTCASE)
        self.assertEqual(objects_from_string, objects_from_file)

    def test_dict_to_objects(self):
        dict_list = importer.parse_csv_string(_TYPICAL_TESTCASE)
        pynag_objects = importer.dict_to_pynag_objects(dict_list)
        self.assertEqual(2, len(pynag_objects))
        self.assertEqual('generic-service', pynag_objects[0].use)
        self.assertEqual('generic-host', pynag_objects[1].use)
        self.assertEqual('service', pynag_objects[0].object_type)
        self.assertEqual('host', pynag_objects[1].object_type)

    def test_import_from_csv_file(self):
        with open(self.filename, 'w') as f:
            f.write(_TYPICAL_TESTCASE)
        pynag_objects = importer.import_from_csv_file(filename=self.filename, seperator=',')
        self.assertEqual(2, len(pynag_objects))
        self.assertEqual('generic-service', pynag_objects[0].use)
        self.assertEqual('generic-host', pynag_objects[1].use)
        self.assertEqual('service', pynag_objects[0].object_type)
        self.assertEqual('host', pynag_objects[1].object_type)


_TYPICAL_TESTCASE = """
object_type,host_name,use,
service,testhost,generic-service
host,testhost,generic-host
"""

if __name__ == '__main__':
    unittest.main()
