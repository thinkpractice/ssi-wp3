#!/bin/bash

PYTHONPATH="." luigi --module ssi.preprocessing.convert ConvertAHReceipts --input-filename=$1 --output-filename=$2 --local-scheduler 