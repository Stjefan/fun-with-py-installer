from calendar import monthrange
from datetime import datetime, timedelta
from http.client import HTTPException
import sys
import typing

import requests
import logging

import pandas as pd
import numpy as np

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pathlib import Path

import urllib3

from konfiguration import project_immendingen
from models.auswertung import Ueberschreitungspruefung
from models.auswertung import Monatsbericht, MonatsuebersichtAnImmissionsort  

from calendar import monthrange


# sts
token = "QRNlK60Noca9m2WIjgUSHaE3C1PGnzNZ-qHY1MajJBSDIjkpJdxPwJ1bG11cOYJREvLgEp8D5h_xH1AhvgvBww=="
org = "kufi"
bucket = "dauerauswertung_immendingen"
bucket_id = "2418514fd1ce2ed6"
org_id = "305097082a5e4648"

# KUF-Server
token = "0ql08EobRW6A23j97jAkLyqNKIfQIKJS9_Wrw4mWIqBu795dl4cSfaykizl261h-QwY9BPDMUXbDCuFzlPQsfg=="
org = "kufi"
bucket = "dauerauswertung_immendingen"
bucket_id = "c6a3680b6746e4d8"
org_id = "ea7b98ca8acb0b14"

# docker
token = "6DeLFWxoSLGGZg5Yv2rpqUlaKJqaTio565N5EyS5AOrW-2KZ3u95AeeoVqorntQPgpiOgdVE7TqjQRn8qF0v9Q=="
org = "kufi"
bucket = "dauerauswertung_immendingen"
bucket_id = "d7f7cc8868f26bc9"
org_id = "08a2c94b75be2389"



influx_url = "http://localhost:8086"

ISOFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def do_dbrps_mapping():
    try:
        r = requests.post("http://localhost:8086/api/v2/dbrps",
                          json={"bucketID": f"{bucket_id}", "database": "dauerauswertung_immendingen",
                                "default": True, "orgID": f"{org_id}", "retention_policy": "example-rp"},
                          headers={"Authorization": f"Token {token}", 'Content-type': "application/json"})
        r.raise_for_status()
        print(r.content)
    except Exception as e:
        print(e)
        print(r.content)


if False:
    def delete_data():
        try:
            r = requests.post(f"http://localhost:8086/api/v2/delete?org={org}&bucket={bucket}",
                            json={
                                "start": "2022-07-01T00:00:00Z",
        "stop": "2022-7-28T00:00:00Z",
        "predicate": "_measurement=\"auswertung_immendingen_erkennung\""
                            },
                            headers={"Authorization": f"Token {token}", 'Content-type': "application/json"})
            r.raise_for_status()
            print(r.content)
        except HTTPException as e:
            print(e)
            print(e.response.content)


def query_4_korrelationsmessung_part_1():
    all_dfs = []
    first_iteration = True
    for v in ["gesamt", "mp5_vorbeifahrt"] + [f"mp{i}_ohne_ereignis" for i in [1, 2, 3, 4, 5, 6]]:
        query = f'''from(bucket: "dauerauswertung_immendingen") |> range(start: 2022-06-15, stop: 2022-07-10)
            |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_lr")
            |> filter(fn: (r) => r["_field"] == "lr")
            |> filter(fn: (r) => r["immissionsort"] == "17")
            |> filter(fn: (r) => r["verursacher"] == "{v}")
            |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
            |> yield(name: "maxlr")'''
        with InfluxDBClient(url=influx_url, token=token, org=org) as client:
            df = client.query_api().query_data_frame(query)
            
            
            df.drop(["table", "_start", "_stop", "_measurement", "immissionsort", "_field", "result", "verursacher"], axis=1, inplace=True)
            # print(df)            
            df = df.set_index("_time")
            df = df.resample("H").max().reset_index()
            df = df[df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5, 6, 23])]
            df = df.set_index("_time")
            if not first_iteration:
                result_df = pd.merge(result_df, df, suffixes=["", v], left_index=True, right_index=True)
            else:
                result_df = df
            first_iteration = False
    filepath = Path('./korrelationsmessung_15_06_22_bis_07_10_22_vergleichswerte_calcmes.csv')  
    result_df.to_csv(filepath, decimal=',', sep=';')
    print(result_df)   

def query_4_korrelationsmessung_part_2():
    query = '''from(bucket: "dauerauswertung_immendingen") |> range(start: 2022-06-15, stop: 2022-07-10)
  |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_korrelationsmessung_lr")
  |> filter(fn: (r) => r["_field"] == "lr")
  |> filter(fn: (r) => r["verursacher"] == "gesamt")
  |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
  |> yield(name: "maxlr")'''
    with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        df = client.query_api().query_data_frame(query)
        # df = df[df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5, 6, 23])]
        df.drop(["table", "_start", "_stop", "_measurement", "immissionsort", "_field", "result", "verursacher"], axis=1, inplace=True)
        df = df.set_index("_time")
        print(df)
        
        filepath = Path('./korrelationsmessung_15_06_22_bis_07_10_22.csv')  
        df.to_csv(filepath, decimal=',', sep=';')
        # query(query, org=org)
        # for table in tables:
        #     for record in table.records:
        #         print(record)

# do_dbrps_mapping()
# delete_data()
# query_4_korrelationsmessung_part_1()
# query_4_korrelationsmessung_part_2()

def query_resu(range_start: datetime, range_stop: datetime):
    project_name = "mannheim"
    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=1000*600) as client:
        query_verfuegbare_sekunden = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "messwerte_{project_name}_resu" and r["_field"] == "lafeq" and r["messpunkt"] == "Mannheim MP 2")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")"""
        result = client.query_api().query_data_frame(query_verfuegbare_sekunden)
        result = result[["_time", "lafeq"]]
        
        result = result.set_index("_time")
        return result



def query_counting_available_values_per_day():
    with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        query_taking_much_too_long = f'''from(bucket: "dauerauswertung_immendingen")
  |> range(start: 2022-06-01, stop: 2022-07-01)
  |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_aussortierung")
  |> filter(fn: (r) => r["_field"] == "grund")'''
        query_auswertungslaeufe = f'''from(bucket: "dauerauswertung_immendingen") |> range(start: 2022-06-15, stop: 2022-07-22)
                            |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_auswertungslauf")'''
        df = client.query_api().query_data_frame(query_auswertungslaeufe)
        print(df)
        query_mete = f'''from(bucket: "dauerauswertung_immendingen") |> range(start: 2022-06-15, stop: 2022-07-10)
                    |> filter(fn: (r) => r["_measurement"] == "messwerte_immendingen_terz" and r["_field"] == "lafeq" and r["messpunkt"] == "Immendingen MP 1")'''
        

def query_resu(range_start: datetime, range_stop: datetime, project_name: str = "mannheim", mp_name: str = "Mannheim MP 2"):
    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=1000*600) as client:
        query_verfuegbare_sekunden = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "messwerte_{project_name}_resu" and r["_field"] == "lafeq" and r["messpunkt"] == "{mp_name}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")"""
        result = client.query_api().query_data_frame(query_verfuegbare_sekunden)
        result = result[["_time", "lafeq"]]
        
        result = result.set_index("_time")
        return result


def query_daimler_io_lr_export(target_folder: str, range_start: datetime, range_stop: datetime):
    project_name = "immendingen"
    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=1000*600) as client:
        query_verfuegbare_sekunden = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_lr" and r["verursacher"] == "gesamt") |> sort(columns: ["_time"])
            |> keep(columns: ["_time", "_value", "immissionsort"])"""
        df_io_lr = client.query_api().query_data_frame(query_verfuegbare_sekunden)
        df_io_lr.drop(["table", "result"], axis=1, inplace=True)
        df_io_lr["immissionsort"] = df_io_lr["immissionsort"].astype(int)
        df_io_lr = df_io_lr.sort_values(by=["_time", "immissionsort"])
        df_io_lr["id"] = 1
        df_io_lr.rename({"immissionsort": "IdImmissionsort", "_value": "Beurteilungspegel", "_time": "Timestamp"}, axis = 1, inplace = True)

        df_io_lr = df_io_lr[['Timestamp', "id", "Beurteilungspegel", "IdImmissionsort"]] # reorder

        df_io_lr.set_index("Timestamp", inplace=True)
        # csv_file = open("test.csv", "w") #f"ios_immendingen_rolling_{range_start.strftime('%Y_%m_%d')}_To_{range_stop.strftime('%Y_%m_%d')}.csv"
        path_to_target_file = f"{target_folder}/ios_immendingen_rolling_{range_start.strftime('%Y_%m_%d')}_To_{range_stop.strftime('%Y_%m_%d')}.csv"
        df_io_lr.to_csv(path_to_target_file,decimal=",", sep=";", date_format="%d.%m.%Y %H:%M:%S")
        logging.debug(df_io_lr)
        return path_to_target_file


def query_monatsbericht(year: int, month: int):
    project = project_immendingen
    project_name = project.name_in_db
    ios = project_immendingen.IOs
    number_days_in_month = monthrange(year, month)[1]
    range_start = datetime(year,month,1, 0, 0, 0)
    range_stop = datetime(year,month,1, 0, 0, 0) + timedelta(days=number_days_in_month)

    my_dict: typing.Dict[int, MonatsuebersichtAnImmissionsort] = dict(zip([io.Id for io in project_immendingen.IOs], [MonatsuebersichtAnImmissionsort(io) for io in ios]))
    
    number_days_in_month = monthrange(range_start.year, range_start.month)[1]
    logging.info(f"Seconds in month: {number_days_in_month*3600*24}")
    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=1000*600) as client:
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
                |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_lr" and r["_field"] == "lr" and r["verursacher"] == "gesamt")'''
        query_lauteste_stunde = f'''from(bucket: "dauerauswertung_immendingen")
        |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_lauteste_stunde")
            |> filter(fn: (r) => r["_field"] == "lauteste_stunde")'''
        df : pd.DataFrame = client.query_api().query_data_frame(query)
        df.drop(["table", "_start", "_stop", "_measurement", "_field", "result", "verursacher"], axis=1, inplace=True)
        df = df.astype({'immissionsort': 'int32'})
        # print(df)            
        # df = df.set_index("_time")
        # df = df.resample("H").max().reset_index()
        df_nachts = df[df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_tagzeitraum = df[~df["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        
        for df in [df_tagzeitraum]:
            for io in ios:
                print(f"Part 1 an {io.Id}", df[df["immissionsort"] == io.Id])
                df_an_io = df[df["immissionsort"] == io.Id].set_index(["_time"])
                lr = df_an_io.groupby(by= lambda idx: idx.day).max()
                print(f"Part 2 an {io.Id}", lr)
                # lr = lr.set_index(["_time"])
                
                my_dict[io.Id].lr_tag = lr
                    
        df_tagzeitraum.set_index(["_time", "immissionsort"], inplace=True)
        
        logging.info(f"lr-nacht: {df_nachts}")
        df_nachts["day"] = df_nachts["_time"].dt.day
        df_lr_nachts = df_nachts.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lr_nachts.sort_values(["immissionsort", "day"], inplace=True)
        for io in ios: 
            df_lr_nachts_an_io = df_lr_nachts[df_lr_nachts["immissionsort"] == io.Id].loc[:, ["_time", "_value", "day"]]
            df_lr_nachts_an_io = df_lr_nachts_an_io.set_index(["day"])
            my_dict[io.Id].lr_max_nacht = df_lr_nachts_an_io
            print(io.Id, my_dict[io.Id].lr_max_nacht)
        # logging.info(f"lr-nacht-mit-arg: {df_lr_nachts}")
        # logging.info(f"lr-tag: {df_tagzeitraum}")
        df_lauteste_stunde = client.query_api().query_data_frame(query_lauteste_stunde)
        df_lauteste_stunde.drop(["table", "_start", "_stop", "_measurement", "_field", "result"], axis=1, inplace=True)
        df_lauteste_stunde_nachts = df_lauteste_stunde[df_lauteste_stunde["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_lauteste_stunde_tagzeitraum = df_lauteste_stunde[~df_lauteste_stunde["_time"].dt.hour.isin([0, 1, 2, 3, 4, 5,  22, 23])]
        df_lauteste_stunde_tagzeitraum.loc[:, "day"] = df_lauteste_stunde_tagzeitraum["_time"].dt.day
        df_lauteste_stunde_nachts.loc[:, "day"] = df_lauteste_stunde_nachts["_time"].dt.day
        df_lauteste_stunde_tagzeitraum = df_lauteste_stunde_tagzeitraum.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lauteste_stunde_tagzeitraum.sort_values(["immissionsort", "day"], inplace=True)
        # df_lauteste_stunde_tagzeitraum.set_index(["day", "immissionsort"], inplace=True)
        # df_lauteste_stunde_nachts.set_index(["day", "immissionsort"], inplace=True)
        df_lauteste_stunde_nachts = df_lauteste_stunde_nachts.sort_values('_value').drop_duplicates(["day", "immissionsort"],keep='last')
        df_lauteste_stunde_nachts.sort_values(["immissionsort", "day"], inplace=True)
        # df_lauteste_stunde_nachts.set_index(["immissionsort", "day"], inplace=True)
        print(f"lauteste_stunde-nacht: {df_lauteste_stunde_nachts}")
        for io in ios: 
            my_dict[io.Id].lauteste_stunde_tag = df_lauteste_stunde_tagzeitraum[df_lauteste_stunde_tagzeitraum["immissionsort"] == io.Bezeichnung].loc[:, ["day", "_value", "_time"]].set_index(["day"])
            my_dict[io.Id].lauteste_stunde_nacht = df_lauteste_stunde_nachts[df_lauteste_stunde_nachts["immissionsort"] == io.Bezeichnung].loc[:, ["day", "_value", "_time"]].set_index(["day"])
        
        # logging.info(f"lauteste_stunde-nacht: {df_lauteste_stunde_nachts}")

        # logging.info(f"lauteste_stunde-tag: {df_lauteste_stunde_tagzeitraum}")

        q_aussortiert_wetter = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung" and contains(value: r["_value"], set: ["wind", "regen"]))
            |> group(columns: ["_measurement"])
            |> count()"""
        df_aussortiert_wetter = client.query_api().query_data_frame(q_aussortiert_wetter)
        logging.info(f"q_aussortiert_wetter: {df_aussortiert_wetter['_value'][0]}")

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
        for io in ios: 
            print("!", my_dict[io.Id])
        a = Monatsbericht(range_start, project_immendingen,
                        df_verfuegbare_sekunden['_value'][0], df_aussortiert_wetter['_value'][0],
                        df_aussortiert_sonstiges['_value'][0], "blub", my_dict)
        return a




def query_4_ueberschreitung_lr(io, zu_pruefender_wert, range_start, range_stop):
    with InfluxDBClient(url=influx_url, token=token, org=org) as client:

        query = f'''from(bucket: "dauerauswertung_immendingen") |> range(start: {range_start}, stop: {range_stop})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_immendingen_lr")
            |> filter(fn: (r) => r["_field"] == "lr")
            |> filter(fn: (r) => r["verursacher"] == "gesamt" and r["immissionsort"] == "{io}") |> filter(fn: (r) => r["_value"] >= {zu_pruefender_wert})'''
        logging.info(query)
        try:
            tables = client.query_api().query(query)
            for table in tables:
                for record in table.records:
                    logging.info(f'Found value of for {io} at {range_start}: {record["_value"]}')
                    return Ueberschreitungspruefung(record["_value"], record["_time"])
                    break
        except urllib3.exceptions.ReadTimeoutError as e:
            logging.exception(e)
            raise e
    return Ueberschreitungspruefung(0, None)


# query_4_ueberschreitung_lr()
def get_anzahl_aussortierte_sekunden(range_start: datetime, range_stop: datetime, project_name: str):
    with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        for field in ["verfuegbare_sekunden", "verwertbare_sekunden", "gewertete_sekuden"]:
            q = f"""from(bucket: "dauerauswertung_immendingen")
    |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
    |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_auswertungslauf" and r["_field"] == "{field}")
    |> group(columns: ["_measurement"])
        |> sum(column: "_value")"""
            df = client.query_api().query_data_frame(q)
            print(df)
        q_aussortiert_wetter = f"""from(bucket: "dauerauswertung_immendingen")
        |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
          |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung" and contains(value: r["_value"], set: ["wind", "regen"]))
            |> group(columns: ["_measurement"])
        |> count()"""
        df = client.query_api().query_data_frame(q_aussortiert_wetter)
        print(df)
        q_aussortiert_kontrolle = f"""from(bucket: "dauerauswertung_immendingen")
        |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
          |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung") |> group(columns: ["_measurement"])
        |> count()"""
        df = client.query_api().query_data_frame(q_aussortiert_kontrolle)
        print(df)

def fehlersuche_2206601(range_start: datetime, range_stop: datetime, project_name: str):

    with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        q_aussortiert_kontrolle = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_aussortierung" and r["_field"] == "grund" and r["_value"] == "zu wenige messwerte")"""
        df = client.query_api().query_data_frame(q_aussortiert_kontrolle)
        print(df)
        q = f"""from(bucket: "dauerauswertung_immendingen")
            |> range(start: {range_start.strftime(ISOFORMAT)}, stop: {range_stop.strftime(ISOFORMAT)})
            |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_auswertungslauf" and r["_field"] == "verwertbare_sekunden")"""
        df = client.query_api().query_data_frame(q)
        print(df["_value"])


def delete_old_zug_data(start_date: datetime, stop_date: datetime, project_name: str):
    bucket = "dauerauswertung_immendingen"

    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=600*1000) as client:
        delete_api = client.delete_api()
        
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_erkennung\"", bucket)


def delete_foo(start_date: datetime, stop_date: datetime, project_name: str):
    bucket = "dauerauswertung_immendingen"

    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=600*1000) as client:
        delete_api = client.delete_api()
        
        delete_api.delete(start_date, stop_date, f"_measurement=\"messwerte_{project_name}_resu\"", bucket)
        delete_api.delete(start_date, stop_date, f"_measurement=\"messwerte_{project_name}_mete\"", bucket)
        delete_api.delete(start_date, stop_date, f"_measurement=\"messwerte_{project_name}_terz\"", bucket)



def read_schallleistungspegel(start_date: datetime, stop_date: datetime, project_name: str):
     with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        q_schallleistungspegel = f"""from(bucket: "dauerauswertung_immendingen")
        |> range(start: {start_date.strftime(ISOFORMAT)}, stop: {stop_date.strftime(ISOFORMAT)})
        |> filter(fn: (r) => r["_measurement"] == "auswertung_{project_name}_schallleistungspegel")"""
        df = client.query_api().query_data_frame(q_schallleistungspegel)

        print(df)

        df["_hour"] = df["_time"].dt.hour
        df["_day"] = df["_time"].dt.day

        for mp_name in ["Sindelfingen MP 5", "Sindelfingen MP 1", "Sindelfingen MP 2"]:
            pass
            # print(df[df["messpunkt"] == mp_name].groupby(["_day", "_hour"])["_value"].agg(['min', 'max']))
        #apply(lambda r: 10*np.log10((10**(0.1*r)).sum())))
        result = df.groupby(["_day", "_hour"]).agg(schallleistungspegel=pd.NamedAgg(column="_value", aggfunc=lambda x: 10*np.log10(sum(10**(0.1*x)))))

        print(result)
        return result

        # print(df_night_mp)
        # print(df)
    


def delete_old_data(start_date: datetime, stop_date: datetime, project_name: str):
    
    bucket = "dauerauswertung_immendingen"

    with InfluxDBClient(url=influx_url, token=token, org=org, timeout=60*1000) as client:
        delete_api = client.delete_api()
        
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_auswertungslauf\"", bucket)
        logging.info("Deleted from auswertungslauf")
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_erkennung\"", bucket)
        logging.info("Deleted from erkennung")
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_lauteste_stunde\"", bucket)
        logging.info("Deleted from lauteste_stunde")
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_schallleistungspegel\"", bucket)
        logging.info("Deleted from schallleistungspegel")
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_lr\"", bucket)
        logging.info("Deleted from lr")
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_aussortierung\"", bucket)
        logging.info("Deleted from aussortierung")


def prepare_erkennung_zug(project_name, erkennungen):

    
    erkennung_seq = []

    messpunkt_bezeichnung = "Test"
    auswertslauf_id = "Test"


    counter = 0
    for e in erkennungen:
        for tp in e.timepoints:
            erkennung_point = Point(f"auswertung_{project_name}_erkennung")\
                .tag("messpunkt", messpunkt_bezeichnung)\
                .tag("pattern", e.pattern_id) \
                .tag("auswertungslauf", f"{auswertslauf_id}")\
                .tag("id_in_auswertungslauf", e.id)\
                .tag("score", e.score)\
                .time(tp).field("erkennung", 1)
            erkennung_seq.append(erkennung_point)
    return erkennung_seq


def delete_duration(start_date: datetime, stop_date: datetime, project_name: str):
    bucket = "dauerauswertung_immendingen"

    with InfluxDBClient(url=influx_url, token=token, org=org) as client:
        delete_api = client.delete_api()
        delete_api.delete(start_date, stop_date, f"_measurement=\"auswertung_{project_name}_erkennung\"", bucket)

if __name__ == "__main__":
    FORMAT = '%(filename)s %(lineno)d %(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(
        level=logging.INFO, format=FORMAT, handlers=[logging.StreamHandler(sys.stdout)]
    )
    project_name = "immendingen"
    month = 5

    _, days_in_month = monthrange(2021, month)
    
    start_date = datetime(2021,month,1, 0, 0, 0)
    stop_date = datetime(2021,month, days_in_month, 23, 59, 59)
    if True:
        read_schallleistungspegel(start_date, stop_date, "sindelfingen")
    if False:
        delete_foo(start_date, stop_date, "sindelfingen")

    if False:
        start_date = datetime(2022,7,25, 0, 0, 0)
        stop_date = start_date + timedelta(days=7)
        my_file = query_daimler_io_lr_export("./", start_date, stop_date)
        print(my_file)
    if False:
        query_monatsbericht()
    if False:
        start_date = datetime(2022,7,15, 6, 0, 0)
        stop_date = datetime(2022,7, 15, 7, 0, 0)
        query_resu(start_date, stop_date)
    # query_counting_available_values_per_day()
    # query_auswertungslauf()
    if False:
    # delete_old_data(start_date, stop_date, project_name)
        total_seconds = (stop_date - start_date).total_seconds()
        print(total_seconds)
        get_anzahl_aussortierte_sekunden(start_date, stop_date, project_name)
        fehlersuche_2206601(start_date, stop_date, project_name)
    # delete_duration(start_date, stop_date, project_name)
    
