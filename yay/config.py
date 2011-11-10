# Copyright 2010-2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import yaml

from yay.loader import Loader
from yay.openers import Openers

class Config(object):

    def __init__(self, special_term='yay', searchpath=None):
        self.special_term = special_term
        self.openers = Openers(searchpath=searchpath)
        self.clear()

    def load_uri(self, uri):
        stream = self.openers.open(uri)
        self.load(stream, uri, hasattr(stream, "secret") and stream.secret)

    def load(self, stream, name="<Unknown>", secret=False):
        l = Loader(stream, name=name, special_term=self.special_term, secret=secret, openers=self.openers)
        data = l.compose(self.mapping)
        self.mapping = data

    def clear(self):
        self.mapping = None

    def get(self):
        if not self.mapping:
            return {}
        return self.mapping.resolve()

def load_uri(uri, special_term='yay'):
    c = Config(special_term)
    c.load_uri(uri)
    return c.get()

def load(stream, special_term='yay', secret=False):
    c = Config(special_term)
    c.load(stream, secret)
    return c.get()

def dump(obj):
    return yaml.dump(obj, default_flow_style=False)

