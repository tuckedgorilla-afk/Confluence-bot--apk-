[app]
title = Confluence Engine
package.name = confluencebot
package.domain = org.scanner
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy,requests,urllib3,chardet,idna
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, FOREGROUND_SERVICE, WAKE_LOCK
services = confluenceengine:service.py
