import os
import json
import copy
import base64
import unittest
import filebuilder

TEST_DATA_FILE = os.path.join(os.getcwd(), 'test_data.json')

class FilebuilderTest(unittest.TestCase):

    def setUp(self):
        with open(TEST_DATA_FILE, 'rb') as test_file:
            self.test_data = json.load(test_file)

        #need to compare byte strings
        for key, value in self.test_data['get_file_result'].items():
            for item in value:
                item['content'] = item['content'].encode()

    def tearDown(self):
        pass

class TestPositiveCases(FilebuilderTest):

    def test_decode(self):
        self.assertEqual(
            filebuilder.decode_content(
                copy.deepcopy(self.test_data['decode_shard'])
            )['content'],
            base64.b64decode(
                self.test_data['decode_shard']['content'].encode('ascii')
            )
        )

    def test_get_files(self):

        self.assertDictEqual(
            filebuilder.get_file_data(self.test_data['shard_list']),
            self.test_data['get_file_result']
        )

    def test_write_files(self):

        result = filebuilder.write_all_files(self.test_data['get_file_result'])

        #File is written
        self.assertTrue(
            os.path.exists(self.test_data['write_file_result']['filepath'])
        )

        #Contents match
        with open(self.test_data['write_file_result']['filepath'], 'rb') as f:
            self.assertEqual(
                self.test_data['write_file_result']['file_contents'].encode(),
                f.read()
            )

if __name__ == '__main__':
    unittest.main()
