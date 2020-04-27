#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import argparse
import glob
import ntpath
import shutil


class Main(object):


    def __init__(self):

        self.settings = {
            'prefix'      : '/org/gnome/shell/theme',
            'gres-source' : '/usr/share/gnome-shell/theme/Yaru/gnome-shell-theme.gresource'
        }

        self.controller()


    def controller(self):

        # Prepare the custom arguments

        argparseHandler = argparse.ArgumentParser(
            add_help=False
        )

        argparseHandler.add_argument(
            '-h', '--help',
            dest='help', action='store_true'
        )

        argparseHandler.add_argument(
            '--init',
            dest='init', nargs='?'
        )

        argparseHandler.add_argument(
            '--compile',
            dest='compile', nargs='?'
        )

        argparseHandler.add_argument(
            '--install',
            dest='install', nargs='?'
        )

        argparseHandler.add_argument(
            '--uninstall',
            dest='uninstall', nargs='?'
        )

        arguments = argparseHandler.parse_known_args(sys.argv[1:])[0]

        # Call the specific service layer

        if(arguments.init):
            self.initProject(arguments.init)

        elif(arguments.compile):
            self.compileProject(arguments.compile)

        elif(arguments.install):
            self.installGresource(arguments.install)

        elif(arguments.uninstall):
            self.uninstallGresource(arguments.uninstall)

        else:
            self.printHelp()


    def printHelp(self):

        print('\n'.join([
            'Gnome Shell 3 Helper - v1.0.1-stable',
            'Use: python3 helper.py [option] [arguments]',
            'Options:',
            '  -h, --help                Print the help message.',
            '      --init [folder]       Initialize project in the specific folder.',
            '      --compile [folder]    Compile project from specific folder.',
            '      --install [gresource] Install specific gresource file.',
            '      --uninstall [alternative path]',
            '                            Uninstall specific alternative gresource path.',
            '                            For show all alternatives ejecute this command:',
            '                            update-alternatives --query gdm3-theme.gresource'
        ]))


    def initProject(self, projectFolder):

        # Normalize
        projectFolder = os.path.realpath(projectFolder)

        # Source template exist?
        if(not os.path.isfile(self.settings['gres-source'])):
            print('! The source template does not exist or is not accessible:')
            print('  ' + self.settings['gres-source'])
            return

        # Verify command to compile
        result = subprocess.run(
            ['which', 'gresource'],
            stdout=subprocess.PIPE
        )
        if(result.returncode == 1):
            print('! The "gresource" command is not found.')
            return

        # Read compiled source
        print('+ Reading gresource compiled content ...')        
        result = subprocess.run(
            ['gresource', 'list', self.settings['gres-source']],
            stdout=subprocess.PIPE
        )
        resources = result.stdout.splitlines()
        del result

        # Verify the folder project
        if(not os.path.isdir(projectFolder)):
            os.mkdir(projectFolder)

        # Extract all resources
        for resourcePath in resources:

            paths = {
                'resource' : resourcePath,
                'relative' : resourcePath[len(self.settings['prefix']):].strip(b'/'),
                'local'    : (
                    projectFolder.encode('utf-8', errors='ignore') +
                    resourcePath[len(self.settings['prefix']):]
                )
            }

            print(
                '  -> Extracting ' +
                paths['relative'].decode('utf-8', errors='ignore') +
                ' ...'
            )

            result = subprocess.run(
                ['gresource', 'extract', self.settings['gres-source'], resourcePath],
                stdout=subprocess.PIPE
            )
            
            # Create folder of file if not exists
            if(not os.path.isdir(os.path.dirname(paths['local']))):
                os.makedirs(os.path.dirname(paths['local']), exist_ok=True)

            # Save file content
            with open(paths['local'], 'wb') as fileHandler:
                fileHandler.write(result.stdout)

        print('+ Project created.')


    def compileProject(self, projectFolder):

        # Normalize
        projectFolder = os.path.realpath(projectFolder)

        # Verify the folder project
        if(not os.path.isdir(projectFolder)):
            print('! The folder of project is not found:')
            print('  ' + projectFolder)
            return

        # Verify command to compile
        result = subprocess.run(
            ['which', 'glib-compile-resources'],
            stdout=subprocess.PIPE
        )
        if(result.returncode == 1):
            print('! The "glib-compile-resources" command is not found.')
            print('  If use Debian or Ubuntu try install "libglib2.0-dev-bin".')
            return

        print('+ Creating resources XML ...')

        # XML data
        xml = {
            'path'    : (
                # Folder of XML file
                projectFolder + '/' +

                # Name of folder project
                ntpath.basename(projectFolder) +

                # Required as extension
                '.gresource.xml'
            ),
            'content' : None
        }
        
        # Initial XML content
        xml['content'] = '\n'.join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<gresources>',
            '    <gresource prefix="' + self.settings['prefix'] + '">',
            ''
        ])

        # Write each path into XML content
        for path in glob.iglob(projectFolder + '/**/*', recursive=True):
            
            # Ommit folders
            if(not os.path.isfile(path)):
                continue

            # Append the path to XML
            namespace = path[len(projectFolder) + 1:]
            xml['content'] += '        <file>' + namespace + '</file>\n'

        # Footer XML content
        xml['content'] += '\n'.join([
            '    </gresource>',
            '</gresources>'
        ])

        # Delete old XML content file
        if(os.path.isfile(xml['path'])):
            os.remove(xml['path'])

        # Save the XML content
        with open(xml['path'], 'w') as fileHandler:
            fileHandler.write(xml['content'])
        
        # Delete old gresource
        if(os.path.isfile(ntpath.basename(projectFolder) + '.gresource')):
            os.remove(ntpath.basename(projectFolder) + '.gresource')

        print('+ Compilling all resources ...')

        result = subprocess.run(
            [
                'glib-compile-resources',
                os.path.split(xml['path'])[1],
                '--target',
                '../' + ntpath.basename(projectFolder) + '.gresource'
            ],
            stdout=subprocess.PIPE,
            cwd=os.path.dirname(xml['path'])
        )
        
        if(not result.returncode == 0):
            print('! Unable compile the theme:')
            print(result.stdout.decode('utf-8', errors='ignore'))
            return

        print('+ Project compiled.')


    def installGresource(self, gresourceFile):

        paths = {
            'gresource'     : os.path.realpath(gresourceFile), # Normalize
            'filename'      : ntpath.basename(gresourceFile),
            'system-folder' : '/usr/local/share/gnome-shell/theme',
            'system-path'   : (
                '/usr/local/share/gnome-shell/theme/' +
                ntpath.basename(gresourceFile)
            )
        }

        if(not (
            (os.geteuid() == 0) or
            (os.getenv('SUDO_USER') is not None)
        )):
            print('! Root is required for this action.')
            return

        # Verify command to compile
        result = subprocess.run(
            ['which', 'update-alternatives'],
            stdout=subprocess.PIPE
        )
        if(result.returncode == 1):
            print('! The "update-alternatives" command is not found.')
            return

        # Verify gresource file
        if(not os.path.isfile(paths['gresource'])):
            print('! The gresource file is not found:')
            print('  ' + paths['gresource'])

        print('+ Installing compilled theme ...')
        
        # Final theme path
        if(not os.path.isdir(paths['system-folder'])):
            os.makedirs(paths['system-folder'], exist_ok=True)

        # Delete old gresource
        if(os.path.isfile(paths['system-path'])):
            os.remove(paths['system-path'])

        # Copy file to system directory
        print('  - Copying gresource file ...')
        shutil.copyfile(paths['gresource'], paths['system-path'])

        # Get installation status
        result = subprocess.run(
            ['update-alternatives', '--query', 'gdm3-theme.gresource'],
            stdout=subprocess.PIPE
        )

        # Is alternative installed?
        isInstalled = False
        for line in result.stdout.splitlines():
            if(line == b'Alternative: ' + paths['system-path'].encode('utf-8', errors='ignore')):
                isInstalled = True
                break

        if(not isInstalled):

            # Install the alternative
            print('  - Installing alternative ...')
            result = subprocess.run(
                [
                    'update-alternatives',
                    '--quiet',
                    '--install',
                    '/usr/share/gnome-shell/gdm3-theme.gresource', # Link
                    'gdm3-theme.gresource', # Name
                    paths['system-path'],   # Path
                    '0',                    # Priority
                ],
                stdout=subprocess.PIPE
            )

        # Apply alternative
        print('  - Applying alternative ...')
        result = subprocess.run(
            [
                'update-alternatives',
                '--quiet',
                '--set',
                'gdm3-theme.gresource', # Name
                paths['system-path']    # Path
            ],
            stdout=subprocess.PIPE
        )

        if(not result.returncode == 0):
            print('! Unable install alternative for theme.')
            print('! For more info execute this command:')
            print('  update-alternatives --set gdm3-theme.gresource ' + paths['system-path'])
            return

        print('+ Theme is installed!')


    def uninstallGresource(self, gresourceSystemFile):

        if(not (
            (os.geteuid() == 0) or
            (os.getenv('SUDO_USER') is not None)
        )):
            print('! Root is required for this action.')
            return

        # Verify command to compile
        result = subprocess.run(
            ['which', 'update-alternatives'],
            stdout=subprocess.PIPE
        )
        if(result.returncode == 1):
            print('! The "update-alternatives" command is not found.')
            return

        print('+ Uninstalling theme ...')

        # Get installation status
        result = subprocess.run(
            ['update-alternatives', '--query', 'gdm3-theme.gresource'],
            stdout=subprocess.PIPE
        )

        # Is alternative installed?
        isInstalled = False
        for line in result.stdout.splitlines():
            if(line == b'Alternative: ' + gresourceSystemFile.encode('utf-8', errors='ignore')):
                isInstalled = True
                break

        if(not isInstalled):
            print('! The theme is not installed as alternative:')
            print('  ' + gresourceSystemFile)
            print('! For more info execute this command:')
            print('  update-alternatives --query gdm3-theme.gresource')
            return

        # Uninstall alternative
        print('  - Uninstalling alternative ...')
        result = subprocess.run(
            [
                'update-alternatives',
                '--remove',
                'gdm3-theme.gresource',
                gresourceSystemFile
            ],
            stdout=subprocess.PIPE
        )

        if(not result.returncode == 0):
            print('! Unable uninstall the alternative.')
            print('! For more info execute this command:')
            print('  update-alternatives --remove gdm3-theme.gresource ' + gresourceSystemFile)
            return

        # Delete gresource file
        print('  - Deleting gresource file ...')
        if(os.path.isfile(gresourceSystemFile)):
            os.remove(gresourceSystemFile)

        print('+ Theme is uninstalled.')
        print('+ For more info execute this command:')
        print('  update-alternatives --query gdm3-theme.gresource')


if __name__ == '__main__':
    Main()