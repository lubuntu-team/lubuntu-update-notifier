#!/usr/bin/python3
# deppend on
# -aptdaemon
# -debconf-kde-helper
import sys
import os

#import pty
#import subprocess

from PyQt5.QtWidgets import (QWidget, QApplication, QLabel, QPushButton,
							QHBoxLayout, QVBoxLayout, QProgressBar, QTreeView,
							 QPlainTextEdit, QMessageBox)
from PyQt5 import uic
from PyQt5.QtCore import (Qt, QProcess)
from PyQt5.QtGui import (QStandardItemModel, QIcon, QTextCursor, QPalette)
from optparse import OptionParser
from aptdaemon import client
from aptdaemon.errors import NotAuthorizedError, TransactionFailed
from aptdaemon.enums import (EXIT_SUCCESS,
                             EXIT_FAILED,
                             STATUS_COMMITTING,
                             get_error_description_from_enum,
                             get_error_string_from_enum,
                             get_status_string_from_enum)
from pathlib import Path

class DialogUpg(QWidget):
    def __init__(self, options=None):
        QWidget.__init__(self)

        self.initUI()
        self.closeBtn.clicked.connect(self.call_reject)
        self.apt_client = client.AptClient()
        self.downloadText = ""
        self.detailText = ""
        self.old_short_desc=""
        self.details=""
        self.status=""
        self.errors = []
        #TODO make a terminal work to see more info
        #self.master, self.slave = pty.openpty()
        '''proc = subprocess.Popen(['qterminal'],
                            stdin=self.slave,
                            #stdout=subprocess.PIPE,
                            stdout=self.slave,
                            #stderr=subprocess.PIPE
                            stderr=self.slave)'''


        if options.fullUpgrade:
            self.trans2 = self.apt_client.upgrade_system(safe_mode=False)
            self.setWindowTitle('Full Upgrade')
        else:
            self.trans2 = self.apt_client.upgrade_system(safe_mode=True)

        if options.cacheUpdate:
            self.trans1 = self.apt_client.update_cache()
            self.update_cache()
        else:
            self.upgrade()

    def initUI(self):
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignHCenter)
        self.closeBtn = QPushButton("Close")
        self.progressBar = QProgressBar()
        self.plainTextEdit = QPlainTextEdit()
        palette = self.plainTextEdit.palette()
        palette.setColor(QPalette.Base, Qt.black)
        palette.setColor(QPalette.Text, Qt.gray)
        self.plainTextEdit.setPalette(palette)

        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.closeBtn)
        hbox.addStretch(1)

        vbox=QVBoxLayout()
        vbox.addWidget(self.label)
        vbox.addWidget(self.progressBar)
        vbox.addWidget(self.plainTextEdit)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 500, 150)
        self.setWindowTitle('Upgrade')
        self.progressBar.setVisible(False)
        self.plainTextEdit.setReadOnly(True)
        self.plainTextEdit.setVisible(False)
        self.center()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def upgrade_progress(self, transaction, progress):
        self.progressBar.setVisible(True)
        self.progressBar.setValue(progress)

    def update_progress(self, transaction, progress):
        self.progressBar.setVisible(True)
        self.progressBar.setValue(progress)
        self.label.setText("Updating cache...")

    def update_progress_download(self, transaction, uri, status, short_desc,
                                  total_size, current_size, msg):
        self.plainTextEdit.setVisible(True)
        if self.old_short_desc == short_desc: #if it's the same file we update the line, don't append new line
            self.plainTextEdit.moveCursor(QTextCursor.End)
            cursor = self.plainTextEdit.textCursor()
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            self.plainTextEdit.insertPlainText(str(current_size) + "/" + str(total_size) + " " + msg)
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
        else:
            self.plainTextEdit.moveCursor(QTextCursor.End)
            self.plainTextEdit.appendPlainText(status + " " + short_desc + "\n")
            self.plainTextEdit.insertPlainText(str(current_size) + "/" + str(total_size) + " " + msg)
            self.plainTextEdit.moveCursor(QTextCursor.End)
            self.old_short_desc = short_desc

    def upgrade_progress_download(self, transaction, uri, status, short_desc,
                                  total_size, current_size, msg):
        self.plainTextEdit.setVisible(True)
        if self.status == "status-downloading":#TODO it prints the last line after installation is complete, need to manage this.
            if self.old_short_desc == short_desc: #if it's the same file we update the line, don't append new line
                self.plainTextEdit.moveCursor(QTextCursor.End)
                cursor = self.plainTextEdit.textCursor()
                cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                self.plainTextEdit.insertPlainText(str(current_size) + "/" + str(total_size) + " " + msg)
                cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            else:
                self.plainTextEdit.moveCursor(QTextCursor.End)
                self.plainTextEdit.appendPlainText(status + " " + short_desc + "\n")
                self.plainTextEdit.insertPlainText(str(current_size) + "/" + str(total_size) + " " + msg)
                self.plainTextEdit.moveCursor(QTextCursor.End)
                self.old_short_desc = short_desc

    def update_progress_detail(self, transaction, current_items, total_items,
                                current_bytes, total_bytes, current_cps, eta):
        if total_items > 0:
            self.plainTextEdit.setVisible(True)
            if self.detailText != "Fetching " + str(current_items) + " of " + str(total_items):
                self.detailText = "Fetching " + str(current_items) + " of " + str(total_items)
                self.label.setText(self.detailText + "\n" + self.downloadText)


    def upgrade_progress_detail(self, transaction, current_items, total_items,
                                current_bytes, total_bytes, current_cps, eta):
        #self.detailText = "Upgrading..."
        #self.label.setText(self.detailText)
        if total_items > 0:
            self.plainTextEdit.setVisible(True)
            if self.detailText != "Downloaded " + str(current_items) + " of " + str(total_items):
                self.detailText = "Downloaded " + str(current_items) + " of " + str(total_items)
                self.label.setText(self.detailText + "\n" + self.downloadText)

    def upgrade_finish(self, transaction, exit_state):
        if exit_state == EXIT_FAILED:
            error_string = get_error_string_from_enum(transaction.error.code)
            error_desc = get_error_description_from_enum(transaction.error.code)

        text = "Upgrade finished"

        reboot_required_path = Path("/var/run/reboot-required")
        if reboot_required_path.exists():
            text = text + "\n" + "Restart required"
        self.progressBar.setVisible(False)

        if(len(self.errors)>0):
            text = text + "\n With some Errors"
            self.plainTextEdit.appendPlainText("Error Resume:\n")
            for error in self.errors:
                self.plainTextEdit.setEnabled(False)
                self.plainTextEdit.insertPlainText(error + "\n")
                self.plainTextEdit.insertPlainText(error_string + "\n")
                self.plainTextEdit.insertPlainText(error_desc + "\n")
                self.plainTextEdit.moveCursor(QTextCursor.End)

        self.label.setText(text)
        self.closeBtn.setVisible(True)
        self.closeBtn.setEnabled(True)
        self.plainTextEdit.setEnabled(True)

    def upgrade_error(self, transaction, error_code, error_details):
        self.plainTextEdit.setVisible(True)
        self.errors.append("Eror Code: " + str(error_code))
        self.errors.append("Error Detail: " + error_details)
        #for error in self.errors:
            #self.plainTextEdit.appendPlainText(error)
        self.plainTextEdit.setVisible(True)
        self.closeBtn.setEnabled(True)
        print("ECode: " + str(error_code) + "\n")
        print("EDetail: " + error_details + "\n")

    def upgrade_cancellable_changed(self, transaction, cancellable):
        self.closeBtn.setEnabled(cancellable)

    def update_cache(self):
        self.closeBtn.setVisible(False)
        #self.label.setText("Updating cache...")
        try:
            self.trans1.connect('finished', self.update_finish)

            self.trans1.connect('progress-changed', self.update_progress)
            self.trans1.connect('progress-details-changed',
                                     self.update_progress_detail)
            self.trans1.connect('progress-download-changed',
                                     self.update_progress_download)
            self.trans1.connect('error', self.upgrade_error)
            #status-details-changed is not needed, progress_download already hast this info when downloading
            #self.trans1.connect("status-details-changed", self.status_details_changed)
            self.trans1.connect("status-changed", self.status_changed)
            #TODO make a terminal work to see more info
            #self.trans1.set_terminal(os.ttyname(self.slave))

            self.trans1.run()
            #print(self.trans1)

        except (NotAuthorizedError, TransactionFailed) as e:
            print("Warning: install transaction not completed successfully:" +
                  "{}".format(e))

    def update_finish(self, transaction, exit_state):
        self.label.setText("Update Cache Finished")
        if exit_state == EXIT_FAILED:
            error_string = get_error_string_from_enum(transaction.error.code)
            error_desc = get_error_description_from_enum(transaction.error.code)
            self.plainTextEdit.setEnabled(False)
            self.plainTextEdit.moveCursor(QTextCursor.End)
            self.plainTextEdit.insertPlainText(error_string + "\n")
            self.plainTextEdit.insertPlainText(error_desc + "\n")
            self.plainTextEdit.moveCursor(QTextCursor.End)
            self.plainTextEdit.setEnabled(True)

        self.upgrade()

    def status_changed(self, transaction, status):
        self.status = status
        self.label.setText("Status:" + get_status_string_from_enum(status))
        print("Status:" + get_status_string_from_enum(status) + " " + status + "\n")

    def status_details_changed(self, transaction, details):
        self.plainTextEdit.setVisible(True)
        if self.details != details:
            self.details = details

            if self.status != "status-downloading": #if "Downloading xxxxx" is handled by "upgrade_progress_download" in short_desc
                self.plainTextEdit.appendPlainText(details)
                self.plainTextEdit.moveCursor(QTextCursor.End)
                self.label.setText(details)
            else:
                self.label.setText(self.detailText + "\n" + details) #if is downloading put the "Downloaded x of y" text
            #print("PTY:" + str(self.slave))

            print("Status Details:" + details)

    def upgrade(self):
        try:
            self.trans2.connect('progress-changed', self.upgrade_progress)
            self.trans2.connect('cancellable-changed',
                                     self.upgrade_cancellable_changed)
            self.trans2.connect('progress-details-changed',
                                     self.upgrade_progress_detail)
            self.trans2.connect('progress-download-changed',
                                     self.upgrade_progress_download)
            self.trans2.connect('finished', self.upgrade_finish)
            self.trans2.connect('error', self.upgrade_error)
            self.trans2.connect("status-details-changed", self.status_details_changed)
            self.trans2.connect("status-changed", self.status_changed)

            #TODO make a terminal work to see more info
            #self.trans2.set_terminal(os.ttyname(self.slave))

            '''
            #TODO implement this
            self.trans2.connect("medium-required", self._on_medium_required)
            self.trans2.connect("config-file-conflict", self._on_config_file_conflict)
            remove_obsoleted_depends
            '''
            self.trans2.set_debconf_frontend('kde')
            self.trans2.run()

        except (NotAuthorizedError, TransactionFailed) as e:
            print("Warning: install transaction not completed successfully:" +
                  "{}".format(e))

    def call_reject(self):
        app.quit()

class App(QApplication):
    def __init__(self, options, *args):
        QApplication.__init__(self, *args)
        self.dialog = DialogUpg(options)
        self.dialog.show()


def main(args, options):
    global app
    app = App(options, args)
    app.setWindowIcon(QIcon.fromTheme("system-software-update"))

    # Check for root permissions
    if os.geteuid() != 0:
        text = "Please run this software with administrative rights. To do so, run this program with lxqt-sudo."
        title = "Need administrative powers"
        msgbox = QMessageBox.critical(None, title, text)
        sys.exit(1)
    else:
        app.exec_()

if __name__ == "__main__":
    # check arguments
    parser = OptionParser()
    parser.add_option("",
                      "--cache-update",
                      action="store_true",
                      dest="cacheUpdate",
                      help="Update Cache Before Upgrade")
    parser.add_option("",
                      "--full-upgrade",
                      action="store_true",
                      dest="fullUpgrade",
                      help="Full upgrade same as dist-upgrade")
    (options, args) = parser.parse_args()

    #run it
    main(sys.argv, options)
