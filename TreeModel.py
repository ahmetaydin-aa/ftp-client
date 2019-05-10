#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 31 01:34:02 2019

@author: ahmet
"""

from PyQt5 import QtGui, QtCore, QtWidgets

HORIZONTAL_HEADERS = ["Name"]
    
class file_class(object):
    '''
    a trivial custom data object
    '''
    def __init__(self, name, path):
        self.name = name
        self.path = path
    
class TreeItem(object):
    '''
    a python object used to return row/column data, and keep note of
    it's parents and/or children
    '''
    def __init__(self, file, header, parentItem):
        self.file = file
        self.parentItem = parentItem
        self.header = header
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(HORIZONTAL_HEADERS)
    
    def data(self, column):
        if self.file == None:
            if column == 0:
                return QtCore.QVariant(self.header)            
        else:
            if column == 0:
                return QtCore.QVariant(self.file.name)
        return QtCore.QVariant()

    def parent(self):
        return self.parentItem
    
    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

class treeModel(QtCore.QAbstractItemModel):
    '''
    a model to display a few names, ordered by sex
    '''
    def __init__(self, parent=None):
        super(treeModel, self).__init__(parent)            
        self.rootItem = TreeItem(None, "Root", None)
        self.parents = {}

    def columnCount(self, parent=None):
        if parent and parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return len(HORIZONTAL_HEADERS)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        item = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return item.data(index.column())
        if role == QtCore.Qt.UserRole:
            if item:
                return item.file

        return QtCore.QVariant()

    def headerData(self, column, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
        role == QtCore.Qt.DisplayRole):
            try:
                return QtCore.QVariant(HORIZONTAL_HEADERS[column])
            except IndexError:
                pass

        return QtCore.QVariant()

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
    
    def getIndex(self, path):
        pathParts = path.split("/")
        
        parent = pathParts[-2]
        file = self.parents[parent]
        row = file.row()
        column = 0
        parent = file.parent()
        
        return self.createIndex(row, column, file)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        if not childItem:
            return QtCore.QModelIndex()
        
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            p_Item = self.rootItem
        else:
            p_Item = parent.internalPointer()
        return p_Item.childCount()
    
    def setupModelData(self, files):
        for file in files:
            fname = file[0]
            fpath = file[1]
            pathParts = fpath.split("/")
            
            ustPath = ""
            for part in pathParts:
                if part == "":
                    part = "/"
                    
                if part not in self.parents.keys():
                    
                    if ustPath == "":
                        pf = file_class(part, "/")
                        fi = TreeItem(pf, "/", self.rootItem)
                        self.rootItem.appendChild(fi)
                    else:
                        pf = file_class(part, ustPath)
                        parentDir = ustPath.split("/")[-1]
                        if parentDir == "":
                            parentDir = "/"
                        
                        fi = TreeItem(pf, ustPath, self.parents[parentDir])
                        self.parents[parentDir].appendChild(fi)
                        
                    self.parents[part] = fi
                
                if part != "/" and ustPath != "/":
                    ustPath += "/"
                ustPath += part
                
            f = file_class(fname, fpath)
            sPart = pathParts[-1]
            if sPart == "":
                sPart = "/"
            newFile = TreeItem(f, fpath, self.parents[sPart])
            self.parents[sPart].appendChild(newFile)
    
    def fileInfo(self, index):
        if not index.isValid():
            return self.parents["/"]
        
        return index.internalPointer().file
    
    def searchModel(self, file):
        '''
        get the modelIndex for a given appointment
        '''
        parentDir = file.path.split("/")[-1]
        
        index = 0
        for child in self.parents[parentDir]:
            if file == child.file:
                index = self.createIndex(child.row(), 0, child)
        
        return index