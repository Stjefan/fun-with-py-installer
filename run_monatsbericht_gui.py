import logging
from msilib.schema import Error
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showerror, showinfo
from tkinter.filedialog import asksaveasfile, askdirectory
import requests
import os
from monatsbericht.connect_2_influx_db import read_data_for_monatsbericht
from monatsbericht.monatsbericht import erstelle_xslx_monatsbericht
from konfiguration import project_mannheim, project_immendingen
from datetime import datetime


def project_selection(arg):
    if arg == "Mannheim":
        return project_mannheim
    elif arg == "Immendingen":
        return project_immendingen
    else: raise Error("Invalid option")

def run_gui():
    # root window
    root = tk.Tk()
    root.title('Monatsbericht-Creator')
    root.geometry('500x200')
    root.resizable(True, True)

    def month_changed(event):
        """ handle the month changed event """
        pass # selected_year.set(selected_month.get())
        
        

    def fahrenheit_to_celsius(f):
        """ Convert fahrenheit to celsius
        """
        return (f - 32) * 5/9


    # frame
    frame = ttk.Frame(root)


    # field options
    options = {'padx': 5, 'pady': 5}

    # temperature label
    # temperature_label = ttk.Label(frame, text='Fahrenheit')
    # temperature_label.grid(column=0, row=0, sticky='W', **options)

    # another label
    # another_label = ttk.Label(frame, text='Monat')
    # another_label.grid(column=0, row=1, sticky='W', **options)

    # temperature entry
    zielverzeichnis = tk.StringVar()
    # temperature_entry = ttk.Entry(frame, textvariable=temperature)
    # temperature_entry.grid(column=1, row=0, **options)
    # temperature_entry.focus()

    # convert button

    def download_file():
        try:
            # url = "https://www.python.org/static/img/python-logo@2x.png"
            

            
            if selected_month.get() in ["", None]:
                showerror(title='Fehler', message = "Kein Monat ausgewählt")
                return
            if selected_year.get() in ["", None]:
                showerror(title='Fehler', message = "Kein Jahr ausgewählt")
                return
            if zielverzeichnis.get() in ["", None]:
                showerror(title='Fehler', message = "Kein Zielverzeichnis ausgewählt")
                return
            project = project_selection(selected_project.get())
            # print(r.content)
            '''
            deprecated
            url = f"http://kuf-srv-02:8080/Monatsbericht/Download?projektId=1&monat={selected_month.get()}&jahr={selected_year.get()}"
            r = requests.get(url, allow_redirects=True)
            print(r.headers.get('content-type'))
            r.raise_for_status()
            target_file = os.path.join(temperature.get(), f"Monatsbericht_Immendingen_{selected_year.get()}_{int(selected_month.get()):02d}.xlsx")
            open(target_file, 'wb').write(r.content)
            showinfo(title="Erfolg", message=f"Monatsbericht in {target_file} erstellt")
            
            url = f"http://kuf-srv-02:8080/Monatsbericht/Data?projektId=1&monat={selected_month.get()}&jahr={selected_year.get()}"
            r = requests.get(url, allow_redirects=True)

            filename_monatsbericht_json = f'monatsbericht_{int(selected_month.get()):02d}_{selected_year.get()}.json'
            open(filename_monatsbericht_json, 'wb').write(r.content)
            target_file = os.path.join(temperature.get(), f"Monatsbericht_Immendingen_{selected_year.get()}_{int(selected_month.get()):02d}.xlsx")
            monatsbericht.write_monatsbericht_v2(filename_monatsbericht_json, target_file)
            '''
            target_file = os.path.join(zielverzeichnis.get(), f"Monatsbericht_{project.name}_{selected_year.get()}_{int(selected_month.get()):02d}.xlsx")
            m = read_data_for_monatsbericht(project, int(selected_year.get()), int(selected_month.get()))
            erstelle_xslx_monatsbericht(m, target_file)

            
        except Exception as error:
            showerror(title='Error', message=error)

    def convert_button_clicked():
        """  Handle convert button click event 
        """
        try:
            # f = float(temperature.get())
            # c = fahrenheit_to_celsius(f)
            # result = f'{f} Fahrenheit = {c:.2f} Celsius'
            # result_label.config(text=result)
            returned_folder = askdirectory(title="Verzeichnis für Monatsbericht wählen")
            if returned_folder is not None:
                print(returned_folder)
                zielverzeichnis.set(returned_folder)
        except ValueError as error:
            showerror(title='Error', message=error)




    convert_button = ttk.Button(frame, text='Monatsbericht erstellen')
    convert_button.grid(column=2, row=5, sticky='W', **options)
    convert_button.configure(command=download_file)


    another_button = ttk.Button(frame, text='...')
    another_button.grid(column=2, row=4, sticky='W', **options)
    another_button.configure(command=convert_button_clicked)


    project_label = ttk.Label(frame, text='Projekt')
    project_label.grid(column=0, row=1, sticky='W', **options)

    # another label
    monat_label = ttk.Label(frame, text='Monat')
    monat_label.grid(column=0, row=2, sticky='W', **options)

    # another label
    year_label = ttk.Label(frame, text='Jahr')
    year_label.grid(column=0, row=3, sticky='W', **options)

    # another label
    target_folder = ttk.Label(frame, text='Zielordner')
    target_folder.grid(column=0, row=4, sticky='W', **options)

    # another label
    target_folder = ttk.Label(frame, textvariable=zielverzeichnis)
    target_folder.grid(column=1, row=4, sticky='W', **options)


    # result label
    result_label = ttk.Label(frame)
    result_label.grid(row=1, columnspan=3, **options)


    # create a combobox
    selected_month = tk.StringVar()
    selected_month.set(datetime.now().month)
    month_cb = ttk.Combobox(frame, textvariable=selected_month)

    month_cb['values'] = [m for m in range(1, 13)]

    # prevent typing a value
    month_cb['state'] = 'readonly'
    month_cb.bind('<<ComboboxSelected>>', month_changed)


    # place the widget
    month_cb.grid(column=1, row=2, sticky='W', **options)


    selected_year = tk.StringVar()
    year_cb = ttk.Combobox(frame, textvariable=selected_year)

    # get first 3 letters of every year name
    year_cb['values'] = [m for m in range(2021, 2021+10)]
    year_cb.set(datetime.now().year)

    # prevent typing a value
    year_cb['state'] = 'readonly'


    

    # place the widget
    year_cb.grid(column=1, row=3, sticky='W', **options)


    selected_project = tk.StringVar()
    project_cb = ttk.Combobox(frame, textvariable=selected_project)

    # get first 3 letters of every year name
    project_cb['values'] = ["Immendingen", "Mannheim"]
    project_cb["state"] = "readonly"
    project_cb.set(project_cb['values'][0])
    project_cb.grid(column=1, row=1, sticky='W', **options)


    # add padding to the frame and show it
    frame.grid(padx=10, pady=10)







    # start the app
    root.mainloop()



if __name__ == '__main__':

    FORMAT = '%(filename)s %(lineno)d %(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
            level=logging.INFO, format=FORMAT, handlers=[logging.FileHandler("monatsbericht_gui.log"),
            logging.StreamHandler(sys.stdout)]
        )
    try:
        run_gui()
    except Exception as e:
        logging.exception(e)

