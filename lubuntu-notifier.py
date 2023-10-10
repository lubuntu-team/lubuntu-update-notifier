#!/usr/bin/python3
# coding=utf-8

# Copyright (C) 2019 Hans P. Möller <hmollercl@lubuntu.me>
# Copyright (C) 2023 Simon Quigley <tsimonq2@lubuntu.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

''' Open Notification Dialog to enable upgrade'''

import sys
import subprocess
from pathlib import Path
import apt_pkg
from argparse import ArgumentParser
import gettext

from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QDialogButtonBox,
                             QHBoxLayout, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from launchpadlib.launchpad import Launchpad

import importlib.util

spec = importlib.util.spec_from_file_location(
    "apt_check", "/usr/lib/update-notifier/apt_check.py")
apt_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apt_check)

class RunUpgradeThread(QThread):
    finished = pyqtSignal()

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        process = subprocess.Popen(self.cmd)
        process.wait()
        self.finished.emit()

class Dialog(QWidget):
    ''' UI '''

    def __init__(self, upgrades, security_upgrades, release_upgrade, version, reboot_required, upg_path):
        QWidget.__init__(self)
        self.upgrades = upgrades
        self.security_upgrades = security_upgrades
        self.release_upgrade = release_upgrade
        self.version = version
        self.upg_path = upg_path
        self.reboot_required = reboot_required

        try:
            self.launchpad = Launchpad.login_anonymously("lubuntu-update-notifier", "production", version="devel")
        except:
            self.launchpad = None

        apt_pkg.init()
        try:
            self.cache = apt_pkg.Cache()
        except SystemError as e:
            sys.stderr.write(_("Error: Opening the cache (%s)") % e)
            sys.exit(-1)
        self.depcache = apt_pkg.DepCache(self.cache)
        self.records = apt_pkg.PackageRecords(self.cache)

        self.initUI()
        self.buttonBox.rejected.connect(self.call_reject)
        self.buttonBox.clicked.connect(self.call_upgrade)

    def initUI(self):
        ''' UI initialization '''
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignHCenter)
        self.label.setTextFormat(Qt.RichText)
        self.label.setOpenExternalLinks(True)

        self.tw = QTreeWidget()
        if self.security_upgrades > 0:
            self.tw.setColumnCount(2)
            self.tw.setHeaderLabels([_('Affected Packages'),
                                     _('Security')])
            self.tw.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tw.header().setStretchLastSection(False)
        else:
            self.tw.setColumnCount(1)
            self.tw.setHeaderLabels([_('Affected Packages')])
            self.tw.setHeaderHidden(True)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel |
                                          QDialogButtonBox.Apply)
        text = ""

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.buttonBox)
        hbox.addStretch(1)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label)
        vbox.addWidget(self.tw)
        vbox.addLayout(hbox)

        self.tw.setVisible(False)

        if self.upg_path is None and not self.release_upgrade:
            self.buttonBox.button(QDialogButtonBox.Apply).setVisible(False)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 500, 150)
        self.setWindowTitle("Update Notifier")
        self.center()

        if self.upgrades > 0:
            self.tw.setVisible(True)
            self.depcache.upgrade(True)  # True for non safe.
            pkg_install = list()
            pkg_upgrade = list()
            pkg_delete = list()
            for p in self.cache.packages:
                if self.depcache.marked_delete(p):
                    pkg_delete.append(p)
                elif self.depcache.marked_install(p):
                    pkg_install.append([p, self.depcache.get_candidate_ver(p)])
                elif self.depcache.marked_upgrade(p):
                    pkg_upgrade.append([p, self.depcache.get_candidate_ver(p)])
            text = _("There are upgrades available. Do you want to do a system"
                     " upgrade?")
            text += "\n"
            text += _("This will mean packages could be upgraded, installed or"
                      " removed.")
            if self.security_upgrades > 0:
                text += "\n" + str(self.security_upgrades)
                if self.security_upgrades == 1:
                    text += _(" is a security upgrade.")
                else:
                    text += _(" are security upgrades.")

            if len(pkg_delete) > 0:
                toDelete = QTreeWidgetItem([_('Remove')])
                for p in pkg_delete:
                    td_child = QTreeWidgetItem([p.name])
                    toDelete.addChild(td_child)
                toDelete.setIcon(0, QIcon.fromTheme("edit-delete"))
                self.tw.addTopLevelItem(toDelete)
            if len(pkg_install) > 0:
                toInstall = QTreeWidgetItem([_('Install')])
                for p in pkg_install:
                    td_child = QTreeWidgetItem([p[0].name + "  /  "
                                                + p[1].ver_str])
                    if apt_check.isSecurityUpgrade(p[1]):
                        td_child.setIcon(1, QIcon.fromTheme("security-high"))
                        toInstall.setIcon(1, QIcon.fromTheme("security-high"))
                    toInstall.addChild(td_child)
                    self.records.lookup(p[1].file_list[0])
                    short = QTreeWidgetItem([self.records.short_desc])
                    td_child.addChild(short)
                toInstall.setIcon(0, QIcon.fromTheme(
                    "system-software-install"))
                self.tw.addTopLevelItem(toInstall)
            if len(pkg_upgrade) > 0:
                toUpgrade = QTreeWidgetItem([_('Upgrade')])
                for p in pkg_upgrade:
                    td_child = QTreeWidgetItem(
                        [p[0].name + "  /  " + p[0].current_ver.ver_str +
                         "  ->  " + p[1].ver_str])
                    if apt_check.isSecurityUpgrade(p[1]):
                        td_child.setIcon(1, QIcon.fromTheme("security-high"))
                        toUpgrade.setIcon(1, QIcon.fromTheme("security-high"))
                    toUpgrade.addChild(td_child)
                    self.records.lookup(p[1].file_list[0])
                    short = QTreeWidgetItem([self.records.short_desc])
                    td_child.addChild(short)
                toUpgrade.setIcon(0, QIcon.fromTheme("system-software-update"))
                self.tw.addTopLevelItem(toUpgrade)
        elif self.release_upgrade:
            self.setWindowTitle("Upgrade Lubuntu")
            text = self.new_version_text()
            self.buttonBox.clicked.connect(self.call_release_upgrader)

        if self.reboot_required:
            if text == "":
                text = _("Reboot required")
                self.buttonBox.button(QDialogButtonBox.Apply).setVisible(False)
            else:
                text += "\n"
                text += _("Reboot required")

        self.label.setText(text)

    def center(self):
        ''' puts UI in center of screen '''
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def call_reject(self):
        ''' when close button is pressed, quit '''
        app.quit()

    def call_upgrade(self, btnClicked):
        if(self.buttonBox.buttonRole(btnClicked) ==
           QDialogButtonBox.ApplyRole):
            ''' starts upgrade process '''
            self.label.setText(_("Upgrading..."))
            self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Apply).setVisible(False)
            self.tw.setVisible(False)

            cmd = ["lxqt-sudo", self.upg_path, "--full-upgrade"]
            self.thread = RunUpgradeThread(cmd)
            self.thread.finished.connect(self.on_upgrade_finished)
            self.thread.start()

    def on_upgrade_finished(self):
        if self.upg_path == "terminal":
            text = _("Upgrade finished")

            reboot_required_path = Path("/var/run/reboot-required")
            if reboot_required_path.exists():
                text += "\n" + _("Reboot required")
            self.label.setText(text)
            self.closeBtn.setVisible(True)
            self.closeBtn.setEnabled(True)
        elif self.release_upgrade:
            self.setWindowTitle("Upgrade Lubuntu")
            self.label.setText(self.new_version_text())
            self.buttonBox.button(QDialogButtonBox.Apply).setEnabled(True)
            self.buttonBox.button(QDialogButtonBox.Apply).setVisible(True)
            self.buttonBox.clicked.disconnect(self.call_upgrade)
            self.buttonBox.clicked.connect(self.call_release_upgrader)
        else:
            app.quit()

    def call_release_upgrader(self, btnClicked):
        if self.buttonBox.buttonRole(btnClicked) == QDialogButtonBox.ApplyRole:
            cmd = ["lxqt-sudo", "do-release-upgrade", "-m", "desktop", "-f", "DistUpgradeViewKDE"]
            self.thread2 = RunUpgradeThread(cmd)
            self.thread2.finished.connect(self.call_reject)
            self.thread2.start()
        elif self.buttonBox.buttonRole(btnClicked) == QDialogButtonBox.RejectRole:
            self.call_reject()

    def new_version_text(self):
        try:
            main_version = '.'.join(self.version.split()[0].split('.')[:2])
            codename = self.launchpad.distributions["ubuntu"].getSeries(name_or_version=main_version).name
        except:
            codename = None

        if codename:
            url_suffix = ""
            point_release = self.version.split(".")[2].split(" ")[0] if "." in self.version[4:] else "0"
            if point_release != "0":
                url_suffix = f"-{int(point_release)}"
            url_suffix += "-released"

            text = f"<a href='https://lubuntu.me/{codename}{url_suffix}/'>"
            text += _("A new version of Lubuntu") + "</a> "
            text += _("is available. Would you like to install it?")
        else:
            text = _("A new version of Lubuntu is available. Would you like to install it?")

        return text


class App(QApplication):
    '''application'''

    def __init__(self, upgrades, security_upgrades, release_upgrade, version, reboot_required, upg_path,
                 *args):
        QApplication.__init__(self, *args)
        self.dialog = Dialog(upgrades, security_upgrades, release_upgrade, version, reboot_required,
                             upg_path)
        self.dialog.show()



def main(args, upgrades, security_upgrades, release_upgrade, version, reboot_required, upg_path):
    '''main'''
    global app
    app = App(upgrades, security_upgrades, release_upgrade, version, reboot_required, upg_path, args)
    app.setWindowIcon(QIcon.fromTheme("system-software-update"))
    app.exec_()


if __name__ == "__main__":
    localesApp = "lubuntu-update-notifier"
    localesDir = "/usr/share/locale"
    gettext.bindtextdomain(localesApp, localesDir)
    gettext.textdomain(localesApp)
    _ = gettext.gettext

    parser = ArgumentParser()
    parser.add_argument("-p",
                        "--upgrader-sw",
                        dest="upg_path",
                        help=_("Define software/app to open for upgrade"),
                        metavar="APP")
    parser.add_argument("-u",
                        "--upgrades",
                        dest="upgrades",
                        help=_("How many upgrades are available"),
                        metavar="APP")
    parser.add_argument("-s",
                        "--security-upg",
                        dest="security_upgrades",
                        help=_("How many security upgrades are available"),
                        metavar="APP")
    parser.add_argument("-r",
                        "--release-upgrade",
                        dest="release_upgrade",
                        help=_("Whether a release upgrade is required"),
                        type=str,
                        metavar="APP")
    parser.add_argument("-v",
                        "--release-upgrade-version",
                        dest="version",
                        help=_("If a release upgrade is available, provide the version"),
                        type=str,
                        metavar="APP")

    options = parser.parse_args()

    reboot_required_path = Path("/var/run/reboot-required")
    reboot_required = reboot_required_path.exists()

    if int(options.release_upgrade) == 0:
        options.release_upgrade = True
    else:
        options.release_upgrade = False

    if int(options.upgrades) > 0 or reboot_required or options.release_upgrade:
        main(sys.argv, int(options.upgrades), int(options.security_upgrades),
             options.release_upgrade, options.version, reboot_required, options.upg_path)
