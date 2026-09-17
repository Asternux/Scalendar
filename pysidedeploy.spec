[app]

title = Scalendar
project_dir = src
input_file = src/main.py
exec_directory = build/pyside6
project_file =
icon =

[python]

python_path = .venv/Scripts/python.exe
packages = Nuitka==4.1.1
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]

qml_files = scalendar/ui/Main.qml,scalendar/ui/Scalendar/Theme/Theme.qml,scalendar/ui/components/CourseCard.qml,scalendar/ui/components/Sidebar.qml,scalendar/ui/components/SidebarItem.qml,scalendar/ui/components/Topbar.qml,scalendar/ui/pages/CourseListPage.qml,scalendar/ui/pages/ExportPage.qml,scalendar/ui/pages/HomePage.qml,scalendar/ui/pages/ImportPage.qml,scalendar/ui/pages/SettingsPage.qml,scalendar/ui/pages/TimeSettingsPage.qml,scalendar/ui/pages/TimetablePage.qml
excluded_qml_plugins = QtCharts,QtSensors,QtWebEngine
modules = Core,Gui,Qml,Quick,QuickControls2
plugins = platforminputcontexts,platforms,qml,qmllint,qmltooling

[android]

wheel_pyside =
wheel_shiboken =
plugins =

[nuitka]

macos.permissions =
mode = standalone
extra_args = --quiet --noinclude-qt-translations --assume-yes-for-downloads --noinclude-qt-plugins=imageformats --noinclude-qt-plugins=iconengines --noinclude-qt-plugins=mediaservice --noinclude-qt-plugins=printsupport --noinclude-qt-plugins=styles --noinclude-qt-plugins=platformthemes --noinclude-qt-plugins=egldeviceintegrations --noinclude-qt-plugins=xcbglintegrations --noinclude-qt-plugins=tls --noinclude-qt-plugins=generic --output-filename=Scalendar.exe

[buildozer]

mode = debug
recipe_dir =
ndk_path =
sdk_path =
jars_dir =
local_libs =
arch =
