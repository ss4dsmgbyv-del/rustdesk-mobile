[app]
title = RustDesk Mobile
package.name = rustdesk_mobile
package.domain = org.madmax
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,requests,pillow,plyer
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,CAMERA
android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a
log_level = 2

[buildozer]
warn_on_root = 1
