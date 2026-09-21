import QtQuick 2.15
import QtQuick.Controls 2.15
import Scalendar.Theme 1.0

Item {
    id: root
    property string label: ""
    property string glyph: ""
    property bool selected: false
    signal clicked()
    implicitHeight: 46

    Rectangle {
        anchors.fill: parent
        radius: Theme.radiusSmall
        color: root.selected ? Theme.accentSoft : (mouse.containsMouse ? Theme.surfaceSoft : "transparent")

        Row {
            anchors.fill: parent
            anchors.leftMargin: 14
            anchors.rightMargin: 12
            spacing: 12
            Text { width: 22; anchors.verticalCenter: parent.verticalCenter; text: root.glyph; color: root.selected ? Theme.accent : Theme.inkSoft; font.pixelSize: 17; horizontalAlignment: Text.AlignHCenter }
            Text { anchors.verticalCenter: parent.verticalCenter; text: root.label; color: root.selected ? Theme.accent : Theme.inkSoft; font.pixelSize: 14; font.weight: root.selected ? Font.DemiBold : Font.Normal }
        }
    }

    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.clicked() }
}
