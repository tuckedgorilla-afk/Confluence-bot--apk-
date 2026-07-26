[app]
title = Confluence Engine
package.name = confluencebot
package.domain = org.scanner
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy,requests,urllib3,chardet,certifi,idna,openssl,hostpython3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, FOREGROUND_SERVICE
services = confluenceengine:service.py

# --- ANDROID CONFIGURATION ---
android.api = 33
android.minapi = 21
android.sdk_build_tools_version = 33.0.2
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 0
