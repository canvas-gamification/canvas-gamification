import logging

from bs4 import BeautifulSoup


def parse_spotbugs_xml(xml):
    bugs = []
    patterns = []

    try:
        doc = BeautifulSoup(xml, "html.parser")
        bug_instances = doc.findAll("buginstance")

        for bug_instance in bug_instances:
            bugs.append(
                {
                    "type": bug_instance["type"],
                    "short_message": bug_instance.shortmessage.text.strip(),
                    "long_message": bug_instance.longmessage.text.strip(),
                    "source_line": bug_instance.find("sourceline", recursive=False).message.text.strip(),
                }
            )

        bug_patterns = doc.findAll("bugpattern")
        for bug_pattern in bug_patterns:
            patterns.append(
                {
                    "type": bug_pattern["type"],
                    "short_description": bug_pattern.shortdescription.text.strip(),
                    "details": bug_pattern.details.text.strip(),
                }
            )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(e)

    return {
        "bugs": bugs,
        "patterns": patterns,
    }
