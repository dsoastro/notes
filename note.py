import os
import subprocess
import datetime
import re
from functools import cmp_to_key
from note_conf import PATH, HISTORY_LOCATION, PHONE, TAGDB
from common import load_dir_history, load_file_history, save_file_history, search_file_history, search_dir_history, \
    add_to_dir_history, save_dir_history
from common import create_file_if_not_exist, show_or_edit_file, print_file, parse_command
from common import EDIT_FILE, SHOW_FILE, NEW_FILE, Commands
from tags import TagProcessor, save_tag_base, get_tag_list, get_paths_by_tag
from error import MyError, log
from update_tag_db import update_tags
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import traceback

def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))

class Taglist:
    def __init__(self, path):
        self.path = path
        self.entries = {}

    def get_name(self):
        return "tag: "

    def _print_names(self):
        i = 0
        for i in range(len(self.entries)):
            name = self.entries[i]
            print(i, name.replace(PATH, ""))

    def _make_and_print_names(self, tagset):
        ''' flist - list of strings '''

        if len(tagset) == 0:
            self.entries = {}
            print("No match")
            return DirectoryList(self.path)

        else:
            i = 0
            self.entries = {}
            for name in tagset:
                self.entries[i] = name
                print(i, name.replace(PATH, ""))
                i += 1
            return self

    def act(self, command):
        parsed = parse_command(command)
        log("taglist parsed", parsed)

        if parsed["command"] == Commands.T:
            arg = parsed["args"][0]
            log("arg", arg)
            tags = arg.split()
            log("tags", tags)
            if len(tags) == 0:
                return DirectoryList(self.path).act(command)

            paths = get_paths_by_tag(tags[0])
            if paths is None:
                print("Tag", tags[0], "is not available")
                return self._make_and_print_names([])

            all_set = set(paths)
            for i in range(1, len(tags)):
                paths = get_paths_by_tag(tags[i])
                if paths is None:
                    print("Tag", tags[i], "is not available")
                    all_set = set()
                    break
                tag_set = set(paths)

                all_set = all_set.intersection(tag_set)

            log("Tlist, act ", all_set)
            return self._make_and_print_names(all_set)

        elif parsed["command"] == Commands.L:
            self._print_names()
            return self

        elif parsed["command"] == Commands.EDIT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                fpath = self.entries[index]

            show_or_edit_file(fpath, EDIT_FILE, ext_editor=parsed["args"][1])
            return self

        # show content
        elif parsed["command"] == Commands.CAT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                name = self.entries[index]

            show_or_edit_file(name, SHOW_FILE)
            return self

        # show content
        elif parsed["is_index"] == True:
            index = parsed["index"]
            log("index", index)
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                fpath = self.entries[index]

            log("fpath", fpath)
            show_or_edit_file(fpath, SHOW_FILE)
            return self

        else:
            return DirectoryList(self.path).act(command)

class Flist:
    def __init__(self, path):
        self.path = path
        self.entries = {}

    def get_name(self):
        return "f: "

    def _print_names(self):
        i = 0
        for i in range(len(self.entries)):
            name = self.entries[i]
            print(i, name.replace(PATH, ""))

    def _make_and_print_names(self, flist):
        ''' flist - list of strings '''

        if len(flist) == 0:
            self.entries = {}
            print("No match")
            return DirectoryList(self.path)

        else:
            i = 0
            self.entries = {}
            for name in flist:
                self.entries[i] = name
                print(i, name.replace(PATH, ""))
                i += 1
            return self

    def act(self, command):
        parsed = parse_command(command)
        # log("parsed", parsed)

        if parsed["command"] == Commands.F:
            arg = parsed["args"][0]
            flist = search_file_history(arg)
            log("Flist, act ", flist, len(flist))
            return self._make_and_print_names(flist)

        elif parsed["command"] == Commands.L:
            self._print_names()
            return self

        elif parsed["command"] == Commands.EDIT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                fpath = self.entries[index]

            show_or_edit_file(fpath, EDIT_FILE, ext_editor=parsed["args"][1])
            return self

        # show content
        elif parsed["command"] == Commands.CAT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                name = self.entries[index]

            show_or_edit_file(name, SHOW_FILE)
            return self

        # show content
        elif parsed["is_index"] == True:
            index = parsed["index"]
            log("index", index)
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                fpath = self.entries[index]

            log("fpath", fpath)
            show_or_edit_file(fpath, SHOW_FILE)
            return self

        else:
            return DirectoryList(self.path).act(command)

class Zdir:
    def __init__(self, path):
        self.path = path
        self.entries = {}

    def get_name(self):
        return "z: "

    def _change_dir(self, index):
        ''' change dir to the self.entries[index]'''

        # selected dir is somehow not a dir
        if not os.path.isdir(self.entries[index]):
            # just in case
            print(repr(self.entries[index]), " not a directory")
            return DirectoryList(self.path)
        else:
            print("Directory changed to", self.entries[index])
            return DirectoryList(self.entries[index])

    def _print_names(self):
        i = 0
        for i in range(len(self.entries)):
            name = self.entries[i]
            print(i, name.replace(PATH, ""))

    def _make_and_print_names(self, dirlist):
        ''' dirlist - list of strings '''

        if len(dirlist) == 0:
            self.entries = {}
            print("No match")
            return DirectoryList(self.path)
        else:

            if len(dirlist) == 1:  # just one item, go there
                self.entries = {}
                self.entries[0] = dirlist[0]
                return self._change_dir(0)
            else:
                i = 0
                self.entries = {}
                for name in dirlist:
                    self.entries[i] = name
                    print(i, name.replace(PATH, ""))
                    i += 1
                return self

    def act(self, command):
        parsed = parse_command(command)

        if parsed["command"] == Commands.Z:
            arg = parsed["args"][0]
            dirlist = search_dir_history(arg)
            log("Zdir, act, dirlist: ", dirlist, len(dirlist))
            return self._make_and_print_names(dirlist)

        elif parsed["command"] == Commands.L:
            self._print_names()
            return self

        elif parsed["is_index"] or parsed["command"] == Commands.CD:
            if parsed["command"] == Commands.CD:
                try:
                    index = int(parsed["args"][0].strip())
                except:
                    return DirectoryList(self.path).act(command)
            else:
                index = parsed["index"]

            if index >= len(self.entries):
                raise MyError("Wrong index: " + str(index))
            else:
                return self._change_dir(index)

        else:
            return DirectoryList(self.path).act(command)

class Search:
    def __init__(self, path):
        self.path = path
        self.entries = {}
        self.search_word = None

    def get_name(self):
        return "search: "

    def _print_search_result(self):
        for i, p in self.entries.items():
            print(i, p.replace(PATH, ""))

    def act(self, command):
        parsed = parse_command(command)

        if parsed["command"] == Commands.SEARCH:
            name = parsed["args"][0]
            self.search_word = name
            name_only = parsed["args"][1]["name_only"]
            self.make_search(name, name_only)
            self._print_search_result()
            return self

        elif parsed["command"] == Commands.L:
            self._print_search_result()
            return self

        # if just index, show its content
        elif parsed["is_index"]:
            index = parsed["index"]
            if index >= len(self.entries):
                raise MyError("Wrong index: " + str(index))
            else:
                name = self.entries[index]
                show_or_edit_file(name, SHOW_FILE, search_word=self.search_word)
            return self

        # show content
        elif parsed["command"] == Commands.CAT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                name = self.entries[index]

            show_or_edit_file(name, SHOW_FILE, search_word=self.search_word)
            return self

        # editing file
        elif parsed["command"] == Commands.EDIT:
            index = parsed["args"][0]
            if index >= len(self.entries):
                raise MyError("Wrong index:" + str(index))
            else:
                fpath = self.entries[index]
                show_or_edit_file(fpath, EDIT_FILE, ext_editor=parsed["args"][1])
                return self

        else:
            return DirectoryList(self.path).act(command)

    def _grep_search_on_phone(self, text):
        '''
        only busybox grep works with cyrillic
        :param text:
        :return:
        '''
        out = ""
        has_git = False

        for name in os.listdir(self.path):
            fpath = os.path.join(self.path, name)
            if ".git" in fpath:
                has_git = True
                break

        if has_git:
            for name in os.listdir(self.path):
                fpath = os.path.join(self.path, name)
                if ".git" in fpath:
                    continue

                if os.path.isdir(fpath):  # dir
                    try:
                        log(fpath)
                        s = subprocess.check_output(["busybox", "grep", "-ril", text, fpath]).decode("utf-8")
                        out += s
                    except Exception as e:
                        log("3", e)
                        pass  # print(e)


                else:  # regular file
                    try:
                        s = subprocess.check_output(["busybox", "grep", "-il", text, fpath]).decode("utf-8")
                        out += s
                    except  Exception as e:
                        log("4", e)
                        pass  # print(e)
        else:
            try:
                s = subprocess.check_output(["busybox", "grep", "-ril", text, self.path]).decode("utf-8")
                out += s
            except  Exception as e:
                log("5", e)
                pass  # print(e)

        return out

    def make_search(self, text, name_only=False):

        out = ""
        gitpath = os.path.join(PATH, ".git")
        if not name_only:
            if PHONE and has_cyrillic(text):
                out += self._grep_search_on_phone(text)

            else:
                # gitpath = os.path.join(PATH, ".git")
                try:
                    log("gitpath", gitpath)
                    s = subprocess.check_output(["grep", '--exclude-dir=.git', '-riIl', text, self.path]).decode(
                        "utf-8")
                    out += s
                except Exception as e:
                    log("1", e)
                    pass
        try:
            fpath = self.path
            if not fpath.endswith("/"):
                fpath += "/"  # need this for phone where notes is a symbolic link, not a true directory
            log("find, path", fpath)
            log("gitpath", gitpath)
            s = subprocess.check_output(
                ["find", fpath, "-path", gitpath, "-prune", "-o", "-iname", '*' + text + '*', "-print"]).decode("utf-8")

            out += s
        except Exception as e:
            log("2", e)
            pass

        aset = set()
        i = 0
        self.entries = {}
        for p in out.split("\n"):
            # exlude tagdb from search
            if p != "" and TAGDB not in p:  # and not ".jpeg" in p and not ".jpg" in p and not ".png" in p and not ".class" in p
                aset.add(p)

        for p in aset:
            self.entries[i] = p
            i += 1

class DirectoryList:
    def __init__(self, path):
        self.path = path
        self.entries = {}

    def get_name(self):
        return "list: "

    def _show_dir_content(self):
        self.entries = {}
        self.entries[0] = ".."
        print(0, "dir\t", self.entries[0])
        i = 1

        def compare_names(lhs, rhs):
            ltime = os.path.getmtime(os.path.join(self.path, lhs))
            rtime = os.path.getmtime(os.path.join(self.path, rhs))
            if ltime < rtime:
                return 1
            elif ltime == rtime:
                return 0
            else:
                return -1

        content = sorted(os.listdir(self.path), key=cmp_to_key(compare_names))

        for name in content:
            self.entries[i] = name
            fpath = os.path.join(self.path, name)
            isdir = os.path.isdir(fpath)
            tp = TagProcessor(name)
            tags = tp.get_non_time_tag_str()
            out_name = tp.getNameWithoutTags() + ("\t" + tags if tags is not None else "")
            print(i, "dir\t" if isdir else "\t", out_name)

            i += 1

    def act(self, command):
        parsed = parse_command(command)

        # show dir content
        if parsed["command"] == Commands.L:
            self._show_dir_content()

        # switching to dirlist view from everywhere
        elif parsed["command"] == Commands.LIST:
            # just stay here
            pass

        elif parsed["is_index"]:
            index_ = parsed["index"]
            try:
                name = self.entries[index_]
            except:
                raise MyError("Wrong index:" + str(index_))

            fpath = os.path.join(self.path, name.strip())

            if os.path.isdir(fpath):
                return DirectoryList(self.path).act("cd " + name.strip())
            else:
                show_or_edit_file(fpath, SHOW_FILE)

        # show file content
        elif parsed["command"] == Commands.CAT:
            index = parsed["args"][0]
            try:
                name = self.entries[index]
            except:
                raise MyError("Wrong index:" + str(index))

            fpath = os.path.join(self.path, name)
            show_or_edit_file(fpath, SHOW_FILE)

        # change dir
        elif parsed["command"] == Commands.CD:

            name = parsed["args"][0]  # "" if command = cd
            if len(name) > 0:
                try:
                    index = int(name)
                    name = self.entries[index]
                except:
                    # either not a number, or number out of range
                    pass

            if name == "":
                fpath = PATH
            else:
                fpath = os.path.join(self.path, name.strip())
            if os.path.isdir(fpath):
                absfpath = os.path.abspath(fpath)  # to deal with ..
                print("Directory changed to", absfpath)
                self.path = absfpath
                self.entries = {}
                add_to_dir_history(absfpath)
                save_dir_history()

        # printing current working dir
        elif parsed["command"] == Commands.PWD:
            print("Current directory", self.path)

        elif parsed["command"] == Commands.UPDATE_TAG_DB:
            update_tags()
        # editing file
        elif parsed["command"] == Commands.EDIT:
            index = parsed["args"][0]
            try:
                name = self.entries[index]
            except:
                raise MyError("Wrong index:" + str(index))

            fpath = os.path.join(self.path, name)
            show_or_edit_file(fpath, EDIT_FILE, ext_editor=parsed["args"][1])

        # new note
        elif parsed["command"] == Commands.NEW_NOTE:
            name = parsed["args"][0]
            tmp_path = os.path.join(self.path, name)
            now = datetime.datetime.now()
            if os.path.exists(tmp_path):
                tagged_name = TagProcessor(name).addTimeTag(now)
            else:
                tagged_name = name
            fpath = os.path.join(self.path, tagged_name)
            log("new, fpath=", fpath)
            mid = TagProcessor("").addTimeTag(now).replace("[", "").replace("]", "")
            show_or_edit_file(fpath, NEW_FILE, ext_editor=parsed["args"][1], mid=mid)

        elif parsed["command"] == Commands.TAGS:
            for tag in get_tag_list():
                print(tag)
        # quick directory search
        elif parsed["command"] == Commands.Z:
            return Zdir(self.path).act(command)
        elif parsed["command"] == Commands.F:
            return Flist(self.path).act(command)
        elif parsed["command"] == Commands.SEARCH:
            return Search(self.path).act(command)
        elif parsed["command"] == Commands.T:
            return Taglist(self.path).act(command)
        else:
            raise MyError("Unknown command: " + command)

        return self

def main():
    proc = None
    load_dir_history()
    load_file_history()
    prompt_history_path = HISTORY_LOCATION + ".prompt_history"
    create_file_if_not_exist(prompt_history_path)
    session = PromptSession(history=FileHistory(prompt_history_path))
    while True:
        if proc is None:
            proc = DirectoryList(PATH)
        try:
            print()
            s = session.prompt(proc.get_name(), auto_suggest=AutoSuggestFromHistory())

            if s[:4] == "exit":
                save_dir_history()
                save_file_history()
                save_tag_base()
                return
            elif s[:4] == "help":
                app_path = os.path.split(__file__)[0]
                help_path = os.path.join(app_path, "help.txt")
                print_file(help_path)
                continue

            log(proc)
            proc = proc.act(s)

        except MyError as e:
            print(e)
        except Exception as e:
            traceback.print_exc()

main()
