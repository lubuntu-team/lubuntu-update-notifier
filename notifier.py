#!/usr/bin/python3

import sys
from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QPushButton,
							QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import (Qt, QProcess)
from PyQt5.QtGui import QIcon
from optparse import OptionParser

from pathlib import Path

import subprocess
#from upgrader import DialogUpg #still dont know how to ask for sudo when calling a function

class Dialog(QWidget):
    def __init__(self, upgrades, security_upgrades, reboot_required, upg_path):
        QWidget.__init__(self)
        self.upgrades = upgrades
        self.security_upgrades = security_upgrades
        self.upg_path = upg_path

        self.initUI()
        self.upgradeBtn.clicked.connect(self.call_upgrade)
        self.closeBtn.clicked.connect(self.call_reject)

    def initUI(self):
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignHCenter)
        self.upgradeBtn = QPushButton("Upgrade")
        self.closeBtn = QPushButton("Close")
        text = ""

        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.upgradeBtn)
        hbox.addWidget(self.closeBtn)
        hbox.addStretch(1)

        vbox=QVBoxLayout()
        vbox.addWidget(self.label)
        vbox.addLayout(hbox)

        if self.upg_path == None:
            self.upgradeBtn.setVisible(False)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 500, 150)
        self.setWindowTitle("Update Notifier")
        self.center()

        if self.upgrades > 0:
            '''text = "There are(is) %s upgrade(s) available and %s security update(s) available\n" % (self.upgrades, self.security_upgrades)
            text = text + "Do you want to do a system upgrade?\nThis will upgrade, install and remove packages"'''
            text = "There are upgrades available. Do you want to do a system upgrade?\nThis will mean packages could be upgraded, installed, or removed."


        if reboot_required:
            if text == "":
                text = "Reboot is needed"
                self.upgradeBtn.setVisible(False)
            else:
                text = text + "\nReboot is needed"

        self.label.setText(text)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def call_reject(self):
        app.quit()

    def call_upgrade(self):
        self.label.setText("Upgrading....")

        #TODO maybe open another thread so notifier won't freeze
        if self.upg_path == "terminal":
            #cmd = ['qterminal', '-e', 'sudo', 'apt', 'dist-upgrade']
            cmd = ['qterminal', '-e', './upg.sh']
        else:
            cmd = ['lxqt-sudo', self.upg_path,'--full-upgrade']
        #process = subprocess.Popen(self.upg_path)
        #process = subprocess.Popen(cmd, shell=True)
        self.upgradeBtn.setVisible(False)
        self.upgradeBtn.setEnabled(False)
        process = subprocess.Popen(cmd)
        process.wait()

        '''options.fullUpgrade = 1
        dialogUpg = DialogUpg(optionss, pkg=self.packages)
        dialogUpg.show()'''

        if self.upg_path == "terminal":
            text = "Upgrade finished"

            reboot_required_path = Path("/var/run/reboot-required")
            if reboot_required_path.exists():
                text = text + "\n" + "Restart required"
            self.label.setText(text)
            self.closeBtn.setVisible(True)
            self.closeBtn.setEnabled(True)

        else:
            app.quit()

class App(QApplication):
    def __init__(self, upgrades, security_upgrades, reboot_required, upg_path,
    			*args):
        QApplication.__init__(self, *args)
        self.dialog = Dialog(upgrades, security_upgrades, reboot_required,
        					 upg_path)
        self.dialog.show()

def main(args, upgrades, security_upgrades, reboot_required, upg_path):
    global app
    app = App(upgrades, security_upgrades, reboot_required, upg_path, args)
    app.setWindowIcon(QIcon.fromTheme("system-software-update"))
    app.exec_()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p",
                      "--upgrader-sw",
                      dest="upg_path",
                      help="Define software/app to open for upgrade",
                      metavar="APP")
    parser.add_option("-u",
                      "--upgrades",
                      dest="upgrades",
                      help="How many upgrades are available",
                      metavar="APP")
    parser.add_option("-s",
                      "--security-upg",
                      dest="security_upgrades",
                      help="How many security upgrades are available",
                      metavar="APP")

    (options, args) = parser.parse_args()

    reboot_required_path = Path("/var/run/reboot-required")
    if reboot_required_path.exists():
        reboot_required = True
    else:
        reboot_required = False

    if int(options.upgrades) > 0 or reboot_required:
        main(sys.argv, int(options.upgrades), int(options.security_upgrades), reboot_required, options.upg_path)
