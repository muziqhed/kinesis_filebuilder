#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-


import os
import sys
import re
from operator import itemgetter
import requests
import json
import base64

with open(os.path.join(os.getcwd(), 'filebuilder_conf.json'), 'rb') as the_file:
    CONFIG = json.load(the_file)

def decode_content(shard_dict):
    """

    Decodes base64 encoded content from file shard, returning the modified dict

    Args:
        shard_dict (int): Dictionary containing file shard from kinesis stream,
            {
                "putEndpoint" : "https://www.example.com/image.jpg",
                "partition": 0,
                "partitionCount": 10,
                "content" : "aGVsbG8gd29ybGQh"
            }

    Returns:
        dict: shard_dict with content key replaced by decoded base64 byte string,
            {
                "putEndpoint" : "https://www.example.com/image.jpg",
                "partition": 0,
                "partitionCount": 10,
                "content" : b"hello world!"
            }

    """

    shard_dict['content'] = base64.b64decode(
        shard_dict['content'].encode('ascii')
    )
    return shard_dict

def get_file_data(shard_list):
    """

    Consumes an iterable of dictionaries representing partitioned file chunks.
    Decodes and reassembles the file content for each file, submitting the
    resulting file to putEndpoint via PUT request.

    Args:
        shard_list: An iterable containing dictionaries of the form
            {
                "putEndpoint" : "https://www.example.com/image.jpg",
                "partition": 0,
                "partitionCount": 10,
                "content" : "aGVsbG8gd29ybGQh"
            }


    Returns:
        dict: Dictionary containing sorted file chunks for each put endpoint,
            e.g.
            {
        		"https://www.example.com/textfile.txt": [
                {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 0,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}, {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 1,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}]
        	}
    """
    all_files = {}

    for data in shard_list:
        if data['putEndpoint'] in all_files:
            all_files[data['putEndpoint']].append(data)
        else:
            all_files[data['putEndpoint']] = [data]

    # Extract and sort file chunks
    for each_put_endpoint, each_shard_list in all_files.items():
        # Sort shards and extract content
        all_files[each_put_endpoint] = [
            decode_content(x) for x in
            sorted(each_shard_list, key=itemgetter('partition'))
        ]

    return all_files

def write_all_files(all_file_data):
    """

    Consumes a dictionary containing put endpoints and sorted lists of decoded
    file chunks. Writes the file associated with each list to a temp directory,
    returning the data with the filepath prepended to each chunk list.

    Args:
        all_file_data (dict): A dictionary of the form
            {
        		"https://www.example.com/textfile.txt": [{
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 0,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}, {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 1,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}]
        	}
    Returns:
        dict: all_file_data with written filepaths prepended to each list, i.e.
            {
        		"https://www.example.com/textfile.txt": [
                "/tmp/textfile.txt",
                {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 0,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}, {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 1,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}]
        	}

    """

    filename_pattern = re.compile(r"^.*\/([\w\-. ]+)")
    for each_put_endpoint, each_shard_list in all_file_data.items():

        # Extract filepath from endpoint
        filename_match = filename_pattern.match(each_put_endpoint)
        if not filename_match:
            print('filepath parse error on put endpoint %s' % each_put_endpoint)
            continue

        filename = filename_match.groups(0)[0]
        filepath= os.path.join(CONFIG['TEMP_LOCATION'], filename)

        # Avoid old data by removing existing file from temp location
        if os.path.exists(filepath):
            os.remove(filepath)

        # Write file bytes
        with open(filepath, 'wb') as the_file:
            for each_shard in each_shard_list:
                the_file.write(each_shard['content'])

        all_file_data[each_put_endpoint].insert(0, filepath)

    return all_file_data

def send_all_files(all_file_data):
    """

    Consumes a dictionary containing put endpoints and lists conatining local
    filepaths of file to be submitted to each put endpoint. PUTs each file to
    its respective endpoint.

    Args:
        all_file_data (dict): A dictionary of the form
            {
        		"https://www.example.com/textfile.txt": [
                "/tmp/textfile.txt",
                {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 0,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}, {
        			"putEndpoint": "https://www.example.com/textfile.txt",
        			"partition": 1,
        			"partitionCount": 2,
        			"content": "hello world!"
        		}]
        	}
    """

    # Upload files
    for each_put_endpoint, each_shard_list in all_file_data.items():
        # PUT file to putEndpoint
        with open(each_shard_list[0], 'rb') as the_file:
            r = requests.put(
                each_put_endpoint,
                data=the_file,
                headers={"Content-Type": None}
            )
            if r.status_code != 200:
                print(
                    'Status_code %s for PUT request %s with content %s' %
                    (r.status_code, each_put_endpoint, r.text)
                )
            else:
                print(
                    'Sucessful PUT request %s' % each_put_endpoint
                )


def lambda_handler(event, context):

    send_all_files(
        write_all_files(
            get_file_data(
                [json.loads(base64.b64decode(x['kinesis']['data'].
                encode('ascii')).decode('ascii')) for x in event['Records']]
            )
        )
    )
