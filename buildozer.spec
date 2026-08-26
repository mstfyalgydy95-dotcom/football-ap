[app]
title = مواعيد المباريات
package.name = footballmatches
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,json,kv,atlas
source.include_patterns = leagues_data.json,logos/*

version = 1.0
requirements = python3,kivy,plyer

orientation = portrait
fullscreen = 0

# صلاحيات أندرويد اللازمة للإشعارات
android.permissions = INTERNET,POST_NOTIFICATIONS,FOREGROUND_SERVICE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
