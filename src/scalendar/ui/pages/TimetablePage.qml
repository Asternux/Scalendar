import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Scalendar.Theme 1.0
import "../components"

Page {
    id: page
    signal editCourse(string courseId)
    signal addCourse()
    background: Rectangle { color: "transparent" }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: "本周课表"
                color: Theme.ink
                font.pixelSize: 25
                font.bold: true
            }
            Button {
                text: "＋ 添加课程"
                onClicked: page.addCourse()
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 10
                    color: Theme.accent
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: appController.semesterName + " · 第 1 教学周 · " + appController.firstWeekMonday
                color: Theme.inkSoft
                font.pixelSize: 12
                elide: Text.ElideRight
            }
            Button {
                text: "节次设置"
                flat: true
                onClicked: appController.navigate("time")
                contentItem: Text {
                    text: parent.text
                    color: Theme.accent
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: timetableGrid.width
            contentHeight: timetableGrid.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            Item {
                id: timetableGrid
                width: Math.max(scroll.width, 980)
                height: appController.timetableLayout.dayHeaderHeight + appController.sectionModel.count * appController.timetableLayout.sectionHeight
                property real dayWidth: (width - appController.timetableLayout.timeColumnWidth) / 7

                Rectangle {
                    x: 0
                    y: 0
                    width: appController.timetableLayout.timeColumnWidth
                    height: appController.timetableLayout.dayHeaderHeight
                    color: Theme.surfaceGlass
                    border.color: Theme.border
                }

                Repeater {
                    model: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    delegate: Rectangle {
                        x: appController.timetableLayout.timeColumnWidth + index * timetableGrid.dayWidth
                        y: 0
                        width: timetableGrid.dayWidth
                        height: appController.timetableLayout.dayHeaderHeight
                        color: Theme.surfaceGlass
                        border.color: Theme.border
                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            color: Theme.inkSoft
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }

                Repeater {
                    model: 7 * appController.sectionModel.count
                    delegate: Rectangle {
                        property int row: Math.floor(index / 7)
                        property int day: index % 7
                        x: appController.timetableLayout.timeColumnWidth + day * timetableGrid.dayWidth + appController.timetableLayout.cellGap / 2
                        y: appController.timetableLayout.dayHeaderHeight + row * appController.timetableLayout.sectionHeight + appController.timetableLayout.cellGap / 2
                        width: timetableGrid.dayWidth - appController.timetableLayout.cellGap
                        height: appController.timetableLayout.sectionHeight - appController.timetableLayout.cellGap
                        radius: 8
                        color: Theme.surface
                        border.color: Theme.border
                    }
                }

                Repeater {
                    model: appController.sectionModel
                    delegate: Rectangle {
                        x: 0
                        y: appController.timetableLayout.dayHeaderHeight + index * appController.timetableLayout.sectionHeight
                        width: appController.timetableLayout.timeColumnWidth
                        height: appController.timetableLayout.sectionHeight
                        color: "transparent"
                        Text {
                            anchors.centerIn: parent
                            text: model.startTime + "\n" + model.endTime
                            color: Theme.muted
                            font.pixelSize: 10
                            lineHeight: 1.2
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }

                Repeater {
                    model: appController.courseModel
                    delegate: CourseCard {
                        property int startRow: appController.sectionModel.rowForSection(model.startSection)
                        property int endRow: appController.sectionModel.rowForSection(model.endSection)
                        x: appController.timetableLayout.timeColumnWidth + (model.weekday - 1) * timetableGrid.dayWidth + appController.timetableLayout.cellGap
                        y: appController.timetableLayout.dayHeaderHeight + startRow * appController.timetableLayout.sectionHeight + appController.timetableLayout.cellGap
                        width: timetableGrid.dayWidth - appController.timetableLayout.cellGap * 2
                        height: Math.max(appController.timetableLayout.sectionHeight - appController.timetableLayout.cellGap * 2, (endRow - startRow + 1) * appController.timetableLayout.sectionHeight - appController.timetableLayout.cellGap * 2)
                        visible: startRow >= 0 && endRow >= startRow
                        z: 2
                        courseId: model.courseId
                        courseName: model.name
                        scheduleLabel: "第" + model.startSection + "–" + model.endSection + "节 · " + model.startWeek + "–" + model.endWeek + "周"
                        teacher: model.teacher
                        locationText: model.locationText || ((model.building || "") + " " + (model.room || "")).trim()
                        courseColor: model.color
                        needsReview: model.needsReviewFields.length > 0
                        onEditRequested: page.editCourse(courseId)
                    }
                }

                Rectangle {
                    visible: appController.courseModel.count === 0
                    x: appController.timetableLayout.timeColumnWidth + 20
                    y: appController.timetableLayout.dayHeaderHeight + 22
                    width: timetableGrid.width - appController.timetableLayout.timeColumnWidth - 40
                    height: 100
                    radius: Theme.radius
                    color: Theme.surfaceGlass
                    border.color: Theme.border
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        Text { Layout.alignment: Qt.AlignHCenter; text: "还没有课程"; color: Theme.ink; font.pixelSize: 15; font.bold: true }
                        Text { Layout.alignment: Qt.AlignHCenter; text: "点击右上角添加第一门课程"; color: Theme.muted; font.pixelSize: 11 }
                    }
                }
            }
        }
    }
}
