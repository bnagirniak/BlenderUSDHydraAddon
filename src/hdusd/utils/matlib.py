#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#********************************************************************
import requests
import weakref
from dataclasses import dataclass, field
import shutil
from pathlib import Path
import zipfile
import json

from . import LIBS_DIR

from ..utils import logging
log = logging.Log(tag='utils.matlib')

URL = "https://matlibapi.stvcis.com/api"
MATLIB_DIR = LIBS_DIR.parent / "matlib"


def download_file(url, path, cache_check=True):
    if cache_check and path.is_file():
        return path

    log("download_file", f"{url=}, {path=}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True) as response:
        with open(path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    log("download_file", "done")
    return path


def request_json(url, params, path, cache_check=True):
    if cache_check and path and path.is_file():
        with open(path) as json_file:
            return json.load(json_file)

    log("request_json", f"{url=}, {params=}, {path=}")

    response = requests.get(url, params=params)
    res_json = response.json()

    if path:
        save_json(res_json, path)

    log("request_json", "done")
    return res_json


def save_json(json_obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as outfile:
        json.dump(json_obj, outfile)


@dataclass(init=False)
class Render:
    id: str
    author: str = field(init=False, default=None)
    image: str = field(init=False, default=None)
    image_url: str = field(init=False, default=None)
    image_path: Path = field(init=False, default=None)
    thumbnail: str = field(init=False, default=None)
    thumbnail_url: str = field(init=False, default=None)
    thumbnail_path: Path = field(init=False, default=None)
    thumbnail_icon_id: int = field(init=False, default=None)

    def __init__(self, id, material):
        self.id = id
        self.material = weakref.ref(material)

    @property
    def cache_dir(self):
        return self.material().cache_dir

    def get_info(self, cache_chek=True):
        json_data = request_json(f"{URL}/renders/{self.id}", None,
                                 self.cache_dir / f"R-{self.id[:8]}.json", cache_chek)

        self.author = json_data['author']
        self.image = json_data['image']
        self.image_url = json_data['image_url']
        self.thumbnail = json_data['thumbnail']
        self.thumbnail_url = json_data['thumbnail_url']

    def get_image(self, cache_check=True):
        self.image_path = download_file(self.image_url,
                                        self.cache_dir / self.image, cache_check)

    def get_thumbnail(self, cache_check=True):
        self.thumbnail_path = download_file(self.thumbnail_url,
                                            self.cache_dir / self.thumbnail, cache_check)

    def thumbnail_load(self, pcoll):
        thumb = pcoll.load(self.thumbnail, str(self.thumbnail_path), 'IMAGE')
        self.thumbnail_icon_id = thumb.icon_id


@dataclass(init=False)
class Package:
    id: str
    author: str = field(init=False, default=None)
    label: str = field(init=False, default=None)
    file: str = field(init=False, default=None)
    file_url: str = field(init=False, default=None)
    size: str = field(init=False, default=None)
    file_path: Path = field(init=False, default=None)

    def __init__(self, id, material):
        self.id = id
        self.material = weakref.ref(material)

    @property
    def cache_dir(self):
        return self.material().cache_dir / f"P-{self.id[:8]}"

    @property
    def has_file(self):
        return bool(self.file_path)

    def get_info(self, cache_check=True):
        json_data = request_json(f"{URL}/packages/{self.id}", None,
                                 self.cache_dir / "info.json", cache_check)

        self.author = json_data['author']
        self.file = json_data['file']
        self.file_url = json_data['file_url']
        self.label = json_data['label']
        self.size = json_data['size']

    def get_file(self, cache_check=True):
        self.file_path = download_file(self.file_url,
                                       self.cache_dir / self.file, cache_check)

    def unzip(self, path=None, cache_check=True):
        if not path:
            path = self.cache_dir / "package"

        if path.is_dir() and not cache_check:
            shutil.rmtree(path, ignore_errors=True)

        if not path.is_dir():
            with zipfile.ZipFile(self.file_path) as z:
                z.extractall(path=path)

        mtlx_file = next(path.glob("**/*.mtlx"))
        return mtlx_file


@dataclass
class Category:
    id: str
    title: str = field(init=False, default=None)

    @property
    def cache_dir(self):
        return MATLIB_DIR

    def get_info(self, use_cache=True):
        json_data = request_json(f"{URL}/categories/{self.id}", None,
                                 self.cache_dir / f"C-{self.id[:8]}.json", use_cache)

        self.title = json_data['title']


@dataclass(init=False)
class Material:
    id: str
    author: str
    title: str
    description: str
    category: Category
    status: str
    renders: list[Render]
    packages: list[Package]

    def __init__(self, mat_json):
        self.id = mat_json['id']
        self.author = mat_json['author']
        self.title = mat_json['title']
        self.description = mat_json['description']
        self.category = Category(mat_json['category']) if mat_json['category'] else None
        self.status = mat_json['status']

        self.renders = []
        for id in mat_json['renders_order']:
            self.renders.append(Render(id, self))

        self.packages = []
        for id in mat_json['packages']:
            self.packages.append(Package(id, self))

        save_json(mat_json, self.cache_dir / "info.json")

    @property
    def cache_dir(self):
        return MATLIB_DIR / f"M-{self.id[:8]}"

    @property
    def full_description(self):
        text = self.title
        if self.description:
            text += f"\n{self.description}"
        if self.category:
            text += f"\nCategory: {self.category.title}"
        text += f"\nAuthor: {self.author}"

        return text

    @classmethod
    def get_materials(cls, limit=10, offset=0):
        res_json = request_json(f"{URL}/materials", {'limit': limit, 'offset': offset}, None)

        for mat_json in res_json['results']:
            mat = Material(mat_json)
            if not mat.packages:
                continue

            yield mat

    @classmethod
    def get_all_materials(cls):
        offset = 0
        limit = 500

        while True:
            mat = None
            for mat in cls.get_materials(limit, offset):
                yield mat

            if not mat:
                break

            offset += limit
