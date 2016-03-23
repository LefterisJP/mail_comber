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


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def rm_file(f):
    try:
        os.remove(f)
    except OSError:
        pass


def has_only_wildcards(str):
    return str.replace(".", "").replace("*", "") == ""


class Comber():
    def __init__(self, args):
        self.args = args
        self.prepare_pattern(args, 'subject')
        self.prepare_pattern(args, 'from')
        self.prepare_pattern(args, 'to')
        self.prepare_pattern(args, 'mailing-list')
        self.prepare_pattern(args, 'list-id')

    def prepare_pattern(self, args, name):
        normalized_name = name.replace("-", "_")
        attr = "{0}_pattern".format(normalized_name)
        if hasattr(args, attr) and getattr(args, attr) is not None:
            pattern = getattr(args, attr)
            if has_only_wildcards(pattern):
                if not query_yes_no(
                        "[WARNING] Provided pattern for '{0}' will match all "
                        "emails! Are you 100% certain you want this?".format(
                            name)):
                    print("Quitting as requested...")
                    sys.exit(0)
            setattr(
                self,
                "{0}_re".format(normalized_name),
                re.compile(pattern)
            )

    def check_header(self, headers, got_match, header):
        attr = '{0}_re'.format(header.replace("-", "_"))
        if headers[header] and hasattr(self, attr):
            re = getattr(self, attr)
            if not re.match(headers[header]):
                return False, got_match
            else:
                got_match = True
        return True, got_match

    def process_mail(self, name, data):
        headers = Parser().parsestr(data)
        match = False

        success, match = self.check_header(headers, match, 'subject')
        if not success:
            return False
        success, match = self.check_header(headers, match, 'from')
        if not success:
            return False
        success, match = self.check_header(headers, match, 'to')
        if not success:
            return False
        success, match = self.check_header(headers, match, 'mailing-list')
        if not success:
            return False
        success, match = self.check_header(headers, match, 'list-id')
        if not success:
            return False

        # if there was no match at any of the filters go out
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
        help="Regular expression to match in the email's subject"
    )
    p.add_argument(
        "--from-pattern",
        help="Regular expression to match in the email's From header"
    )
    p.add_argument(
        "--to-pattern",
        help="Regular expression to match in the email's To header"
    )
    p.add_argument(
        "--mailing-list-pattern",
        help="Regular expression to match in the email's Mailing-List header"
    )
    p.add_argument(
        "--list-id-pattern",
        help="Regular expression to match in the email's List-Id header"
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
