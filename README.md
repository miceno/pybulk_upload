Python script to create bulk_upload files for Gallery 2 

Photos of the Arxiu Historic del Poblenou: http://fotos.arxiuhistoricpoblenou.es


To install the Xlrd package in 1and1 hosting:

1. Download easy_install
2. Install easy_install
3. run command

```easy_install --root```

4. include the library directly on the script
5. using PYTHONPATH will not work since the apache server running the cgi is under control of 1and1 admin and does not export PYTHONPATH from the local environment of a user account

Requirements
============

You will need python 2.7.

In addition, you should update the path to system modules at the begining of the file, to load `XLRD` module.


Keywords management
===================


Use script `update_keywords.py` and `clean_keywords.py` to create a SQL file to update the keywords of pictures.
