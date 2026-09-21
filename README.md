# Scalendar V1

Scalendar V1 is a next-generation Windows desktop application for converting timetable images into calendar data. It is a complete rewrite based on the old test version and is kept Git-isolated from the historical version; the legacy baseline remains available in Git without affecting V1 development.

The current V1.0.0 delivery scope covers Milestones 0–9, including the Python / PySide6 / QML project foundation, the complete `.scalendar` project lifecycle, an editable course model, multi-select batch operations in the course list, and calendar export workflows.

## Features

- Recognize timetable images and extract structured course data
- Manage an editable course model and timetable data
- Select multiple courses for batch editing, deletion, and schedule adjustments
- Sort and filter courses by weekday, period, or course name
- Use `.scalendar` project files as the single source of truth
- Import/export Excel files and export ICS calendars
- Provide a Windows desktop application and portable release workflow
- Include automated tests and CI build checks

## Development Environment

- Python 3.11+
- PySide6 6.8+
- Windows 10 / 11 (target platform)

Using the virtual environment included with the project is recommended for development. Neither the application nor its tests require end users to use PowerShell as their only entry point; PowerShell is mainly used for development and build workflows.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

## Running and Testing

```powershell
python -m scalendar.main
pytest
```

After installing the project, you can also run it directly:

```powershell
scalendar
```

Build the Windows portable version:

```powershell
.\tools\build_windows.ps1
```

The build output is located at `build\release\Scalendar\Scalendar.exe`. Build directories are not committed to Git. The Windows release workflow uses Qt for Python's official `pyside6-deploy`; its configuration is stored in `pysidedeploy.spec`.

GitHub Actions automatically runs the regular push and pull request test suite on a Windows runner. Manually triggering the `Windows package` workflow, or pushing a version tag, produces a portable build artifact retained for a short period.

After starting the GUI, the Home page is displayed. Users can create a blank timetable, add/edit/delete courses, synchronize edits between the timetable and course list, sort by weekday/period/name, and apply batch changes to multiple selected courses.

## Architecture

```text
src/scalendar/
├── main.py                 # Qt application entry point
├── core/                   # Pure data models, validation, and timetable date calculations
├── storage/                # .scalendar JSON project read/write
├── recognition/            # Image-recognition providers and candidate-result normalization
├── importers/              # Excel input adapters and external spreadsheet compatibility layer
├── exporters/              # XLSX / ICS output adapters
├── bridge/                 # Python–QML controller boundary
├── ui/                     # Qt Quick / QML pages, components, and theme
└── tests/                  # Automated tests
```

Project files use UTF-8 encoded JSON and the `.scalendar` extension. They are the single source of truth. Excel is an import/export format for review and exchange, not the internal source of truth. Recognition results should be reviewed and edited by the user before they are used or exported.

## User Data and Security

User settings and project files should be stored in a user-writable directory or a directory selected manually by the user. API keys are accepted only as in-memory values for the current session and should not be persisted in the project directory or a system-wide directory.

The repository ignores user images, Excel files, ICS files, `.scalendar` files, virtual environments, build artifacts, and secret files. See [docs/release.md](docs/release.md) for release workflow details.

## Milestone Status

| Milestone | Status |
| --- | --- |
| M0 Project environment and minimal window | Implemented |
| M1 Data core and project read/write | Implemented |
| M2 UI shell and visual direction | Complete |
| M3 Real project data and manual timetable editor | Complete |
| M4 Course list and time-setting enhancements | Complete |
| M5 Image recognition | Complete |
| M6 Excel import / export | Complete |
| M7 ICS export | Complete |
| M8 Windows EXE / release workflow | Complete |
| M9 GitHub CI / build automation | Complete |

## Notes

- This is the rewritten V1 version; the history of the old version remains in Git and does not affect new-version development.
- Future documentation improvements may include a quick-start example, screenshots, a FAQ, a feature roadmap, and contribution guidelines.
