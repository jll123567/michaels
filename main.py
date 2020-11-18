import requests
import re
import webbrowser
import copy
import json


def get_responses(start, end):
    n = start
    response_list = {}
    while n <= end:
        r = requests.get("https://www.tokywoky.com/webview/v4/{}".format(n))
        print("Got {} with code {}".format(n, r.status_code))
        response_list[n] = r
        n += 1
    return response_list


def clean_by_response_code(response_list):
    rm_key_list = []
    for k in response_list.keys():
        if not response_list[k].ok:
            rm_key_list.append(k)
    for k in rm_key_list:
        response_list.pop(k)
    return response_list


def clean_by_content_search(response_list):
    rm_key_list = []
    for k in response_list.keys():
        if re.search(r"<div id=\"app\"></div>", response_list[k].content.decode("utf-8")) is None:
            rm_key_list.append(k)
    for k in rm_key_list:
        response_list.pop(k)
    return response_list


def convert_id_to_link(link_id):
    return "https://www.tokywoky.com/webview/v4/{}".format(link_id)


def convert_to_links(response_list):
    links_list = copy.copy(response_list)
    for k in links_list.keys():
        links_list[k] = convert_id_to_link(k)
    return links_list


def open_all_links(links_list):
    first = True
    if isinstance(links_list, dict):
        for k in links_list.keys():
            if first:
                webbrowser.open_new(links_list[k])
                first = False
            else:
                webbrowser.open_new_tab(links_list[k])
    else:
        for k in links_list:
            if first:
                webbrowser.open_new(k)
                first = False
            else:
                webbrowser.open_new_tab(k)


def export_links(links_list):
    s = ""
    for k in links_list.keys():
        s += links_list[k] + "\n"
    return s


def close_all_responses(response_list):
    for r in response_list.values():
        if isinstance(r, list):
            r[0].close()
        else:
            r.close()


def import_links(links_string):
    return links_string.split("\n")


def getGroupInfo(response):
    content = response.content.decode("utf-8")
    return json.loads(re.search(r"window\.group = ({.*})", content).group(1))


def getQuestions(categoryid):
    r = requests.get("https://www.tokywoky.com/api/v2/brandcategories/{}/questions".format(categoryid))
    try:
        return r.json()
    except json.JSONDecodeError:
        return "NoQuestions"


def addQuestionCount(response_list):
    for link_id in response_list:
        q = getQuestions(getGroupInfo(response_list[link_id])["groupCategoryId"])
        if q == "NoQuestions":
            response_list[link_id] = [response_list[link_id], q]
        else:
            response_list[link_id] = [response_list[link_id], q.__len__()]
    return response_list


def printIdAndQCount(response_list):
    for link_id in response_list:
        print("{}: {}".format(convert_id_to_link(link_id), response_list[link_id][1]))


def clean_by_questions(response_list):
    rm_key_list = []
    for link_id in response_list:
        if response_list[link_id][1] == 'NoQuestions':
            continue
        if response_list[link_id][1] > 2:  # Remove if...
            rm_key_list.append(link_id)
    for k in rm_key_list:
        response_list.pop(k)
    return response_list


def separateResponses(response_list):
    investigate_response_list = {}
    for link_id in response_list:
        if response_list[link_id][1] == 'NoQuestions':
            investigate_response_list[link_id] = response_list[link_id]
    for link_id in investigate_response_list:
        response_list.pop(link_id)
    return response_list, investigate_response_list


if __name__ == "__main__":
    rs = get_responses(0, 530)
    rs = clean_by_response_code(rs)
    rs = clean_by_content_search(rs)
    rs = addQuestionCount(rs)
    rs = clean_by_questions(rs)
    rs, irs = separateResponses(rs)
    ls = convert_to_links(rs)
    ils = convert_to_links(irs)
    print("\n--------------------\n")
    print(export_links(ls))
    print("\n-----investigate----\n")
    print(export_links(ils))
    open_all_links(ils)
    # open_all_links(ls)
    close_all_responses(rs)
    close_all_responses(irs)
    # bc 605 url toky.chat
    # bc 20 url 74 (lovecore)
    # bc 101 url 131 (gray)
    # bc 607 url 515 (goth)

    # some api stuff
    # questions, customerServiceKeywords, chats(accepts a query), emojis, users
    # users has a page me(users/me)
