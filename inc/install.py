import os
import logging
import shutil
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
from ebbs import Builder
from ebbs import OtherBuildError

class install(Builder):
    def __init__(self, name="Install a package"):
        super().__init__(name)

        #Support all project types here, since we don't use the local system
        #This bypasses type checking.
        self.supportedProjectTypes = []

        self.requiredKWArgs.append("repo")

        self.installSrcPath = "./"
        self.installIncPath = "./"
        self.installBinPath = "./"

    #Optional Builder method. See that class for details.
    def PreBuild(self, **kwargs):
        self.repo = kwargs.get("repo")
        if (not len(self.repo)):
            raise OtherBuildError('Repo credentials required to know where saved packages end up!')

        if (self.os in ['Linux']):
            self.installSrcPath = "/usr/local/lib"
            self.installIncPath = "/usr/local/include/"
            self.installBinPath = "/usr/local/bin"
        #TODO: support windows & mac

        #rewrite builder code for our own uses.
        self.package = '_'.join([self.buildPath, self.architecture])
        details = self.buildPath.split("_")
        self.projectType = details[0]
        if (len(details) > 1):
            self.projectName = '_'.join(details[1:])

    #Required Builder method. See that class for details.
    def Build(self):
        packagePath = self.repo['store']
        if (os.path.exists(packagePath)):
            logging.info(f'DELETING {packagePath}')
            shutil.rmtree(packagePath)
        mkpath(packagePath)

        self.executor.DownloadPackage(self.package, registerClasses=False)
        if (not os.path.isdir(packagePath)):
            raise OtherBuildError('Couldn\'t find downloaded package')
        os.chdir(packagePath)
        zipFile = f'{self.package}.zip'
        logging.debug(f'Removing {zipFile}')
        if (os.path.isfile(zipFile)):
            os.remove(zipFile)

        if (self.projectType in ['lib']):
            for thing in os.listdir('.'):
                thingPath = os.path.abspath(thing)
                if os.path.isfile(thingPath):
                    logging.debug(f'Copying {thingPath} to {self.installSrcPath}')
                    copy_file(thingPath, self.installSrcPath)
                elif os.path.isdir(thingPath):
                    destPath = os.path.join(self.installIncPath, thing)
                    logging.debug(f'Copying {thingPath} to {destPath}')
                    mkpath(destPath)
                    copy_tree(thingPath, destPath)

        if (self.projectType in ['bin']):
            for thing in os.listdir('.'):
                thingPath = os.path.abspath(thing)
                if os.path.isfile(thingPath):
                    logging.debug(f'Copying {thingPath} to {self.installBinPath}')
                    copy_file(thingPath, self.installBinPath)
                #ignore folders.