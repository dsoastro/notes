# Notes

The python CLI application for managing text notes on Linux (in fact, a convenient python wrapper over Linux commands: grep, find, nano, etc.). It provides for note efficient search, selection and creation in zsh-like command style. The notes are kept as usual files on Linux filesystem. You could open them with any other application as well (file manager, editor, etc).

The app also works with GUI editors ("gedit", "sublime", "vim", "nano", "atom", "grip", "mdless", "code") to look through / edit notes. The list of editors could be extended by amending the EDITOR_LIST variable. The app keeps the input history and provides for autocompletion.

The author uses the app to organise and quickly search through several thousands notes.
## Installation
```
git clone https://github.com/dsoastro/notes
cd notes
pip3 install -r requirements.txt
```

## Get Started

Create folder structure for note keeping with file manager / linux commands. In note_conf.py file set the app root folder in PATH variable, the path to the app history file in HISTORY_LOCATION and your preferred editor (e.g. nano, vim) in EDITOR variables.
Run the app:
```
python3 note.py
```

Enter `l` to list files in the current folder. The possible output:
```
list: l
0 dir	 ..
1 	 wireguard.txt
2 	 Carbonyl.txt
3 	 dia.txt
4 	 gocryptfs.txt
5 	 obsidian.txt
6 	 wireshark.txt	
```
Enter `1` to show the content of the first file, `e 1` to edit it with the default editor, `e 1 editor=gedit` to edit it with gedit. `s text_to_search` to search recursively through all files in the current folder and below, `n abc.txt` to create a new file in the current folder.

## Usage on android phone

Install Termux (the Linux emulator). Run the app inside. Set PHONE variable in note_conf.py to True.
## Full list of commands
```
c 1               cat file # 1
cat 1             cat file # 1
e 1               edit file #1
e 1 editor=gedit  edit file #1 using gedit
n file.txt        create new file.txt
n file.txt editor=gedit   create new file.txt using gedit
cd 1              change folder to #1
cd folder         change folder to folder
pwd               print working directory
tags              show list of available tags
list              change program state to main (list)
l                 list files
update_tag_db     update tags database
s word            search for word in current folder and below
s word --name     search for word in current folder and below in file names only
z dirword         change to directory which name contains dirword among recently used
f fileword        go to file which name contains fileword among recently used
t tag1 tag2       list files with tag1 and tag2
help              show this help
```

If a file contains a string like:  
```
tags: abc def
```  
then the note will be tagged with "abc" and "def" tags.

To show markdown files with formatting:
```
e 1 editor=grip   (in browser)
e 1 editor=mdless (in command line)
e 1 editor=code (gui)
```
for that:
```
https://unix.stackexchange.com/questions/4140/markdown-viewer

pip install grip
sudo gem install mdless
sudo apt install code
```

## Synchronisation

Use any external tool (git, dropbox, etc.). The author prefers `git` so the app ignores `.git` folder when searching for notes.