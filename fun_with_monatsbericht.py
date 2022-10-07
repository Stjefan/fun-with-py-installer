
from monatsbericht.connect_2_influx_db import read_data_for_monatsbericht
from monatsbericht.monatsbericht import erstelle_xslx_monatsbericht
from konfiguration import project_mannheim, project_immendingen, project_sindelfingen
import logging
import sys

import argparse
import pathlib

import shutil

# Hinweis:
# Zum verschieben auf das Scan-Verzeichnis:
# In Powershell als Admin: Move-Item -Path C:\CalcMessdaten\SQLiteDatabaseBrowserPortable\August_IO_17_Beurteilungspegel.csv -Destination \\kuf-srv-01\Scan\
# z.B: Move-Item -Path ./Monatsbericht_07_22.xlsx -Destination \\kuf-srv-01\Scan\

FORMAT = '%(filename)s %(lineno)d %(asctime)s %(levelname)s %(message)s'
use_as_cli = False
use_as_script = not use_as_cli
if __name__ == '__main__':
    logging.basicConfig(
            level=logging.INFO, format=FORMAT, handlers=[logging.FileHandler("monatsbericht.log"),
            logging.StreamHandler(sys.stdout)]
        )

    if use_as_cli:
        parser = argparse.ArgumentParser(description='Erstellt Monatsbericht')
        parser.add_argument('--year', type=int, required=True,
                            help='Jahr des Monatsberichts')

        parser.add_argument('--month', type=int, required=True,
                            help='Monat des Monatsberichts')

        parser.add_argument('--path', type=pathlib.Path, required=True,
                            help='Ort, an dem die Output-xlsx gespeichert wird')

        args = parser.parse_args()

        
        
        logging.info(f"Erstelle Monatsbericht für {args.month} {args.year}")
        # py .\fun_with_monatsbericht.py --year 2022 --month 4 --path ./monatsbericht_mannheim_04_22.xlsx
        m = read_data_for_monatsbericht(project_mannheim, args.year, args.month)
        erstelle_xslx_monatsbericht(m, args.path)
        logging.info(f"Monatsbericht erfolgreich in {args.path} gespeichert")

    if use_as_script:
        year = 2021
        project = project_sindelfingen
        for month in [12]: # 1, 7, 8, 9, 10, 11, 
            logging.info(f"Create report for {month}")
            path_monatsbericht = f"{project.name}_{year}_{month:02d}.xlsx"
            m = read_data_for_monatsbericht(project, year, month, project.has_mete_data, True)
            if True:
                erstelle_xslx_monatsbericht(m, path_monatsbericht, True)
                logging.info(f"Monatsbericht erfolgreich in {path_monatsbericht} gespeichert")
                # shutil.move(path_monatsbericht, "//kuf-srv-01/scan/" + path_monatsbericht)

