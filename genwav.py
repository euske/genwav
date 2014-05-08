#!/usr/bin/env python
#
# Generates a tone wave.
#
# usage:
#   $ python genwav.py {-N|-T|-Q} out.wav [tone ...]
#

import sys
import wave
import struct
import array
from math import sin, cos, pi


##  WaveWriter
##
class WaveWriter(object):

    def __init__(self, fp, 
                 nchannels=1, sampwidth=2,
                 framerate=44100, nframes=None):
        self.fp = fp
        self.nchannels = nchannels
        self.sampwidth = sampwidth
        self.framerate = framerate
        self.nframes = nframes
        self._nframeswritten = 0
        if self.sampwidth == 1:
            self.ratio = 255.0
            self.arraytype = 'b'
        else:
            self.ratio = 32767.0
            self.arraytype = 'h'
        if nframes is None:
            self._write_header(0, 0, 0, 0)
        else:
            self._write_header(nchannels, sampwidth, framerate, nframes)
        return

    def __len__(self):
        return self.nframes

    def _write_header(self, nchannels, sampwidth, framerate, nframes):
        datalen = nchannels * sampwidth * nframes
        self.fp.write('RIFF')
        self.fp.write(struct.pack('<l4s4slhhllhh4sl',
                                  36+datalen, 'WAVE', 'fmt ', 16,
                                  0x0001, nchannels, framerate,
                                  nchannels*sampwidth*framerate,
                                  nchannels*sampwidth,
                                  sampwidth*8, 'data', datalen))
        return

    def close(self):
        if self.nframes is None:
            self.fp.seek(0)
            self._write_header(self.nchannels, self.sampwidth,
                               self.framerate, self._nframeswritten)
        return

    def eof(self):
        return (self.nframes is not None and self.nframes <= self._nframeswritten)
    
    def tell(self):
        return self._nframeswritten

    def writeraw(self, bytes):
        self.fp.write(bytes)
        self._nframeswritten += (len(bytes)/self.sampwidth)
        return
    
    def write(self, frames):
        assert self.nchannels == 1
        a = [ int(x*self.ratio) for x in frames ]
        a = array.array(self.arraytype, a)
        self.writeraw(a.tostring())
        return


##  WaveGenerator
##
class WaveGenerator(object):

    TONE2FREQ = {
        'A0': 28,
        '^A0': 29,
        'B0': 31,
        'C1': 33,
        '^C1': 35,
        'D1': 37,
        '^D1': 39,
        'E1': 41,
        'F1': 44,
        '^F1': 46,
        'G1': 49,
        '^G1': 52,
        'A1': 55,
        '^A1': 58,
        'B1': 62,
        'C2': 65,
        '^C2': 69,
        'D2': 73,
        '^D2': 78,
        'E2': 82,
        'F2': 87,
        '^F2': 93,
        'G2': 98,
        '^G2': 104,
        'A2': 110,
        '^A2': 117,
        'B2': 123,
        'C3': 131,
        '^C3': 139,
        'D3': 147,
        '^D3': 156,
        'E3': 165,
        'F3': 175,
        '^F3': 185,
        'G3': 196,
        '^G3': 208,
        'A3': 220,
        '^A3': 233,
        'B3': 247,
        'C4': 262,
        '^C4': 277,
        'D4': 294,
        '^D4': 311,
        'E4': 330,
        'F4': 349,
        '^F4': 370,
        'G4': 392,
        '^G4': 415,
        'A4': 440,
        '^A4': 466,
        'B4': 494,
        'C5': 523,
        '^C5': 554,
        'D5': 587,
        '^D5': 622,
        'E5': 659,
        'F5': 698,
        '^F5': 740,
        'G5': 784,
        '^G5': 831,
        'A5': 880,
        '^A5': 932,
        'B5': 988,
        'C6': 1047,
        '^C6': 1109,
        'D6': 1175,
        '^D6': 1245,
        'E6': 1319,
        'F6': 1397,
        '^F6': 1480,
        'G6': 1568,
        '^G6': 1661,
        'A6': 1760,
        '^A6': 1865,
        'B6': 1976,
        'C7': 2093,
        '^C7': 2217,
        'D7': 2349,
        '^D7': 2489,
        'E7': 2637,
        'F7': 2794,
        '^F7': 2960,
        'G7': 3136,
        '^G7': 3322,
        'A7': 3520,
        '^A7': 3729,
        'B7': 3951,
        'C8': 4186,
    }

    def __init__(self, framerate):
        self.framerate = framerate
        return

    def add(self, *iters):
        while iters:
            x = 0.0
            r = []
            for it in iters:
                try:
                    x += it.next()
                except StopIteration:
                    r.append(it)
            yield x
            for it in r:
                iters.remove(it)
        return

    def mult(self, *iters):
        while iters:
            x = 1.0
            r = []
            for it in iters:
                try:
                    x *= it.next()
                except StopIteration:
                    r.append(it)
            yield x
            for it in r:
                iters.remove(it)
        return

    def concat(self, *iters):
        for it in iters:
            for x in it:
                yield x
        return

    def avg(self, *iters):
        r = 1.0/len(iters)
        return self.amp(r, self.add(*iters))

    def amp(self, volume, it):
        for x in it:
            yield volume*x
        return

    def cut(self, duration, it):
        n = int(self.framerate * duration)
        for i in xrange(n):
            try:
                yield it.next()
            except StopIteration:
                break
        return

    def attack(self, attack, decay, it):
        na = int(self.framerate * attack)
        ra = 1.0/float(na)
        for i in xrange(na):
            try:
                yield i*ra*it.next()
            except StopIteration:
                return
        nd = int(self.framerate * decay)
        rd = 1.0/float(nd)
        for i in xrange(nd):
            try:
                yield (1.0-i*rd)*it.next()
            except StopIteration:
                return
        yield 0.0
        return

    def sine(self, freq):
        freq = self.TONE2FREQ.get(freq, freq)
        fr = 2*pi*freq/self.framerate
        i = 0
        while 1:
            yield sin(i*fr)
            i += 1
        return

    def square(self, freq):
        freq = self.TONE2FREQ.get(freq, freq)
        w = int(self.framerate/freq/2)
        while 1:
            for i in xrange(w):
                yield +1
            for i in xrange(w):
                yield -1
        return

    def triangle(self, freq):
        freq = self.TONE2FREQ.get(freq, freq)
        w = int(self.framerate/freq)
        r = 2.0/float(w)
        while 1:
            for i in xrange(w):
                yield i*r-1.0
        return

# gen_sine_tone
def gen_sine_tone(path, tones, volume=0.5, attack=0.01, decay=0.7):
    print 'gen_sine_tone', path, tones
    fp = open(path, 'wb')
    stream = WaveWriter(fp)
    gen = WaveGenerator(stream.framerate)
    wav = gen.avg(*[ gen.sine(k) for k in tones ])
    wav = gen.amp(volume, wav)
    wav = gen.attack(attack, decay, wav)
    stream.write(wav)
    stream.close()
    fp.close()
    return

# gen_square_tone
def gen_square_tone(path, tones, volume=0.5, attack=0.01, decay=0.7):
    print 'gen_square_tone', path, tones
    fp = open(path, 'wb')
    stream = WaveWriter(fp)
    gen = WaveGenerator(stream.framerate)
    wav = gen.avg(*[ gen.square(k) for k in tones ])
    wav = gen.amp(volume, wav)
    wav = gen.attack(attack, decay, wav)
    stream.write(wav)
    stream.close()
    fp.close()
    return

# gen_triangle_tone
def gen_triangle_tone(path, tones, volume=0.5, attack=0.01, decay=0.7):
    print 'gen_triangle_tone', path, tones
    fp = open(path, 'wb')
    stream = WaveWriter(fp)
    gen = WaveGenerator(stream.framerate)
    wav = gen.avg(*[ gen.triangle(k) for k in tones ])
    wav = gen.amp(volume, wav)
    wav = gen.attack(attack, decay, wav)
    stream.write(wav)
    stream.close()
    fp.close()
    return

# main
def main(argv):
    import getopt
    def usage():
        print 'usage: %s {-N|-Q|-T} out.wav [tone ...]' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'NQT')
    except getopt.GetoptError:
        return usage()
    func = gen_sine_tone
    for (k, v) in opts:
        if k == '-N': func = gen_sine_tone
        elif k == '-Q': func = gen_square_tone
        elif k == '-T': func = gen_triangle_tone
    path = args.pop(0)
    func(path, args)
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
