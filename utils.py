#! /usr/bin/env python
# -*- coding: utf-8 -*-
from itertools import chain
from pathlib import Path
import sys
import yaml


def from_yaml(file_path, directory=False):
    """
    From data from yaml file
    """
    data = {}

    if directory:
        path = Path(file_path)
        yaml_files = list(chain.from_iterable([
            path.glob(extension)
            for extension in ('*.yaml', '*.yml')
        ]))

        for fp in yaml_files:
            stem = fp.stem
            with open(fp, 'r') as fh:
                hostvars = yaml.safe_load(fh.read())
                if hostvars:
                    data[stem] = hostvars
        return data

    try:

        with open(file_path, 'r') as handle:
            stream = handle.read()
            data = yaml.safe_load(stream)
        return data
    except yaml.parser.ParserError:
        sys.exit(f'File does not appear to be a valid YAML file.')

    except OSError as e:
        print(f'could not open data file: {file_path}')
        print(str(e))
