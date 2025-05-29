#!/bin/sh
git -C /app/$1 pull
mysqldump --add-drop-database --skip-dump-date --user=root --password="$2" --result-file="/app/$1/backupdb.sql" --databases attendancedb
git -C /app/$1 commit -am "update"
git -C /app/$1 push
