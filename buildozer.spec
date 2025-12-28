[app]

# App name
title = IRIS Pics

# Package identifiers (must be lowercase)
package.name = irispics
package.domain = org.emergentmindworks

# Version (THIS FIXES YOUR ERROR)
version = 0.1

# Source
source.dir = .
source.include_exts = py

# Entry point
entrypoint = main.py

# Python & libs
requirements = python3,kivy,pillow

# Screen
orientation = portrait
fullscreen = 0

# Permissions (none needed yet)
android.permissions =

# Android API targets (safe defaults)
android.api = 33
android.minapi = 21
android.sdk = 24
android.ndk = 25b

# Build options
android.private_storage = True
android.allow_backup = True

# Architecture
android.archs = arm64-v8a

# Logcat (optional but helpful)
log_level = 2

# Disable unnecessary features
android.accept_sdk_license = True
