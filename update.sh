#!/bin/bash
BASE=/opt/acedia
SRC=/home/n/Acedia_Linux
cp $SRC/main.py $BASE/main.py
cp $SRC/acedia/views/main_window.py $BASE/acedia/views/main_window.py
cp $SRC/acedia/views/paper_detail_view.py $BASE/acedia/views/paper_detail_view.py
cp $SRC/acedia/views/paper_list_view.py $BASE/acedia/views/paper_list_view.py
cp $SRC/acedia/views/paper_edit_dialog.py $BASE/acedia/views/paper_edit_dialog.py
cp $SRC/acedia/views/notes_view.py $BASE/acedia/views/notes_view.py
cp $SRC/acedia/views/citation_view.py $BASE/acedia/views/citation_view.py
cp $SRC/acedia/services/paper_service.py $BASE/acedia/services/paper_service.py
cp $SRC/acedia/services/ris_service.py $BASE/acedia/services/ris_service.py
mkdir -p $BASE/acedia/resources
cp $SRC/acedia/resources/icon.ico $BASE/acedia/resources/icon.ico
echo "完了"
