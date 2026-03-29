#!/bin/bash

echo "Cleaning up!"
echo "Removing Python caches..."
find . -name \*.__pycache__ -delete
find . -name \*.pytest_cache -delete
find . -name \*.pyc -delete
echo "resetting python libraries"
echo find . -name $VIRTUAL_ENV/lib/python*/site-packages/*/*__pycache__ -delete 
echo find . -name $VIRTUAL_ENV/lib/python*/site-packages/*/*.pyc -delete


echo "Cleaning output files..."
find . -name \*.out -delete
find . -name \*.log -delete
find . -name \*.err -delete
find . -type f -name "*.lock" ! -name "uv.lock" -delete

rm -rf logs/

echo "Removing build files..."
find . -wholename build -delete
find . -wholename dist -delete
# .tox is no longer used, but we keep this here to clean up old environments
rm -rf .tox/
echo "Done cleaning!"
