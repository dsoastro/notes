import os
from tags import get_tags_in_file, add_tag_to_base, clear_tag_dict, save_tag_base
from note_conf import PATH

def update_tags():
    clear_tag_dict()
    for root, subdirs, files in os.walk(PATH):
        for file in files:
            if ".git" in file or ".git" in root:
                continue
            path = os.path.join(root,file)
            tags = get_tags_in_file(path)
            add_tag_to_base(tags,path)

    save_tag_base()