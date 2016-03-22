#!/usr/bin/python

"""Email Directory Comber

This is just a script I wrote in order to easily filter/delete emails
in a mail directory on a remote server without relying on a UI.
Use from inside a mail directory in order to iterate mails and delete
depending on a given filter.

Compatible with python version >= 2.6.6
"""

# This is just a script I wrote in order to easily filter/delete emails
# in a mail directory on a remote server without relying on a UI.
# Use from inside a mail directory in order to iterate mails and delete
# depending on a given filter.
# Compatible with python version >= 2.6.6

import argparse
import os
import sys
import re
from email.parser import Parser

__author__ = "Lefteris Karapetsas<lefteris@refu.co>"
__license__ = "MIT"


def rm_file(f):
    try:
        os.remove(f)
    except OSError:
        pass


class Comber():
    def __init__(self, args):
        self.args = args
        if args.subject_pattern:
            self.subject_re = re.compile(args.subject_pattern)
        if args.from_pattern:
            self.from_re = re.compile(args.from_pattern)
        if args.to_pattern:
            self.to_re = re.compile(args.to_pattern)

    def process_mail(self, name, data):
        headers = Parser().parsestr(data)
        if headers['subject'] and hasattr(self, 'subject_re'):
            match = self.subject_re.match(headers['subject'])
            if not match:
                return False

        if headers['from'] and hasattr(self, 'from_re'):
            match = self.from_re.match(headers['from'])
            if not match:
                return False

        if headers['to'] and hasattr(self, 'to_re'):
            match = self.to_re.match(headers['to'])
            if not match:
                return False

        subject = headers['subject'] if headers['subject'] else "No Subject"
        if self.args.dry:
            print(
                "[DRY] Would delete mail {0} with subject \"{1}\""
                "".format(name, subject)
            )
            return False

        print(
            "[INFO] Deleting mail {0} with subject \"{1}\""
            "".format(name, subject)
        )
        rm_file(name)
        return True

    def iterate_mails(self):
        idx = 0
        for name in os.listdir(self.args.dir):
            fullname = os.path.join(self.args.dir, name)
            with open(fullname, 'r') as f:
                data = f.read()
            if self.process_mail(fullname, data):
                idx += 1
                if idx == self.args.limit:
                    print(
                        "INFO: Reached the requested limit of {0} mails."
                        " Stopping.".format(self.args.limit)
                    )
                    sys.exit(0)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description='Mail comber')
    p.add_argument("--dir", default=".", help="The directory to work in")
    p.add_argument(
        "--subject-pattern",
        help="Regular expression to match in the email subject"
    )
    p.add_argument(
        "--from-pattern",
        help="Regular expression to match in the email from header"
    )
    p.add_argument(
        "--to-pattern",
        help="Regular expression to match in the email to header"
    )
    p.add_argument(
        "--limit",
        default=-1,
        type=int,
        help="Set a limit to the number of emails to scan"
    )
    p.add_argument(
        "--dry",
        action="store_true",
        help="When given, will not actually delete anything but just "
        "run through the script's steps"
    )
    args = p.parse_args()
    c = Comber(args)
    c.iterate_mails()
