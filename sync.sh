#!/bin/bash
venv/bin/python trello-list.py
scp *.html cloud-user@10.3.10.135:/var/www/html
