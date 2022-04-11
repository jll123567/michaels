import requests
import re
import webbrowser
import copy
import json
from dataclasses import dataclass, field
class account:
    def __init__(self, cookie=""):
        self.cookie = cookie
        self.headers = {
            "Accept": "application/json, text/plain",
            "Accept-Language": "en-US,en;q=0.5",
            "Cookie": self.cookie
        }

    def set_cookie(self, cookie):
        self.cookie = cookie
        self.headers = {
            "Accept": "application/json, text/plain",
            "Accept-Language": "en-US,en;q=0.5",
            "Cookie": self.cookie
        }

    def request_with_account(self, endpoint):
        return requests.get(url=endpoint, headers=self.headers)

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

    def print_questons(self):
        print(json.dumps(self.questions, indent=4))

    def print_brandcategory_endpoint(self, endpoint):
        r = requests.get(f"https://www.tokywoky.com/api/v2/brandcategories/{self.category_id}/{endpoint}")
        try:
            print(json.dumps(r.json(), indent=4))
        except json.JSONDecodeError:
            print("Endpoint returned no data or is invalid.")

    def request_brandcategory_endpoint(self, endpoint):
        return requests.get(f"https://www.tokywoky.com/api/v2/brandcategories/{self.category_id}/{endpoint}")


def get_tokys(start, end, debug=False):
    """Get tokys by link_Id from start(inclusive) to end(exclusive)."""
    tokys = []
    for n in range(start, end):
        r = requests.get(f"https://www.tokywoky.com/webview/v4/{n}")
        if debug:
            print(f"Got {n} with code {r.status_code}")
        tokys.append(toky(n, f"https://www.tokywoky.com/webview/v4/{n}", r))
    return tokys


def get_toky(link_id):
    return toky(link_id,
                f"https://www.tokywoky.com/webview/v4/{link_id}",
                requests.get(f"https://www.tokywoky.com/webview/v4/{link_id}"))


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


def make_link_lists():
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


if __name__ == "__main__" and True:
    # t = get_toky(131)
    # t.populate_group_info()
    # t.populate_questions()
    # print(t.category_id)
    # print(t.request_brandcategory_endpoint("questions?limit=5").json().__len__())
    A = account("cookie")
    r = A.request_with_account("https://www.tokywoky.com/api/v2/brandcategories/101/questions?last=true")
    print(r.json())

    # some api stuff
    # questions, customerServiceKeywords, chats(accepts a query), emojis, users
    # users has a page me(users/me)

    # brandcategory: the brand/category owned by some company a "toky" basically
    ## questions: the list of available questions(last=true, limit?, offset?)
    ## users: list of users, cannot view
    ### users/me: logged in user
    ## questionSkipped: access to goto next question
    ## chats: mesages started by an answer(filter=(unread|???), isBrandRestricted=true)
    # signalr: telemetry?
    ## ping: I guess a heartbeat to check for new data?
    ## negotiate: get a connection token (clientProtocol=1.5, connectionData=[{"name"%3A"publichub"}])
    ## abort: end a connection (transport=webSockets, clientProtocol=1.5, connectionToken=token, connectionData=[{"name"%3A"publichub"}])
    ## start: start a connection (transport=webSockets, clientProtocol=1.5, connectionToken=token, connectionData=[{"name"%3A"publichub"}])
