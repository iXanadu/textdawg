#!/bin/bash
git reset
git fetch --all
git reset --hard origin/main
pip install --upgrade git+ssh://git@github.com/iXanadu/FubHandler.git
git status

