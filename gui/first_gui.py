#!/usr/bin/env python3

import PySimpleGUI as sg

sg.theme("Dark Blue 3")  # please make your windows colorful

# ------ Menu Definition ------ #
menu_def = [
    ["&File", ["&Open", "&Save", "---", "Properties", "E&xit"]],
    ["&Edit", ["Paste", ["Special", "Normal",], "Undo"],],
    ["&Help", "&About..."],
]

layout = [
    [sg.Text("Rename files or folders")],
    [sg.Text("Source for Folders", size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
    [sg.Text("Source for Files ", size=(15, 1)), sg.InputText(), sg.FolderBrowse()],
    [sg.Submit(), sg.Cancel()],
]

window = sg.Window("Rename Files or Folders", layout)

event, values = window.read()
window.close()
folder_path, file_path = values[0], values[1]  # get the data from the values dictionary
print(folder_path, file_path)
