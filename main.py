# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

import sys
import os
from ftplib import FTP
import re
from datetime import date
from TreeModel import treeModel as TreeModel


class Ui_MainWindow(object):
    ftp = None
    dosyaSize = 0
    transferSize = 0
    blockSize = 1024

    def baglan(self):
        if self.ftp is not None:
            self.baglantiKes()

        try:
            self.ftp = FTP()
            self.ftp.encoding = "UTF-8"
            self.sunucu = self.sunucuText.text()
            self.port = int(self.portText.text())
            self.kullanici = self.kullaniciText.text()
            self.sifre = self.sifreText.text()

            self._statuBas(self.sunucu + " sunucusuna bağlanılıyor...", bilgi=True)
            if self.sunucu != "":
                self._statuBas(self.ftp.connect(host=self.sunucu, port=self.port))

            if self.kullanici != "":
                self._statuBas(self.ftp.login(user=self.kullanici, passwd=self.sifre))

            self.treeVeListBagla()
            self.suankiDirs()
        except Exception as e:
            self._hataBas(e)

    def baglantiKes(self):
        try:
            if self.ftp is not None:
                self._statuBas(self.sunucu + " sunucu bağlantısı kesiliyor...", onemliBilgi=True)
                self._statuBas(self.ftp.quit())
                self.ftp.close()
                self.ftp = None

        except Exception as e:
            self._hataBas(e)

    def dosyaYukle(self, dosya):
        try:
            if self.ftp is None:
                raise self.CustomHata("Server Bağlantısı Yok")

            self._statuBas(dosya.fileName() + " dosya aktarımı başladı.", bilgi=True)
            self.progressBar.setProperty("value", 0)
            self.dosyaSize = os.path.getsize(dosya.absoluteFilePath())
            self.transferSize = 0
            dosyaAdi = dosya.fileName()

            self._statuBas(self.ftp.storbinary("STOR " + dosyaAdi,
                                               open(dosya.absoluteFilePath(), "rb"),
                                               blocksize=self.blockSize,
                                               callback=lambda block: self._updateProgress(block)))

            self.dirListele()
        except Exception as e:
            self._hataBas(e)

    def dosyaIndir(self, dosyaAdi):
        try:
            if self.ftp is None:
                raise self.CustomHata("Server Bağlantısı Yok")

            self.progressBar.setProperty("value", 0)
            self.dosyaSize = self.ftp.size(dosyaAdi)
            self.transferSize = 0

            self._statuBas(dosyaAdi + " dosya aktarımı başladı.", bilgi=True)
            inenDosya = open(os.path.join(self.lokalPWD, dosyaAdi), "wb")

            self._statuBas(self.ftp.retrbinary("RETR " + dosyaAdi,
                                               blocksize=self.blockSize,
                                               callback=lambda block: self._updateProgress(block, inenDosya)))

            inenDosya.close()
            self.dirListele()
        except Exception as e:
            self._hataBas(e)

    def isimDegis(self, eskiIsim, yeniIsim, lokal=True):
        try:
            if self.ftp == None:
                raise self.CustomHata("Server Bağlantısı Yok")

            if lokal:
                self._statuBas("Lokal dosya isim değişikliği " + eskiIsim + " -> " + yeniIsim + " isteği.", bilgi=True)
                os.rename(eskiIsim, yeniIsim)
            else:
                self._statuBas("Uzak dosya isim değişikliği " + eskiIsim + " -> " + yeniIsim + " isteği.", bilgi=True)
                self._statuBas(self.ftp.rename(eskiIsim, yeniIsim))

            self.dirListele()
        except Exception as e:
            self._hataBas(e)

    def sil(self, dosyaIsim, directory=False, lokal=True):
        try:
            if self.ftp == None:
                raise self.CustomHata("Server Bağlantısı Yok")

            if lokal:
                if directory:
                    self._statuBas("Lokal " + dosyaIsim + " dizini siliniyor!", onemliBilgi=True)
                    os.rmdir(dosyaIsim)
                else:
                    self._statuBas("Lokal " + dosyaIsim + " dosyası siliniyor!", onemliBilgi=True)
                    os.remove(dosyaIsim)
            else:
                if directory:
                    self._statuBas("Uzak " + dosyaIsim + " dizini siliniyor!", onemliBilgi=True)
                    self._statuBas(self.ftp.rmd(dosyaIsim))
                else:
                    self._statuBas("Uzak " + dosyaIsim + " dosyası siliniyor!", onemliBilgi=True)
                    self._statuBas(self.ftp.delete(dosyaIsim))

            self.dirListele()
        except os.error as e:
            self._hataBas(e)
        except Exception as e:
            self._hataBas(e)

    def yeniDizin(self, dizinAdi, lokal=True):
        try:
            if self.ftp == None:
                raise self.CustomHata("Server Bağlantısı Yok")

            if lokal:
                self._statuBas("Lokal " + dizinAdi + " dizini oluşturuluyor.", bilgi=True)
                os.mkdir(dizinAdi)
            else:
                self._statuBas("Uzak " + dizinAdi + " dizini oluşturuluyor.", bilgi=True)
                self._statuBas(self.ftp.mkd(dizinAdi))
            self.dirListele()
        except os.error as e:
            self._hataBas(e)
        except Exception as e:
            self._hataBas(e)

    def lokalDirDegis(self, signal):
        fi = signal.model().fileInfo(signal)
        self._statuBas("Lokal dizin değişikliği:<br> " +
                       "Eski Dizin: " + self.lokalPWD + "<br>" +
                       "Yeni Dizin: " + fi.absoluteFilePath(), bilgi=True)
        os.chdir(fi.absoluteFilePath())
        self.suankiDirs()

    def uzakDirDegis(self, signal):
        try:
            if self.ftp == None:
                raise self.CustomHata("Server Bağlantısı Yok")

            file = signal.model().fileInfo(signal)
            yeniDir = file.path + "/" + file.name
#            print(yeniDir, "-", self.uzakPWD)
            if yeniDir != self.uzakPWD:
                self._statuBas("Uzak dizin değişikliği:<br> " +
                               "Eski Dizin: " + self.uzakPWD + "<br>" +
                               "Yeni Dizin: " + yeniDir, bilgi=True)
                self._statuBas(self.ftp.cwd(file.path + "/" + file.name))
                self.suankiDirs()
        except Exception as e:
            self._hataBas(e)

    def dirListele(self):
        try:
            if self.ftp is None:
                raise self.CustomHata("Server Bağlantısı Yok")

            self._statuBas("Dizinler Listeleniyor:<br> " +
                           "Lokal Dizin: " + self.lokalPWD + "<br>" +
                           "Uzak Dizin: " + self.uzakPWD, bilgi=True)

            index = self.lokalDirModel.index(self.lokalPWD)
            self.lokalDirList.setRootIndex(index)

            uzakDosyalar = []
            uzakDirs = []
            self.ftp.dir(uzakDosyalar.append)
            self.uzakDirModel = QtGui.QStandardItemModel()
            self.uzakDirModel.setHorizontalHeaderLabels(["Name", "Size", "Type", "Date Modified"])
            self.uzakDirList.setModel(self.uzakDirModel)
            self.uzakDirList.verticalHeader().hide()
            self.uzakDirList.setSortingEnabled(True)

            self.uzakTreeModel = TreeModel()
            self.uzakTree.setModel(self.uzakTreeModel)

            if len(uzakDosyalar) == 0:
                self._statuBas(self.ftp.cwd(".."))
                self.suankiDirs()
                return

            for x in uzakDosyalar:
                pattern = "(?P<perm>[dlrwxtTbcsSp\+\-]+) +(?P<link_count>\d+) +(?P<owner>\d+) +(?P<group>\d+) +(?P<size>\d+) +(?P<mdate>[a-zA-Z]{3} +\d{1,2}) +(?P<ys>\d{4}|\d{2}:\d{2}) +(?P<name>((.+?(?= -> ))|.+))( -> )?(?P<link>.+)?"
                m = re.match(pattern, x)

                if m.group("perm")[0] == "d":
                    dosyaType = "Folder"
                    uzakDirs.append([m.group("name"), self.uzakPWD])
                elif m.group("perm")[0] == "l":
                    dosyaType = "symLink"
                else:
                    extension = m.group("name").split(".")
                    if len(extension) >= 2:
                        dosyaType = extension[-1] + " "
                    else:
                        dosyaType = ""

                    dosyaType += "File"

                ys = str(date.today().year) + " " + m.group("ys") if ":" in m.group("ys") else m.group("ys")
                dateModified = m.group("mdate") + " " + ys
                row = [QtGui.QStandardItem(m.group("name")),
                       QtGui.QStandardItem(m.group("size")),
                       QtGui.QStandardItem(dosyaType),
                       QtGui.QStandardItem(dateModified)]
                self.uzakDirModel.appendRow(row)
            self.uzakTreeModel.setupModelData(uzakDirs)
#            self.uzakTree.setRootIndex(self.uzakTreeModel.getIndex(self.uzakPWD))
            self.uzakTree.expandAll()

            for x in range(len(self.uzakDirList.horizontalHeader())):
                self.uzakDirList.horizontalHeader().setSectionResizeMode(x, QtWidgets.QHeaderView.Stretch)

            for x in range(len(self.lokalDirList.horizontalHeader())):
                self.lokalDirList.horizontalHeader().setSectionResizeMode(x, QtWidgets.QHeaderView.Stretch)

        except Exception as e:
            self._hataBas(e)

    def suankiDirs(self):
        try:
            if self.ftp == None:
                raise self.CustomHata("Server Bağlantısı Yok")

            self.lokalPWD = os.path.abspath(".")
            self.uzakPWD = self.ftp.pwd()
            self.lokalPWDText.setText(self.lokalPWD)
            self.uzakPWDText.setText(self.uzakPWD)

            index = self.lokalTreeModel.index(self.lokalPWD)
            self.lokalTree.setCurrentIndex(index)
            self.dirListele()
        except Exception as e:
            self._hataBas(e)

    def treeVeListBagla(self):
        self.lokalDirModel = QtWidgets.QFileSystemModel()
        self.lokalDirModel.setRootPath("")
        self.lokalDirList.setModel(self.lokalDirModel)
        self.lokalDirList.verticalHeader().hide()
        self.lokalDirList.setSortingEnabled(True)

        self.lokalTreeModel = QtWidgets.QFileSystemModel()
        self.lokalTreeModel.setRootPath("")
        self.lokalTreeModel.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.lokalTree.setModel(self.lokalTreeModel)
        for i in range(1, self.lokalTreeModel.columnCount()):
            self.lokalTree.hideColumn(i)

    def lokalDirSagTik(self, QPos=None):
        parent = self.lokalDirList.sender()
        pPos = parent.mapToGlobal(QtCore.QPoint(0, 0))
        mPos = pPos + QPos

        self.lokalDirMenu.move(mPos)
        self.lokalDirMenu.show()

    def uzakDirSagTik(self, QPos=None):
        parent=self.uzakDirList.sender()
        pPos=parent.mapToGlobal(QtCore.QPoint(0, 0))
        mPos=pPos+QPos

        self.uzakDirMenu.move(mPos)
        self.uzakDirMenu.show()

    def lokalDirMenuAction(self, action):
        if len(self.lokalDirList.selectedIndexes()) > 0:
            index = self.lokalDirList.selectedIndexes()[0]
            it = index.model().fileInfo(index)
            if action.data() == 1:
                self.dosyaYukle(it)
            elif action.data() == 2:
                yeniIsim, okPressed = QtWidgets.QInputDialog.getText(self.lokalDirList, it.fileName() + " Dosyasını/Dizinini Yeniden Adlandır","Yeni İsim:", QtWidgets.QLineEdit.Normal, "")
                if okPressed and yeniIsim != '':
                    self.isimDegis(it.fileName(), yeniIsim)
            elif action.data() == 3:
                sil = QtWidgets.QMessageBox.question(self.lokalDirList,
                                                   'Emin misiniz?',
                                                   it.fileName() + " adlı dosyayı/dizini silmek istediğinize emin misiniz?",
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)
                if sil == QtWidgets.QMessageBox.Yes:
                    self.sil(it.fileName(), directory=it.isDir())
            elif action.data() == 4:
                dizinAdi, okPressed = QtWidgets.QInputDialog.getText(self.lokalDirList, "Yeni Dizin","Dizin Adı:", QtWidgets.QLineEdit.Normal, "")
                if okPressed and dizinAdi != '':
                    self.yeniDizin(dizinAdi)

    def uzakDirMenuAction(self, action):
        if len(self.uzakDirList.selectedIndexes()) > 0:
            index = self.uzakDirList.selectedIndexes()[0]
            it = index.model().item(index.row())
            if action.data() == 1:
                self.dosyaIndir(it.text())
            elif action.data() == 2:
                yeniIsim, okPressed = QtWidgets.QInputDialog.getText(self.uzakDirList, it.text() + " Dosyasını/Dizinini Yeniden Adlandır","Yeni İsim:", QtWidgets.QLineEdit.Normal, "")
                if okPressed and yeniIsim != '':
                    self.isimDegis(it.text(), yeniIsim, lokal=False)
            elif action.data() == 3:
                sil = QtWidgets.QMessageBox.question(self.uzakDirList,
                                                   'Emin misiniz?',
                                                   it.text() + " adlı dosyayı/dizini silmek istediğinize emin misiniz?",
                                                   QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.No)
                if sil == QtWidgets.QMessageBox.Yes:
                    dosyaAdi = it.text()
                    it = index.model().item(index.row(), 2)
                    isDir = True if it.text() == "Folder" else False
                    self.sil(dosyaAdi, directory=isDir, lokal=False)
            elif action.data() == 4:
                dizinAdi, okPressed = QtWidgets.QInputDialog.getText(self.uzakDirList, "Yeni Dizin","Dizin Adı:", QtWidgets.QLineEdit.Normal, "")
                if okPressed and dizinAdi != '':
                    self.yeniDizin(dizinAdi, lokal=False)


    def customKomut(self):
        komut = self.customKomutText.text()
        if komut != "":
            try:
                if self.ftp == None:
                    raise self.CustomHata("Server Bağlantısı Yok")

                self._statuBas("Özel komut: " + komut, onemliBilgi=True)
                self._statuBas(self.ftp.sendcmd(komut))
                self.suankiDirs()
            except Exception as e:
                self._hataBas(e)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1024, 680)
        MainWindow.setMaximumSize(QtCore.QSize(1024, 680))
        MainWindow.setMinimumSize(QtCore.QSize(1024, 680))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.statusText = QtWidgets.QTextEdit(self.centralwidget)
        self.statusText.setGeometry(QtCore.QRect(10, 40, 1000, 171))
        self.statusText.setObjectName("statusText")
        self.statusText.setReadOnly(True)
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 1000, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.sunucuText = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.sunucuText.setObjectName("sunucuText")
        self.horizontalLayout.addWidget(self.sunucuText)
        self.label_2 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.kullaniciText = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.kullaniciText.setObjectName("kullaniciText")
        self.horizontalLayout.addWidget(self.kullaniciText)
        self.label_3 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.sifreText = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.sifreText.setEchoMode(QtWidgets.QLineEdit.Password)
        self.sifreText.setObjectName("sifreText")
        self.horizontalLayout.addWidget(self.sifreText)
        self.label_4 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.portText = QtWidgets.QLineEdit(self.horizontalLayoutWidget)
        self.portText.setMaximumSize(QtCore.QSize(85, 16777215))
        self.portText.setMaxLength(5)
        self.portText.setObjectName("portText")
        self.horizontalLayout.addWidget(self.portText)
        self.baglanButton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.baglanButton.setObjectName("baglanButton")
        self.horizontalLayout.addWidget(self.baglanButton)
        self.baglantiyiKesButtton = QtWidgets.QPushButton(self.horizontalLayoutWidget)
        self.baglantiyiKesButtton.setObjectName("baglantiyiKesButtton")
        self.horizontalLayout.addWidget(self.baglantiyiKesButtton)
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 239, 1000, 395))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label_6 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 0, 1, 1, 1)
        self.lokalDirList = QtWidgets.QTableView(self.gridLayoutWidget)
        self.lokalDirList.setObjectName("lokalDirList")
        self.gridLayout.addWidget(self.lokalDirList, 3, 0, 1, 1)
        self.lokalPWDText = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lokalPWDText.setReadOnly(True)
        self.lokalPWDText.setObjectName("lokalPWDText")
        self.gridLayout.addWidget(self.lokalPWDText, 1, 0, 1, 1)
        self.lokalTree = QtWidgets.QTreeView(self.gridLayoutWidget)
        self.lokalTree.setMaximumSize(QtCore.QSize(16777215, 150))
        self.lokalTree.setObjectName("lokalTree")
        self.gridLayout.addWidget(self.lokalTree, 2, 0, 1, 1)
        self.uzakPWDText = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.uzakPWDText.setReadOnly(True)
        self.uzakPWDText.setObjectName("uzakPWDText")
        self.gridLayout.addWidget(self.uzakPWDText, 1, 1, 1, 1)
        self.uzakDirList = QtWidgets.QTableView(self.gridLayoutWidget)
        self.uzakDirList.setObjectName("uzakDirList")
        self.gridLayout.addWidget(self.uzakDirList, 3, 1, 1, 1)
        self.uzakTree = QtWidgets.QTreeView(self.gridLayoutWidget)
        self.uzakTree.setMaximumSize(QtCore.QSize(16777215, 150))
        self.uzakTree.setObjectName("uzakTree")
        self.gridLayout.addWidget(self.uzakTree, 2, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(10, 640, 1000, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(10, 210, 1000, 31))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_7 = QtWidgets.QLabel(self.horizontalLayoutWidget_2)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_2.addWidget(self.label_7)
        self.customKomutText = QtWidgets.QLineEdit(self.horizontalLayoutWidget_2)
        self.customKomutText.setObjectName("customKomutText")
        self.horizontalLayout_2.addWidget(self.customKomutText)
        self.customKomutButton = QtWidgets.QPushButton(self.horizontalLayoutWidget_2)
        self.customKomutButton.setObjectName("customKomutButton")
        self.horizontalLayout_2.addWidget(self.customKomutButton)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.lokalDirMenu=QtWidgets.QMenu(self.lokalDirList)
        self.lokalDirMenu.addAction('Karşıya Yükle').setData(1)
        self.lokalDirMenu.addAction('Yeniden Adlandır').setData(2)
        self.lokalDirMenu.addAction('Sil').setData(3)
        self.lokalDirMenu.addAction('Yeni Klasör').setData(4)
        self.lokalDirMenu.triggered.connect(self.lokalDirMenuAction)
        self.lokalDirList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lokalDirList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows);
        self.lokalDirList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection);
        self.lokalDirList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lokalDirList.customContextMenuRequested.connect(self.lokalDirSagTik)

        self.uzakDirMenu=QtWidgets.QMenu(self.uzakDirList)
        self.uzakDirMenu.addAction('İndir').setData(1)
        self.uzakDirMenu.addAction('Yeniden Adlandır').setData(2)
        self.uzakDirMenu.addAction('Sil').setData(3)
        self.uzakDirMenu.addAction('Yeni Klasör').setData(4)
        self.uzakDirMenu.triggered.connect(self.uzakDirMenuAction)
        self.uzakDirList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.uzakDirList.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows);
        self.uzakDirList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection);
        self.uzakDirList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.uzakDirList.customContextMenuRequested.connect(self.uzakDirSagTik)

        self.lokalTree.clicked.connect(self.lokalDirDegis)
        self.uzakTree.clicked.connect(self.uzakDirDegis)
        self.baglanButton.clicked.connect(self.baglan)
        self.baglantiyiKesButtton.clicked.connect(self.baglantiKes)
        self.customKomutButton.clicked.connect(self.customKomut)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Elendil - FTP Client"))
        self.label.setText(_translate("MainWindow", "Sunucu:"))
        self.label_2.setText(_translate("MainWindow", "Kullanıcı Adı:"))
        self.label_3.setText(_translate("MainWindow", "Şifre:"))
        self.label_4.setText(_translate("MainWindow", "Port:"))
        self.portText.setText(_translate("MainWindow", "21"))
        self.baglanButton.setText(_translate("MainWindow", "Bağlan"))
        self.baglantiyiKesButtton.setText(_translate("MainWindow", "Bağlantıyı Kes"))
        self.customKomutButton.setText(_translate("MainWindow", "Çalıştır"))
        self.label_6.setText(_translate("MainWindow", "Uzak Sunucu:"))
        self.label_5.setText(_translate("MainWindow", "Lokal:"))
        self.label_7.setText(_translate("MainWindow", "Komut Çalıştır:"))

    def _updateProgress(self, block, inenDosya = None):
        self.transferSize += len(block)
        toplamYuzde = round((self.transferSize / self.dosyaSize) * 100)
        self.progressBar.setProperty("value", toplamYuzde)

        if inenDosya != None:
            inenDosya.write(block)

    def _statuBas(self, statu, bilgi=False, onemliBilgi=False):
        if bilgi:
            log = "<font color=\"green\">Bilgi: " + statu + "</font>"
        elif onemliBilgi:
            log = "<b><font color=\"blue\">Bilgi: " + statu + "</font></b>"
        else:
            log = "Durum: " + statu

        self.statusText.append(log)

    class CustomHata(Exception):
        def __init__(self, *args):
            self.args = [a for a in args]

    def _hataBas(self, e):
        print(e.args)
        if isinstance(e, os.error):
            self.statusText.append("<b><font color=\"red\">Hata: </font>" + e.args[1] + "</b>")
        else:
            self.statusText.append("<b><font color=\"red\">Hata: </font>" + e.args[0] + "</b>")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    frame = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(frame)
    frame.show()
    app.exec_()
