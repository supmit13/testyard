import os, sys, re, time
from PIL import Image
# May incorporate pooling later on once we have a working version of the code - Supriyo.


def iter_frames(im):
    try:
        i= 0
        while 1:
            im.seek(i)
            imframe = im.copy()
            if i == 0: 
                palette = imframe.getpalette()
            else:
                imframe.putpalette(palette)
            yield imframe
            i += 1
    except EOFError:
        pass


def convert_to_png(srcdir):
    userdirslist = os.listdir(srcdir) # "/var/www/html/face-api.js/examples/public/images"
    for entrydir in userdirslist:
        entrydir = srcdir+ os.path.sep + entrydir
        if os.path.isdir(entrydir):
            fileslist = os.listdir(entrydir)
            for fileentry in fileslist:
                fileentry = entrydir+ os.path.sep + fileentry
                im = Image.open(fileentry)
                fileparts = fileentry.split(".")
                if fileparts.__len__() > 2 and fileparts[2] == "png":
                    continue
                elif fileparts.__len__() > 2 and (fileparts[2] == "jpg" or fileparts[2] == "jpeg"):
                    im.save(fileparts[0] +"." + fileparts[1] + '.png')
                elif fileparts.__len__() > 2 and  fileparts[2] == "gif":
                    for i, frame in enumerate(iter_frames(im)):
                        print "HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH ", fileparts[0], " SSSSSSSSSSSSSS ", frame.info
                        orig_filename = fileparts[0] + "." + fileparts[1]
                        frame.save('%s.png' % orig_filename,**frame.info)
                else:
                    print "Unsupported format."


# Test the above code.
if __name__ == "__main__":
    convert_to_png("/var/www/html/face-api.js/examples/public/images")




