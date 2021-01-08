#!/usr/bin/env python3

import PySimpleGUI as sg

# import tkinter

sg.theme("dark grey 9")
# Define the window's contents
layout = [
    [sg.Text("What's your name?")],
    [sg.Input(key="-INPUT-")],
    [sg.Text(size=(40, 1), key="-OUTPUT-")],
    [sg.Button("Ok"), sg.Button("Quit")],
]

# Create the window
window = sg.Window("Window Title", layout)

# Display and interact with the Window using an Event Loop
while True:
    event, values = window.read()
    # See if user wants to quit or window was closed
    if event == sg.WINDOW_CLOSED or event == "Quit":
        break
    # Output a message to the window
    window["-OUTPUT-"].update("Hello " + values["-INPUT-"] + "! Thanks for trying PySimpleGUI", text_color="yellow")

# Finish up by removing from the screen
window.close()
