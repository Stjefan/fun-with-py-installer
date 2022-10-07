from dataclasses import dataclass, field
from typing import List
import datetime
import json
import typing
from models.allgemein import Messpunkt, Immissionsort

from pandas import Series, DataFrame
import numpy as np

from models.allgemein import Projekt



@dataclass
class Detected:
    start: datetime.datetime
    end: datetime.datetime
    timepoints: np.array
    pattern_id: int
    messpunkt_id: int
    id: int
    score: float

@dataclass
class Auswertungslauf:
    ausgewertetes_datum: datetime
    project: str
    erkennung_set= [] 
    aussortierung_set= []
    beurteilungspegel_set= []
    schallleistungspegel_set= []
    lautestestunde_set= []
    zugeordneter_beurteilungszeitraum: int
    no_verwertbare_messwerte: int = 0
    no_verfuegbare_messwerte: int = 0
    no_gewertete_messwerte: int = 0
    no_aussortiert_wetter: int = 0
    no_aussortiert_sonstiges: int = 0
    zeitpunkt_durchfuehrung: datetime = field(default_factory=datetime.datetime.now)
    kennung_auswertungslauf: str = "N/A"
                                  

@dataclass
class Vorbeifahrt:
    beginn: datetime
    ende: datetime
    messpunkt: Messpunkt

@dataclass
class Aussortiert:
    timepoints: Series
    bezeichnug: str
    messpunkt: Messpunkt


@dataclass
class Schallleistungspegel:
    pegel: float
    zeitpunkt: datetime
    messpunkt: Messpunkt

@dataclass
class LautesteStunde:
    pegel: float
    zeitpunkt: datetime
    immissionsort: Immissionsort

@dataclass
class MonatsuebersichtAnImmissionsort:
    immissionsort: Immissionsort
    lr_tag: DataFrame = None
    lr_max_nacht: DataFrame = None
    lauteste_stunde_tag:  DataFrame = None
    lauteste_stunde_nacht: DataFrame = None
    


@dataclass
class Monatsbericht:
    monat: datetime.date
    projekt: Projekt
    no_verwertbare_sekunden: int
    no_aussortiert_wetter: int
    no_aussortiert_sonstige: int
    ueberschrift: str
    details_io: typing.Dict[int, MonatsuebersichtAnImmissionsort]
    schallleistungspegel: typing.Dict[typing.Tuple[int, int], float] = None
    
@dataclass
class Ueberschreitungspruefung:
    pegel: float
    erste_ueberschreitung: datetime

def get_total_second(arg: datetime.datetime):
    result = int(datetime.timedelta(hours=arg.hour, seconds=arg.second, minutes=arg.minute).total_seconds())
    if result == 0:
        return 24*3600
    else:
        return result