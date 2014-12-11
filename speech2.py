import sys,os

def decodeSpeech(hmmd,lmdir,dictp,wavfile):
    """
    Decodes a speech file
    """

    try:
        import pocketsphinx as ps
        import sphinxbase

    except:
        print """Pocket sphinx and sphixbase is not installed
        in your system. Please install it with package manager.
        """

    speechRec = ps.Decoder(hmm = hmmd, lm = lmdir, dict = dictp)
    wavFile = file(wavfile,'rb')
    wavFile.seek(44)
    speechRec.decode_raw(wavFile)
    result = speechRec.get_hyp()
    return result

if __name__ == "__main__":
    hmdir = "/usr/share/pocketsphinx/model/hmm/wsj1"
    lmd = "/usr/share/pocketsphinx/model/lm/wsj/wlist5o.3e-7.vp.tg.lm.DMP"
    dictd = "/usr/share/pocketsphinx/model/lm/wsj/wlist5o.dic"
    wavfile = sys.argv[1]
    recognised = decodeSpeech(hmdir,lmd,dictd,wavfile)
    #print recognised
    for word in recognised:
        print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"
        print word.__str__() + " "
        print "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"

# http://cmusphinx.sourceforge.net/wiki/gstreamer
