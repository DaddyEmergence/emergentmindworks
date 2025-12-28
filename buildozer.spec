[app]

# ---- App identity ----
title = IRIS Pics
package.name = irispics
package.domain = org.emergentmindworks

# REQUIRED — this fixes your exact error
version = 0.1

# ---- Source ----
source.dir = .
source.include_exts = py

# ---- Python requirements ----
requirements = python3,kivy,pillow

# ---- Entry point ----
# main.py must exist and start the Kivy App
entrypoint = main.py

# ---- Display ----
orientation = portrait
fullscreen = 0

# ---- Android SDK / NDK ----
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# ---- Architectures ----
android.arch = arm64-v8a

# ---- Permissions (none needed yet) ----
android.permissions =

# ---- Logging (helps debugging in Actions) ----
log_level = 2

# ---- Disable things that break CI ----
android.accept_sdk_license = True
android.enable_androidx = True

# ---- Packaging sanity ----
copy_libs = True
ignore_setup_py = True

# ---- Build performance ----
android.skip_update = False
android.private_storage = False

# ---- END ----
