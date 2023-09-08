from dotenv import load_dotenv
import os
import sys
load_dotenv(".env")

import requests
from pydantic import BaseModel, Field
from typing import List, Optional, Union

class EntryParams(BaseModel):
    mim_number: Union[int, List[int]]
    include: List[str] = [
        "clinicalSynopsis",
        "existFlags",
        "externalLinks",
        "contributors",
        "creationDate",
        "editHistory",
        "dates",
    ]
    exclude: List[str] = []


class EntrySearchParams(BaseModel):
    search: str
    filter: Optional[str] = None
    fields: Optional[str] = "number^5 title^3 default"
    sort: Optional[str] = "score desc"
    operator: Optional[str] = None
    start: int = 0
    limit: int = 10
    retrieve: Optional[str] = None
    include: List[str] = [
        "clinicalSynopsis",
        "existFlags",
        "externalLinks",
        "contributors",
        "creationDate",
        "editHistory",
        "dates",
    ]
    exclude: List[str] = []


class ClinicalSynopsisParams(BaseModel):
    mim_number: Union[int, List[int]]
    include: List[str] = [
        "clinicalSynopsis",
        "existFlags",
        "externalLinks",
        "contributors",
        "creationDate",
        "editHistory",
        "dates",
    ]
    exclude: List[str] = []

class GeneMapParams(BaseModel):
    sequence_id: int = None
    mim_number: Union[int, List[int]] = None
    chromosome: str = None
    chromosome_sort: int = None
    start: int = 0
    limit: int = 10
    phenotype_exists: bool = None

class OMIM:
    def __init__(self):
        self.api_key = os.environ.get("OMIM_API_KEY")
        self.base_url = "https://api.omim.org/api"
        self.tool_desctption = "OMIM API"

    def fetch_entry(self, entry_params: EntryParams):
        mim_numbers = entry_params.mim_number
        if not isinstance(mim_numbers, list):
            mim_numbers = [mim_numbers]
        mim_numbers_str = ",".join(map(str, mim_numbers))

        include_str = "&include=" + ",".join(entry_params.include)

        exclude_str = ""
        if entry_params.exclude:
            exclude_str = "&exclude=" + ",".join(entry_params.exclude)

        try:
            url = f"{self.base_url}/entry?mimNumber={mim_numbers_str}{include_str}{exclude_str}&format=json&apiKey={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def search_entry(self, entry_search_params: EntrySearchParams):
        params = {
            "format": "json",
            "apiKey": self.api_key,
            "search": entry_search_params.search,
            "filter": entry_search_params.filter,
            "fields": entry_search_params.fields,
            "sort": entry_search_params.sort,
            "operator": entry_search_params.operator,
            "start": entry_search_params.start,
            "limit": entry_search_params.limit,
            "retrieve": entry_search_params.retrieve,
            "include": ",".join(entry_search_params.include),
            "exclude": ",".join(entry_search_params.exclude),
        }

        try:
            url = f"{self.base_url}/entry/search"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def fetch_clinical_synopsis(self, clinical_synopsis_params: ClinicalSynopsisParams):
        mim_numbers = clinical_synopsis_params.mim_number
        if not isinstance(mim_numbers, list):
            mim_numbers = [mim_numbers]
        mim_numbers_str = ",".join(map(str, mim_numbers))

        include_str = "&include=" + ",".join(clinical_synopsis_params.include)

        exclude_str = ""
        if clinical_synopsis_params.exclude:
            exclude_str = "&exclude=" + ",".join(clinical_synopsis_params.exclude)

        try:
            url = f"{self.base_url}/clinicalSynopsis?mimNumber={mim_numbers_str}{include_str}{exclude_str}&format=json&apiKey={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def fetch_gene_map(self, gene_map_params: GeneMapParams):
        params = {
            "format": "json",
            "apiKey": self.api_key,
            "sequenceID": gene_map_params.sequence_id,
            "mimNumber": gene_map_params.mim_number,
            "chromosome": gene_map_params.chromosome,
            "chromosomeSort": gene_map_params.chromosome_sort,
            "start": gene_map_params.start,
            "limit": gene_map_params.limit,
            "phenotypeExists": gene_map_params.phenotype_exists,
        }

        try:
            url = f"{self.base_url}/geneMap"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None