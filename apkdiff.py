#!/usr/bin/python3
# -*- coding:utf8 -*-
from filecmp import *
from difflib import unified_diff
import re
import argparse
from subprocess import call,STDOUT
import os
import zipfile
import shutil

outreport = "OutReport"
outPath = os.path.normpath(os.curdir+os.sep+outreport)
if not os.path.exists(outPath):
 os.makedirs(outPath)
f = open(os.path.normpath(outPath+os.sep+"report.txt"), 'w',encoding='utf-8')
fd = open(os.path.normpath(outPath + os.sep + "DiffCodeReport.txt"), 'w', encoding='utf-8')
ignore = ".*(align|apk|MF|RSA|SF|bin|so|lock|jar|svn-base|db|png|jpg|der|ttf|otf|class|dex|smali)"

at = "at/"
class_files = "classes"

class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'

def main() :
    parser = argparse.ArgumentParser(description='Diff two versions of an APK file.')
    parser.add_argument('apk1', metavar='apk1', help='Location of the first APK.')
    parser.add_argument('apk2', metavar='apk2', help='Location of the second APK.')
    parser.add_argument('-o', '--output', default=os.curdir+os.sep+"tmp"+os.sep,
                        help='The location to output the extracted files to.')

    global args
    args = parser.parse_args()
    print('args=', args)

    exists(args.apk1)
    exists(args.apk2)

    print_apk_size(args.apk1,args.apk2)

    folderExists(args.output, True)

    temp1 = args.output + "1/"
    temp2 = args.output + "2/"

    at1 = temp1 + at
    at2 = temp2 + at

    classes1 = at1 + class_files
    classes2 = at2 + class_files

    folderExists(temp1, True)
    folderExists(temp2, True)

    extract(args.apk1, temp1)
    extract(args.apk2, temp2)

    apktoolit(args.apk1, at1)
    apktoolit(args.apk2, at2)

    folderExists(classes1, True)
    folderExists(classes2, True)

    extractJar(temp1 + "classes.dex", classes1)
    extractJar(temp2 + "classes.dex", classes2)

    try:
        compare(at1,at2)
    except UnicodeError as e:
        print('UnicodeError',e)

    finally:
        f.close()
        fd.close()

def print_apk_size(apk1,apk2):
    print("*******************************************")
    f.write("*******************************************\n\n")
    apk1_size = os.path.getsize(apk1)/1024/1024
    apk2_size = os.path.getsize(apk2)/1024/1024
    print("\t%s\t%.2fMB"%(apk1,apk1_size))
    f.write("\t%s\t%.2fMB\n\n"%(apk1,apk1_size))
    print("\t%s\t%.2fMB"%(apk2,apk2_size))
    f.write("\t%s\t%.2fMB\n\n"%(apk2,apk2_size))
    if apk1_size > apk2_size:
        print('\t%s比%s减少了%.3fMB\n\n'%(apk2,apk1,apk1_size-apk2_size))
        f.write('\t%s比%s减少了%.3fMB\n\n'%(apk2,apk1,apk1_size-apk2_size))
    elif apk1_size < apk2_size:
        print('\t%s比%s增加了%.3fMB\n\n' % (apk2, apk1,apk2_size - apk1_size))
        f.write('\t%s比%s增加了%.3fMB\n\n' % (apk2, apk1,apk2_size - apk1_size))
    else:
        print('\t大小没有变化')
        f.write('\t大小没有变化\n\n')
    print("*******************************************")
    f.write("*******************************************\n\n")

def folderExists(path, clean=False):
    if clean and os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def extractJar(file,out):
    print("Dex2Jar'" + format(file, bcolors.OKBLUE) + "'")
    call(["cd",os.getcwd()],shell=True)
    call(["d2j-dex2jar.bat","-f", "-o", out, file],shell=True)

def exists(file):
    if not os.path.isfile(file):
        print(format("'{}' does not exist.".format(file), bcolors.FAIL))
        exit(0)

def extract(apk, dir):
    zipfi = zipfile.ZipFile(apk, 'r')
    zipfi.extract("classes.dex", dir)
    zipfi.close()
    print("Extracted '" + format("classes.dex", bcolors.OKBLUE) + "' from '" + format(apk, bcolors.OKBLUE) + "'.")

def apktoolit(file, dir):
    print("Running apktool against '" + format(file, bcolors.OKBLUE) + "'")
    call(["cd", os.getcwd()], shell=True)
    call(["apktool", "d", "-o", dir, file], stdout=open(os.devnull, 'w'), stderr=STDOUT,shell=True)
    print("[" + format("OK", bcolors.OKGREEN) + "]")

def compare(dir1,dir2):
    dcmp = dircmp(dir1,dir2)
    report_full_closure(dcmp,dir1,dir2)

def report_full_closure(dcmp,dir1,dir2):
    print_package_changes(dcmp,dir1,dir2)
    f.write('\n*****************************************删除的文件******************************************\n\n')
    print_left_only_files(dcmp)
    f.write("\n******************************************增加的文件******************************************\n\n")
    print_right_only_files(dcmp)
    f.write("\n******************************************不同的文件******************************************\n\n")
    print_diff_files(dcmp)
    diff_different_files(dcmp)

def print_package_changes(dcmp,dir1,dir2):
    print("*******************************************")
    f.write("*******************************************\n\n")
    shutil.rmtree(os.path.normpath(dir1+os.sep+"smali"))
    shutil.rmtree(os.path.normpath(dir2 + os.sep + "smali"))
    print(dcmp.common)
    for name in dcmp.common:
            path1 = os.path.normpath(dir1+os.sep+name)
            path2 = os.path.normpath(dir2+os.sep+name)
            diff_size = GetPathSize(path2) - GetPathSize(path1)
            if diff_size >= 0 :
                print("\t%-20s\t+%.3fMB"%(name,diff_size/1024/1024))
                f.write("\t%-20s\t+%.3fMB\n\n"%(name,diff_size/1024/1024))
            else:
                print("\t%-20s\t%.3fMB" % (name, diff_size/1024/1024))
                f.write("\t%-20s\t%.3fMB\n\n" % (name, diff_size/1024/1024))
    print("*******************************************")
    f.write("*******************************************\n\n")

def print_diff_files(dcmp):
    for name in dcmp.diff_files:
        path1 = os.path.normpath(dcmp.left + os.sep + name)
        path2 = os.path.normpath(dcmp.right + os.sep + name)
        diff_size = (os.path.getsize(path2) - os.path.getsize(path1))/1024
        if diff_size >=0:
            f.write("%-60s%-60s%-60s+%.3fKB\n" % (os.path.normpath(name), os.path.normpath(dcmp.left), os.path.normpath(dcmp.right),diff_size))
            print("%-60s%-60s%-60s+%.3fKB\n" % (os.path.normpath(name), os.path.normpath(dcmp.left), os.path.normpath(dcmp.right),diff_size))
        else:
            f.write("%-60s%-60s%-60s%.3fKB\n" % (
            os.path.normpath(name), os.path.normpath(dcmp.left), os.path.normpath(dcmp.right), diff_size))
            print("%-60s%-60s%-60s%.3fKB\n" % (
            os.path.normpath(name), os.path.normpath(dcmp.left), os.path.normpath(dcmp.right), diff_size))
    for sub_dcmp in dcmp.subdirs.values():
        print_diff_files(sub_dcmp)

def diff_different_files(dcmp):
         for name in dcmp.diff_files:
             if not re.match(ignore, name):
                 if not re.match('AndroidManifest.xml',name):
                     print("****************%s%s%s*************" % (
                     os.path.normpath(dcmp.left), os.sep, os.path.normpath(name)))
                     fd.write("***************%s%s%s*************\n\n" % (
                     os.path.normpath(dcmp.left), os.sep, os.path.normpath(name)))
                     content1 = reader(os.path.normpath(dcmp.left) + os.sep + os.path.normpath(name)).splitlines(1)
                     content2 = reader(os.path.normpath(dcmp.right) + os.sep + os.path.normpath(name)).splitlines(1)
                     diff = unified_diff(content1, content2)
                     tidy(list(diff))
                     print("*****************End**************\n\n")
                     fd.write("\n****************End*************\n\n")
         for sub_dcmp in dcmp.subdirs.values():
            diff_different_files(sub_dcmp)

def print_left_only_files(dcmp):
    for name in dcmp.left_only:
        f.write("---  %.2fKB\t\'%s%s%s\'      \n" % (os.path.getsize(dcmp.left+"/"+name)/1024,os.path.normpath(dcmp.left),os.sep,os.path.normpath(name),))
        print(format("---  %.2fKB\t\'%s%s%s\'      \n" % (os.path.getsize(dcmp.left+"/"+name)/1024,os.path.normpath(dcmp.left),os.sep,os.path.normpath(name)),bcolors.FAIL))
    for sub_dcmp in dcmp.subdirs.values():
       print_left_only_files(sub_dcmp)

def print_right_only_files(dcmp):
    for name in dcmp.right_only:
        f.write("+++  %.2fKB\t\'%s%s%s\'      \n" % (
        os.path.getsize(dcmp.right + "/" + name) / 1024, os.path.normpath(dcmp.right), os.sep, os.path.normpath(name),))
        print(format("+++  %.2fKB\t\'%s%s%s\'      \n" % (
        os.path.getsize(dcmp.right + "/" + name) / 1024, os.path.normpath(dcmp.right), os.sep, os.path.normpath(name)),
                     bcolors.OKGREEN))
    for sub_dcmp in dcmp.subdirs.values():
       print_right_only_files(sub_dcmp)


def GetPathSize(strPath):
    if not os.path.exists(strPath):
        return 0

    if os.path.isfile(strPath):
        return os.path.getsize(strPath)

    nTotalSize = 0
    for strRoot, lsDir, lsFiles in os.walk(strPath):
        # get child directory size
        for strDir in lsDir:
            nTotalSize = nTotalSize + GetPathSize(os.path.join(strRoot, strDir))

            # for child file size
        for strFile in lsFiles:
            nTotalSize = nTotalSize + os.path.getsize(os.path.join(strRoot, strFile))

    return nTotalSize

def tidy(lines):
    result = ""
    for line in lines:
        result = result + line
    fd.write(result)
    sorted = ""
    for line in lines:
        if line[:1] == "+":
            line = format(line, bcolors.OKGREEN)
        elif line[:1] == "-":
            line = format(line, bcolors.FAIL)
        sorted += line
    print(sorted)


def format(string, col):
    return col + string + '\033[0m'

def reader(file):
    tmpfile = open(file, 'r',encoding="utf8")
    tempdata = tmpfile.read()
    data = tempdata.encode('utf-8','ignore').decode('utf-8','ignore')
    tmpfile.close()
    return data

if __name__ == '__main__':
    main()