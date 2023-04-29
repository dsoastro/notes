import os
from enum import Enum
from error import MyError, log
from note_conf import HISTORY_LOCATION, PATH, EDITOR
from tags import get_tags_in_file, add_tag_to_base, save_tag_base


class Commands(Enum):
    CAT = 1
    EDIT = 2
    NEW_NOTE = 3
    CD = 4
    L = 5
    PWD = 6
    SEARCH = 7
    Z = 8
    F = 9
    LIST = 10
    TAGS = 11
    T = 12
    UPDATE_TAG_DB = 13


COLOR = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "ENDC": "\033[0m",
    "BOLD": "\033[1m"
}

SHOW_FILE = 1
EDIT_FILE = 2
NEW_FILE = 3

EDITOR_COMMAND = "editor="
EDITOR_LIST = ["gedit", "subl", "vim", "nano", "atom", "grip", "mdless", "code"]

dir_history = {PATH}
file_history = set()


def save_dir_history():
    path = os.path.join(HISTORY_LOCATION, ".dirhistory")
    with open(path, "w") as f:
        for p in dir_history:
            f.write(p + "\n")


def load_dir_history():
    path = os.path.join(HISTORY_LOCATION, ".dirhistory")
    try:
        with open(path, "r") as f:
            for line in f:
                dir_history.add(line.rstrip())
    except:
        pass


def add_to_dir_history(path):
    dir_history.add(path)
    log("add_to_dir_history, added: ", path)
    log("add_to_dir_history, dir_history:", dir_history)


def search_dir_history(word):
    ''' return list of entries containing word '''
    log("search_dir_history for: ", word)
    result = [entry for entry in dir_history if word.lower() in entry.lower()]
    log("search_dir_history res: ", result)
    return result


def save_file_history():
    path = os.path.join(HISTORY_LOCATION, ".filehistory")
    with open(path, "w") as f:
        for p in file_history:
            f.write(p + "\n")


def load_file_history():
    path = os.path.join(HISTORY_LOCATION, ".filehistory")
    try:
        with open(path, "r") as f:
            for line in f:
                file_history.add(line.rstrip())
    except:
        pass


def add_to_file_history(path):
    if os.path.isdir(path):
        return
    file_history.add(path)

    log("add_to_file_history, added: ", path)
    # log("add_to_file_history, file_history:", file_history)


def search_file_history(word):
    ''' return list of entries containing word '''
    log("search_file_history for: ", word)

    result = [path for path in file_history if word.lower() in os.path.basename(path).lower()]
    log("search_file_history res: ", result)
    return result


def print_file(path, search_word=None):
    def print_line(line):
        if search_word is None:
            print(line, end="")
        else:
            index = line.lower().find(search_word.lower())
            original_word = line[index:index + len(search_word)]
            if index != -1:
                endpos = index + len(search_word)
                print(line[:index], end="")
                print(COLOR["BOLD"], end="")
                print(COLOR["RED"], end="")
                print(original_word, end="")
                print(COLOR["ENDC"], end="")
                print(line[endpos:], end="")

            else:
                print(line, end="")

    print("cat", end=" ")
    print_line(path)
    print()
    # os.system("/usr/bin/bat " + '"' + path+'"')
    try:
        with open(path, "r") as f:
            for line in f:
                print_line(line)

    except Exception as e:
        print(e)


def get_external_editor(command):
    '''

    :param command: command to search editor in
    :return: (None,command) or (editor,command string without editor)
    '''

    if EDITOR_COMMAND in command:
        pos = command.find(EDITOR_COMMAND)
        a = command[pos:].split("=")
        if len(a) > 1:
            if a[1] in EDITOR_LIST:
                return (a[1], command.replace(EDITOR_COMMAND + a[1], ""))
            else:
                return (None, command.replace(EDITOR_COMMAND + a[1], ""))

        return (None, command.replace(EDITOR_COMMAND, ""))

    return (None, command)


def show_or_edit_file(fpath, type, ext_editor=None, mid="", add_id=True, search_word=None):
    '''

    :param fpath: full path
    :param type: show, edit or new_file
    :return:
    '''
    if os.path.isdir(fpath):
        raise MyError("Please specify a file, not a directory")

    if type != NEW_FILE and not os.path.exists(fpath):
        raise MyError("File " + fpath + " does not exist")

    log("show / edit, fpath=", fpath)

    add_to_file_history(fpath)
    save_file_history()
    if type == SHOW_FILE:
        print_file(fpath, search_word=search_word)
    else:

        if add_id and type == NEW_FILE:
            id_string = "id: " + mid  # generate_new_id()
            create_file_if_not_exist(fpath, id_string)

        if type == EDIT_FILE:
            prev_tags = get_tags_in_file(fpath)
        else:
            prev_tags = []

        if ext_editor is None:
            os.system(EDITOR + ' "' + fpath + '"')
        else:
            if ext_editor == "grip":
                os.system("grip -b" + ' "' + fpath + '"')
            else:
                os.system(ext_editor + ' "' + fpath + '"')

        tags = get_tags_in_file(fpath)
        add_tag_to_base(tags, fpath)

        prev_tags_set = set(prev_tags)
        tags_set = set(tags)
        if prev_tags_set != tags_set:
            log("save tag base")
            save_tag_base()


def parse_command(command):
    '''
    :param command: string of command
    :return: { "is_index": True / False, "command": command, "args":[args] }
    '''

    # check if command is just index
    index_ = -1
    index_flag = False
    try:
        index_ = int(command)
        index_flag = True
    except:
        pass

    if index_flag:
        return {"is_index": True, "index": index_, "command": None, "args": []}

    if command.startswith("c ") or command.startswith("cat "):
        arr = command.split()
        if len(arr) < 2:
            raise MyError("Usage: c(at) filenumber")
        else:
            try:
                index = int(arr[1])

            except:
                raise MyError("Wrong index:" + arr[1])

            return {"is_index": False, "index": -1, "command": Commands.CAT, "args": [index]}

    if command.startswith("e "):
        ext_editor, command = get_external_editor(command)
        arr = command.split()
        if len(arr) < 2:
            raise MyError("Usage: e filenumber")
        else:
            try:
                index = int(arr[1])

            except:
                raise MyError("Wrong index:" + arr[1])

            return {"is_index": False, "index": -1, "command": Commands.EDIT, "args": [index, ext_editor]}

    if command.startswith("n "):
        ext_editor, command = get_external_editor(command)

        name = command[1:].strip()
        if name == "":
            raise MyError("Usage: n filename")
        else:
            return {"is_index": False, "index": -1, "command": Commands.NEW_NOTE, "args": [name, ext_editor]}

    if command.startswith("cd"):
        name = command[2:]  # "" if command = cd
        return {"is_index": False, "index": -1, "command": Commands.CD, "args": [name]}

    if command.strip() == "l":
        return {"is_index": False, "index": -1, "command": Commands.L, "args": []}

    if command.strip() == "pwd":
        return {"is_index": False, "index": -1, "command": Commands.PWD, "args": []}

    if command.strip() == "tags":
        return {"is_index": False, "index": -1, "command": Commands.TAGS, "args": []}

    if command.strip() == "list":
        return {"is_index": False, "index": -1, "command": Commands.LIST, "args": []}

    if command.strip() == "update_tag_db":
        return {"is_index": False, "index": -1, "command": Commands.UPDATE_TAG_DB, "args": []}

    if command.startswith("s "):
        name = command[2:].strip()
        if name == "":
            raise MyError("Usage: s search_string")
        # search in file names only
        if name.endswith("--name"):
            name = name.replace("--name", "").strip()
            return {"is_index": False, "index": -1, "command": Commands.SEARCH, "args": [name, {"name_only": True}]}
        else:
            return {"is_index": False, "index": -1, "command": Commands.SEARCH, "args": [name, {"name_only": False}]}

    if command.startswith('z '):
        if len(command) < 2:
            raise MyError("Usage: z dirname")
        return {"is_index": False, "index": -1, "command": Commands.Z, "args": [command[2:].strip()]}

    if command.startswith('f '):
        if len(command) < 2:
            raise MyError("Usage: f filename")
        return {"is_index": False, "index": -1, "command": Commands.F, "args": [command[2:].strip()]}

    if command.startswith('t '):
        if len(command) < 2:
            raise MyError("Usage: t taglist")
        return {"is_index": False, "index": -1, "command": Commands.T, "args": [command[2:].strip()]}

    raise MyError("Unknown command: " + command)


def create_file_if_not_exist(path, content=""):
    if os.path.exists(path):
        return
    else:
        try:
            with open(path, "w") as f:
                f.write(content)
        except:
            pass


SHOW_FILE = 1
EDIT_FILE = 2
NEW_FILE = 3


def show_or_edit_file(fpath, type, ext_editor=None, mid="", add_id=True, search_word=None):
    '''

    :param fpath: full path
    :param type: show, edit or new_file
    :return:
    '''
    if os.path.isdir(fpath):
        raise MyError("Please specify a file, not a directory")

    if type != NEW_FILE and not os.path.exists(fpath):
        raise MyError("File " + fpath + " does not exist")

    log("show / edit, fpath=", fpath)

    add_to_file_history(fpath)
    save_file_history()
    if type == SHOW_FILE:
        print_file(fpath, search_word=search_word)
    else:

        if add_id and type == NEW_FILE:
            id_string = "id: " + mid  # generate_new_id()
            create_file_if_not_exist(fpath, id_string)

        if type == EDIT_FILE:
            prev_tags = get_tags_in_file(fpath)
        else:
            prev_tags = []

        if ext_editor is None:
            os.system(EDITOR + ' "' + fpath + '"')
        else:
            if ext_editor == "grip":
                os.system("grip -b" + ' "' + fpath + '"')
            else:
                os.system(ext_editor + ' "' + fpath + '"')

        tags = get_tags_in_file(fpath)
        add_tag_to_base(tags, fpath)

        prev_tags_set = set(prev_tags)
        tags_set = set(tags)
        if prev_tags_set != tags_set:
            log("save tag base")
            save_tag_base()
