import requests
import re
import webbrowser
import copy
import json
from dataclasses import dataclass, field


@dataclass
class toky:
    link_id: int
    link: str
    response: requests.Response
    group_info: dict = field(default_factory=dict)
    category_id: int = -1
    questions: dict = field(default_factory=dict)
    question_count: int = -1

    def populate_group_info(self):
        """Get the group info for the group from a response."""
        content = self.response.content.decode("utf-8")
        self.group_info = json.loads(re.search(r"window\.group = ({.*})", content).group(1))
        self.category_id = self.group_info["groupCategoryId"]

    def populate_questions(self):
        """Get the questions of a toky."""
        r = requests.get("https://www.tokywoky.com/api/v2/brandcategories/{}/questions".format(self.category_id))
        try:
            self.questions = r.json()
            self.question_count = self.questions.__len__()
        except json.JSONDecodeError:
            pass



def get_tokys(start, end, debug=False):
    """Get tokys by link_Id from start(inclusive) to end(exclusive)."""
    tokys = []
    for n in range(start, end):
        r = requests.get(f"https://www.tokywoky.com/webview/v4/{n}")
        if debug:
            print(f"Got {n} with code {r.status_code}")
        tokys.append(toky(n, f"https://www.tokywoky.com/webview/v4/{n}", r))
    return tokys


def clean_by_response_code(tokys):
    """Remove tokys from the list if they have a response that is not ok"""
    for toky_index in reversed(range(tokys.__len__())):
        if not tokys[toky_index].response.ok:
            tokys.pop(toky_index)
    return tokys


def convert_to_links(tokys):
    """Return a list of links from the  ids in the response_list."""
    return [toky.link for toky in tokys]


def open_all_links(links_list):
    """Take a list of links and open them all in the default browser."""
    first = True
    for k in links_list:
        if first:
            webbrowser.open_new(k)
            first = False
        else:
            webbrowser.open_new_tab(k)


def export_links(links, file_name=None):
    """Take a list of links and return them as a newline separated string."""
    s = ""
    for link in links:
        s += link + "\n"
    if file_name is not None:
        with open(file_name, r"w") as f:
            f.write(s)
    return s


def close_all_responses(tokys):
    """Close all the responses in the response list."""
    for toky in tokys:
        toky.response.close()


def import_links(links_string):
    """Convert a newline separated list of links to a list."""
    return links_string.split("\n")


def separate_responses(tokys):
    """
    Separate tokys into lists using some criteria.

    Tokys are safe if they have between 0 and 9.
    Tokys are in_use if they have 10 or more questions.
    Tokys need investigation if they have -1 questions(didn't get json from api)
    """
    investigate_tokys = []
    in_use_tokys = []
    safe_tokys = []
    for toky in tokys:
        if toky.question_count == -1:
            investigate_tokys.append(toky)
        elif toky.question_count >= 10:
            in_use_tokys.append(toky)
        else:
            safe_tokys.append(toky)
    return investigate_tokys, in_use_tokys, safe_tokys


def populate_all(tokys, debug=False):
    """Populate group info and questions for a list of tokys"""
    for toky in tokys:
        if debug:
            print(f"populating {toky.link}")
        toky.populate_group_info()
        toky.populate_questions()


if __name__ == "__main__" and True:
    ts = get_tokys(0, 600, debug=True)
    print(f"Unclean: {[t.link_id for t in ts]}")
    clean_by_response_code(ts)
    print(f"Clean:   {[t.link_id for t in ts]}")
    populate_all(ts, debug=True)
    it, ut, st = separate_responses(ts)
    print(f"\n -------------investigate------------- \n{export_links(convert_to_links(it), 'tokys_investigate.txt')}")
    print(f"\n ---------------in use---------------- \n{export_links(convert_to_links(ut), 'tokys_in_use.txt')}")
    print(f"\n ----------------safe----------------- \n{export_links(convert_to_links(st), 'tokys_safe.txt')}")
    close_all_responses(ts)

    # some api stuff
    # questions, customerServiceKeywords, chats(accepts a query), emojis, users
    # users has a page me(users/me)
