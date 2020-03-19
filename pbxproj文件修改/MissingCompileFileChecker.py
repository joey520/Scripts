"""
指定两个target，检查target编译文件直接的差异，避免因为category等没有添加导致运行时崩溃
通常用于开发target和发布target。
使用方式: python MissingCompileFileChecker xxx.pbxproj debugtagetName releaseTargetName
"""

#coding=utf-8
import os
import sys
from pbxproj import XcodeProject
from pbxproj import PBXGenericObject
import uuid

kDebugTarget = "SDK QA"
kReleaseTarget = "Release Version SDK"

def fetchTarget(project, target_name):
    targets = project.objects.get_targets(target_name)
    if len(targets) == 0:
        print("❌ not found target: " + target_name)
        return None
    else:
         target = targets[0]
         return target

def fetchFileRefUUIDSFromBuildFiles(project, buildFileUUIDs):
    fileRefs = []
    if len(buildFileUUIDs) <= 0:
        return
    for uuid in buildFileUUIDs:
        # 先获取buildfile
        buildFile = project.objects[uuid]
        # 找到fileRef
        fileRef = buildFile["fileRef"]
        fileRefs.append(fileRef)
    return fileRefs

# 获取target的buildFiles
def fetchTargetBuildFileUUIDs(project, target_name):
    target = fetchTarget(project, target_name)
    buildFileUUIDS = []
    if target_name is not None:
        buildPhases = target.buildPhases
        # print(buildPhases)
        # 第一个phase就是compile sources
        buildSoucesId = buildPhases[0]
        # 获取build source对象,
        buildSources = project.get_object(buildSoucesId)
        # 取出所有文件的uuid
        buildFileUUIDS = buildSources["files"]
    return buildFileUUIDS

def fethFileNamesForBuildUUIDs(project, buildFileUUIDs):
    buildFileRefs = fetchFileRefUUIDSFromBuildFiles(project, buildFileUUIDs)
    fileNames = []
    for buildFileRef in buildFileRefs:
        fileRef = project.get_object(buildFileRef)
        fileName = fileRef["path"]
        fileNames.append(fileName)
    return fileNames

def addTargetMembership(project, target_name, buildFileUUID, file_ref):
    # buildfile, 内容是一样的
    # 所以说白了就是再加一个uuid
    buildFile = project.get_object(buildFileUUID)
    kuuid = ''.join(str(uuid.uuid1()).upper().split('-')[1:])
    project._create_build_files(file_ref, target_name, u'PBXSourcesBuildPhase', FileOptions())
        # print("✅")
        # print(buildFileUUID._get_comment())
        # print(buildFile)
        # # 新增一个buildFile
        # project.objects[kuuid] = buildFile
        # # print("add one fileRef: " + buildFile)
        # # 还需要添加到target下
        # releaseBuildFiles = fetchTargetBuildFileUUIDs(project, kReleaseTarget)
        # fileName = fethFileNamesForBuildUUIDs(project, [buildFileUUID])[0]
        # comment = u' /* {0} */,'.format(buildFileUUID._get_comment())
        # oneline = kuuid + " /*" + fileName + " in Sources */,"
        # ret = kuuid + comment
        

        
        # releaseBuildFiles.append(buildFileUUID)

# pre action并不会打印出log, 一种方式是注入error, 另一种方式是终止编译
def logForMissingFiles(project, missingFileRefs):
    if len(missingFileRefs) <= 0:
        return
    notice = "❌❌ 有以下文件在release版本的target membership:\n"
    for fileRefUUID in missingFileRefs:
        fileRef = project.get_object(fileRefUUID)
        fileName = fileRef["path"]
        notice = notice + str(fileName) + "\n"
    print(notice)
    # 注入到一个文件中

def start(pbxfile = None):
    project = XcodeProject.load(pbxfile)
    debugBuildFileUUIDs = fetchTargetBuildFileUUIDs(project, kDebugTarget)
    releaseBuildFileUUIDs = fetchTargetBuildFileUUIDs(project, kReleaseTarget)

    debugBuildFilesRefUUIDs = fetchFileRefUUIDSFromBuildFiles(project, debugBuildFileUUIDs)
    releaseBuildFilesRefUUIDs = fetchFileRefUUIDSFromBuildFiles(project, releaseBuildFileUUIDs)
    difference = set(debugBuildFilesRefUUIDs).difference(set(releaseBuildFilesRefUUIDs))

    for uuid in difference:
        fileRefUUIDs = fetchFileRefUUIDSFromBuildFiles(project, [buildFileUUID])

    if len(difference):
        logForMissingFiles(project, difference)
        raise Exception, "❌❌ 请检查并补全上述缺失的文件（一般为Category忘记勾选）"
        # 看有没有必要自动添加了，安全起见还是报错手动添加
        # for buildFileUUID in debugBuildFileUUIDs:
        #     fileRefUUIDs = fetchFileRefUUIDSFromBuildFiles(project, [buildFileUUID])
        #     if len(fileRefUUIDs) <= 0:
        #         continue
        #     fileRefUUID = fileRefUUIDs[0]
        #     if fileRefUUID in difference:
        #         addTargetMembership(project, kReleaseTarget, buildFileUUID, fileRefUUID)
    project.save()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("❌ please input the path of xcodeproj file!")
        exit()
        
    start(sys.argv[1])