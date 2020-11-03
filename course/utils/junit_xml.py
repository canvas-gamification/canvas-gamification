import logging
import re


from bs4 import BeautifulSoup


def parse_junit_xml(xml):
    results = []

    try:
        doc = BeautifulSoup(xml)
        test_cases = doc.findAll('testcase')

        for test_case in test_cases:
            doc = {
                'name': format_test_name(test_case['name']),
                'status': "PASS",
                'message': ""
            }

            failure = test_case.failure
            if failure:
                doc['status'] = "FAIL"
                doc['message'] = format_message(failure['message'])

            results.append(doc)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(e)

    return results


def format_message(message):
    starting_arrow_index = message.find("==>")
    return message if starting_arrow_index == -1 else message[:starting_arrow_index]


def convert_camel_case_to_title_case(text):
    title_case_str = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', text)
    return re.sub('([a-z0-9])([A-Z0-9])', r'\1 \2', title_case_str)


def format_test_name(name):
    title_case_str = convert_camel_case_to_title_case(name)
    return title_case_str.replace('()', '').capitalize()
