from calendar import monthrange
from datetime import datetime, timedelta
from http.client import HTTPException
import sys
import typing

import requests
import logging

import pandas as pd

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


import urllib3

from konfiguration import project_immendingen

from models.auswertung import Monatsbericht, MonatsuebersichtAnImmissionsort  

from monatsbericht.config import *
from models.allgemein import Projekt
from influx_api import read_schallleistungspegel



def read_data_for_monatsbericht(project: Projekt, year: int, month: int, has_mete: bool = False, read_schallleistung = False):
    # project = project_immendingen
    project_name = project.name_in_db
    ios = project.IOs
    number_days_in_month = monthrange(year, month)[1]
    range_start = datetime(year,month,1, 0, 0, 0)
    range_stop = datetime(year,month,1, 0, 0, 0) + timedelta(days=number_days_in_month)

    io_monatsuebersicht: typing.Dict[int, MonatsuebersichtAnImmissionsort] = dict(zip([io.Id for io in project.IOs], [MonatsuebersichtAnImmissionsort(io) for io in ios]))
    
    number_days_in_month = monthrange(range_start.year, range_start.month)[1]
    logging.info(f"Seconds in month: {number_days_in_month*3600*24}")
    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=1000*600) as client:
        if read_schallleistung:
            schallleistungspegel = {}
            df = read_schallleistungspegel(range_start, range_stop, project.name_in_db)
            for idx, row in df.iterrows():
                schallleistungspegel[idx] = row["schallleistungspegel"]
                print(idx, row["schallleistungspegel"])
                

            
        else:
            schallleistungspegel = None

        query_verfuegbare_sekunden = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_auswertungslauf" and r["_field"] == "verfuegbare_sekunden")
            |> group(columns: ["_measurement"])
            |> sum(column: "_value")"""
        df_verfuegbare_sekunden = client.query_api().query_data_frame(query_verfuegbare_sekunden)
        logging.info(f"verfuegbare_sekunden: {df_verfuegbare_sekunden['_value'][0]}")
        logging.info(type(df_verfuegbare_sekunden['_value'][0]))
        query = f'''from(bucket: "dauerauswertung_immendingen")
                |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
                |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_lr" and r["_field"] == "lr" and r["verursacher"] == "gesamt")'''
        query_lauteste_stunde = f'''from(bucket: "dauerauswertung_immendingen")
        |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_lauteste_stunde")
            |> filter(fn: (r) => r["_field"] == "lauteste_stunde")'''
        df : pd.DataFrame = client.query_api().query_data_frame(query)
        df.drop(["table", "_start", "_stop", "_measurement", "_field", "result", "verursacher"], axis=1, inplace=True)
        df = df.astype({'immissionsort': 'int32'})

        df_nachts = df[df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_tagzeitraum = df[~df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        
        for df in [df_tagzeitraum]:
            for io in ios:

                df_an_io = df[df["immissionsort"] == io.Id].set_index(["_time"])
                lr = df_an_io.groupby(by= lambda idx: idx.day).max()

                io_monatsuebersicht[io.Id].lr_tag = lr
                    
        df_tagzeitraum.set_index(["_time", "immissionsort"], inplace=True)
        
        df_nachts["day"] = df_nachts["_time"].dt.day
        df_lr_nachts = df_nachts.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lr_nachts.sort_values(["immissionsort", "day"], inplace=True)
        for io in ios: 
            df_lr_nachts_an_io = df_lr_nachts[df_lr_nachts["immissionsort"] == io.Id].loc[:, ["_time", "_value", "day"]]
            df_lr_nachts_an_io = df_lr_nachts_an_io.set_index(["day"])
            io_monatsuebersicht[io.Id].lr_max_nacht = df_lr_nachts_an_io

        df_lauteste_stunde = client.query_api().query_data_frame(query_lauteste_stunde)
        df_lauteste_stunde.drop(["table", "_start", "_stop", "_measurement", "_field", "result"], axis=1, inplace=True)
        df_lauteste_stunde_nachts = df_lauteste_stunde[df_lauteste_stunde["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_lauteste_stunde_tagzeitraum = df_lauteste_stunde[~df_lauteste_stunde["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_lauteste_stunde_tagzeitraum.loc[:, "day"] = df_lauteste_stunde_tagzeitraum["_time"].dt.day
        df_lauteste_stunde_nachts.loc[:, "day"] = df_lauteste_stunde_nachts["_time"].dt.day
        df_lauteste_stunde_tagzeitraum = df_lauteste_stunde_tagzeitraum.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lauteste_stunde_tagzeitraum.sort_values(["immissionsort", "day"], inplace=True)

        df_lauteste_stunde_nachts = df_lauteste_stunde_nachts.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lauteste_stunde_nachts.sort_values(["immissionsort", "day"], inplace=True)

        for io in ios: 
            io_monatsuebersicht[io.Id].lauteste_stunde_tag = df_lauteste_stunde_tagzeitraum[df_lauteste_stunde_tagzeitraum["immissionsort"] == io.Bezeichnung].loc[:, ["day", "_value", "_time"]].set_index(["day"])
            io_monatsuebersicht[io.Id].lauteste_stunde_nacht = df_lauteste_stunde_nachts[df_lauteste_stunde_nachts["immissionsort"] == io.Bezeichnung].loc[:, ["day", "_value", "_time"]].set_index(["day"])
        
        if has_mete:
            q_aussortiert_wetter = f"""from(bucket: "dauerauswertung_immendingen")
                |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
                |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung" and contains(value: r["_value"], set: ["wind", "regen"]))
                |> group(columns: ["_measurement"])
                |> count()"""
            df_aussortiert_wetter = client.query_api().query_data_frame(q_aussortiert_wetter)
            if not df_aussortiert_wetter.empty:
                logging.info(f"q_aussortiert_wetter: {df_aussortiert_wetter['_value'][0]}")
                wegen_wetter_aussortiert = df_aussortiert_wetter['_value'][0]
            else:
                wegen_wetter_aussortiert = 0
        else:
            wegen_wetter_aussortiert= 0

        q_aussortiert_gesamt = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung") |> group(columns: ["_measurement"])
            |> count()"""
        df_aussortiert_gesamt = client.query_api().query_data_frame(q_aussortiert_gesamt)
        logging.info(f"q_aussortiert_gesamt: {df_aussortiert_gesamt['_value'][0]}")
        q_aussortiert_sonstiges = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung" and not contains(value: r["_value"], set: ["wind", "regen"])) |> group(columns: ["_measurement"])
            |> count()"""
        df_aussortiert_sonstiges = client.query_api().query_data_frame(q_aussortiert_sonstiges)

        logging.info(f"q_aussortiert_sonstiges: {df_aussortiert_sonstiges['_value'][0]}")

        a = Monatsbericht(range_start, project,
                        df_verfuegbare_sekunden['_value'][0], wegen_wetter_aussortiert,
                        df_aussortiert_sonstiges['_value'][0], "blub", io_monatsuebersicht, schallleistungspegel)
        return a
