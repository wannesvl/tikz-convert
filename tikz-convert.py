#!/usr/bin/python

# tikz-convert -- A helper script to convert tikz drawings to pdf, png or eps
# Copyright (C) 2013 Wannes Van Loock. All rights reserved.
#
# tikz-convert is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
# CasADi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import  optparse, os, subprocess, sys, tempfile, re

def stripComments(text):
    return re.sub('%.*','', text)

def getPreamble(fileName):
    beginDoc = "\\begin{document}"
    texLines_new = []
    with open(fileName) as texFile:
        texLines = texFile.readlines()
    for i, line in enumerate(texLines):
        f = stripComments(texLines[i]).strip()
        if (f!='' and f!='\n'):
            texLines_new.append(f)
        if beginDoc in line:
            return '\n'.join(texLines_new[:-1])
    sys.stderr.write("converTikz -> getPreamble: Incorrect template-file. \n"
                     "Script will exit now")

def convertTikz(pathToFile, outputformat="pdf", once="true", density=300,
                root=None):
    sys.stdout.write("\nconvertTikz: Processing file %s \n \n" % pathToFile)
    pathName, tikzName = os.path.split(pathToFile)
    baseName = tikzName.split(".")[0]
    tikzName = baseName + "_tikz"
    texName = tikzName + ".tex"
    pdfName = tikzName
    tempFiles = [tikzName + '.' + ext for ext in ['tex', 'aux', 'bcf', 'fls', 'idx', 'ind', 'lof', 'lot',  'out', 'toc', 'fdb_latexmk', 'run.xml', 'log', 'pyg']]
    # Create a template    
    with open(pathToFile) as tikzFile:
        mainDoc = tikzFile.readline()
    if root:
        template = getPreamble(root)
    elif mainDoc.replace(" ", "").rfind('%root=') != -1:
        template = getPreamble(mainDoc.split("=")[1].strip())
    else:
        template = r"\documentclass{article}"
    template = '\n'.join([template,
                    '\\usepackage{tikz,pgfplots,amsmath,amssymb,siunitx}',
                    '\\usetikzlibrary{arrows,decorations,backgrounds,patterns,matrix,shapes,fit,calc,shadows,plotmarks,intersections,positioning,through,pgfplots.groupplots,3d}',
                    '\\pgfplotsset{compat=newest}',
                    '\\usepackage[graphics, tightpage, active]{preview}',
		    '\\usepackage{tikz-3dplot}',
                    '\\PreviewEnvironment{tikzpicture}', 
                    '\\begin{document}', r'\input{%s}', 
                    '\\end{document}'])
    
    # Write tex file
    texInputFile = "\"" + pathToFile + "\""
    with open(texName,"w") as texfile:
        texfile.write(template % texInputFile.replace("\\","/"))  
    out = tempfile.TemporaryFile()
    # Compile tex file
    if once:
        sys.stdout.write("convertTikz: Converting tikz to pdf\n")
        try:
            ec = subprocess.call(["lualatex", "-halt-on-error",
                "-shell-escape", "-jobname=%s" %pdfName ,texName],
                                  stdout = out)
        except:
            ec = subprocess.call(["pdflatex", "-halt-on-error",
                                  "-jobname=%s" %pdfName ,texName],
                                  stdout = out)
        # Check for compilation errors
        if ec:
            out.seek(0)
            sys.stdout.write(out.read())
            sys.stderr.write("convertTikz: ERROR generating pdf file\n")
        else:
            sys.stdout.write("convertTikz: Successfully generated pdf\n")
    else:
        sys.stdout.write("convertTikz: WARNING continuous compilation requires"
                         " latexmk to be on your PATH\n")
        try:
            ec = subprocess.call(["latexmk", "-pdf", "-pvc",
                                  tikzName], stdout = None)
        except KeyboardInterrupt:
            pass
    
    # Convert to other formats
    if "eps" in outputformat:
        sys.stdout.write("convertTikz: Converting pdf to eps\n")
        sys.stdout.write("convertTikz: WARNING conversion to eps requires"
                         " \"pdftops\"\n")
        toeps = subprocess.call("pdftops -eps %s.pdf" %pdfName,shell=True)
        if toeps:
            sys.stdout.write("convertTikz: ERROR generating eps file\n")
        else:
            with open(tikzName + ".eps") as epsFile:
                epsLines = epsFile.readlines()
            # Some versions of pdftops add something weird to the second line so
            # we remove this line
            if "Produced by" in epsLines[1]:
                del epsLines[1]
            with open(tikzName + ".eps","w") as epsFile:
                epsFile.writelines(epsLines)
            sys.stdout.write("convertTikz: Successfully generated eps file \n")        
    if "png" in outputformat:
        sys.stdout.write("convertTikz: Converting pdf to png\n")
        sys.stdout.write("convertTikz: WARNING conversion requires convert"
                         "requires \"convert\"\n")
        topng = subprocess.call(
            "convert -alpha on -channel rgba -fuzz 5%% -transparent white -density %d %s.pdf PNG32:%s.png" %(density,pdfName,tikzName),
            shell=True)
        if topng:
            sys.stdout.write("convertTikz: ERROR generating png file\n")

    # Remove temp files
    sys.stdout.write("convertTikz: Deleting temporary files\n")
    for tf in tempFiles:
        if os.path.isfile(tf):
            os.remove(tf)
    
    sys.stdout.write("convertTikz: Done!\n")


if __name__ == "__main__":
    usage = ("usage: %prog [options] arg. If arg is a foldername," 
            "the entire folder is scanned for *.tikz files and all are"
            "converted to pdf")
    op = optparse.OptionParser(usage=usage)
    op.add_option("-o", "--once", action = "store_true",
                  dest = "once", default = False,
                  help = "only convert once, then clean up temporary files "
                         "and quit")
    op.add_option("-e","--eps", action="store_true",
                  dest = "eps",default=False,
                  help = "Compile image to postscript format. pdftops must be "
                         "installed on your system in order to use this option!")
    op.add_option("-p","--png", action="store_true",
                  dest = "png",default=False,
                  help = "Creates an image of PNG dpi in png format for use on "
                         "e.g. websites. \"Convert\" must be available on your "
                         "system in order to use this option!")
    op.add_option("-d","--density",
                  dest = "density",type="int",default = 300,
                  help = "The resolution in dpi of the resulting png")
    op.add_option("-r","--root", dest = "root", default = None,
                  help = "The location of the main tex file")

    options, args = op.parse_args()
    args = args[0].replace("/",os.sep)
    
    if options.eps and options.png:
        outputformat = ("pdf","eps","png")
    elif options.eps:
        outputformat = ("pdf","eps")
    elif options.png:
        outputformat = ("pdf","png")
    else:
        outputformat = ("pdf")

    if os.path.isfile(args):
        # Change argument to absolute path for compileTikz function
        convertTikz(os.path.join(os.getcwd(),args), outputformat, options.once,
                    options.density)
    elif os.path.isdir(args):
        for dirs, names, filenames in os.walk(args):
            for fi in filenames:
                if fi.endswith(".tikz"):
                    # Give absolute path to compileTikz
                    convertTikz(os.path.join(os.getcwd(),dirs,fi), outputformat,
                                True, options.density)
