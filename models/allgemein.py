from dataclasses import dataclass, field

from enum import Enum

@dataclass
class MessdatenFolder:
    folder_path: str
    id_messpunkt: int
    typ: int

    def get_typ_messfile(self):
        return self.typ

class SvlMessfiletyp(Enum):
    version_07_21_mit_wetterdaten = 1
    version_07_21_ohne_wetterdaten = 0



'''
@dataclass
class Koordinaten:
    rechtswert: float = 0
    hochwert: float = 0
'''
@dataclass
class Koordinaten:
    GKRechtswert: float = 0
    GKHochwert: float = 0
'''
@dataclass
class Immissionsort:
    id: int
    koordinaten: Koordinaten = field(default_factory=Koordinaten)
    bezeichnung: str = "Y"
    grenzwert_tag: float = 0
    grenzwert_nacht: float = 0
    ruhezeitzuschlag: bool = False
'''
@dataclass
class Immissionsort:
    Id: str
    Bezeichnung: str = "Missing IO name"
    Grenzwert_nacht: float = 100
    Grenzwert_tag: float = 100
    Koordinaten:  Koordinaten = Koordinaten(0, 0)
    ruhezeitzuschlag: bool = False
    shortname_for_excel: str = "" # <= 31 chars

    def get_kurzbezeichnung(self):
        return f"IO {self.Id}"

    def __post_init__(self):
        if self.shortname_for_excel == "":
            self.shortname_for_excel = self.Bezeichnung
@dataclass
class Messpunkt:
    Id: str
    bezeichnung_in_db: str = ""
    Bezeichnung: str = "Missing MP name"
    Koordinaten: Koordinaten = Koordinaten(0, 0)
    Ereignisse: list[str] = field(default_factory=list)
    LWA: float = 0.0 # schallleistungspegel_korrektur
    Filter: list[str] = field(default_factory=list)
    OrdnerMessdaten: str = ""
    

'''
@dataclass
class Messpunkt:
    id: int
    koordinaten: Koordinaten = field(default_factory=Koordinaten)
    ereignisse: list[str] = field(default_factory=list)
    bezeichnung: str = "X"
    lwa: float = 0.0  # schallleistungspegel_korrektur """
'''


@dataclass
class Projekt:
    name: str
    IOs: list[Immissionsort]
    MPs: list[Messpunkt]
    Ausbreitungsfaktoren: dict
    name_in_db: str
    has_mete_data: bool = False
    has_terz_data: bool = False
    gw_lafeq: float = 90
    gw_lafmax: float = 100


@dataclass
class Beurteilungszeitraum:
    Beginn: int
    Ende: int
    Stunden_in_beurteilungszeitraum: int

