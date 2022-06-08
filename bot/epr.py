# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the Elastic License;
# you may not use this file except in compliance with the Elastic License.

import requests
import functools


@functools.lru_cache
def get_epr():

    class Epr:
        url = "https://epr.elastic.co"

        def __init__(self):
            self.session = requests.Session()

        def close(self):
            self.session.close()

        def search(self, package=None, all=False):
            url = f"{self.url}/search?all={int(all)}"
            if package:
                url += f"&package={package}"
            res = self.session.get(url)
            res.raise_for_status()
            return res.json()

    return Epr()
