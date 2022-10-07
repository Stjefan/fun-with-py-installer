from time import sleep


def read_file():
    try:
        print("good times are gone...")
        with open('readme.txt', 'r') as f:
            output = f.read()
            print(output)
    except Exception as e:
        newWindow = Toplevel(root)
 
        # sets the title of the
        # Toplevel widget
        newWindow.title("An error occured")
    
        # sets the geometry of toplevel
        newWindow.geometry("200x200")
    
        # A Label widget to show in toplevel
        Label(newWindow,
            text =f"{e}").pack()


# function to open a new window
# on a button click
def openNewWindow():
     
    # Toplevel object which will
    # be treated as a new window
    read_file()
    newWindow = Toplevel(root)
 
    # sets the title of the
    # Toplevel widget
    newWindow.title("New Window")
 
    # sets the geometry of toplevel
    newWindow.geometry("200x200")
 
    # A Label widget to show in toplevel
    Label(newWindow,
          text ="This is a new window").pack()


def blub():
    print("Rising sun...")
    print("You begin to wonder...")
    sleep(5)

from tkinter import *
from tkinter import ttk
root = Tk()
frm = ttk.Frame(root, padding=10)
frm.grid()
ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
ttk.Button(frm, text="Blub", command=openNewWindow).grid(column=2, row=0)
root.mainloop()