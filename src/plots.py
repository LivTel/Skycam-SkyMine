'''
name:		plots.py
author:		rmb

description: 	A plotting class
'''

import logging
import numpy as np

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg
import pylab
import random

from FITSFile import FITSFile

def plotCalibration(matchedSources, calibrationCoeffs, lowerColourLimit, upperColourLimit, logger, hard, outImageFilename, outDataFilename, numSubsamplePoints=40000):
    '''
    make calibration plot from a list of (USNOB matched) source instances
    '''
    magDifference = []
    BRcolour = []
    for i in matchedSources:
        BRcolour.append(i.USNOBCatB2MAG - i.USNOBCatR2MAG)
        magDifference.append(i.sExCatMagAuto - i.USNOBCatR2MAG)
    pylab.plot(BRcolour, magDifference, 'bx')

    # best fit
    c = calibrationCoeffs[0]
    m = calibrationCoeffs[1]
    x = np.arange(lowerColourLimit, upperColourLimit+0.1)
    y = (m*x) + c
    pylab.plot(x, y, '--r') 

    # plot parameters
    pylab.xlabel(r'$B \minus R$')
    pylab.ylabel(r'$R_{inst} \minus R_{cat}$')
    pylab.xlim(lowerColourLimit, upperColourLimit)

    if hard:
        pylab.savefig(outImageFilename)
        logger.info("(plotCalibration) Made plot " + outImageFilename) 
    else:
        pylab.show()
    pylab.close()

    # write data to file
    with open(outDataFilename, 'w+') as f:
        for idx in range(len(magDifference)):
            f.write(str(BRcolour[idx]) + '\t' + str(magDifference[idx]) + '\n')

    # write random subsample of data to file
    ## make sure the number of subsampling points isn't greater than the actual sample size!
    if numSubsamplePoints > len(magDifference):
        numSubsamplePoints = len(magDifference)
   
    ## create random sample
    subsampleIndexes = random.sample(range(len(magDifference)), numSubsamplePoints)

    with open(outDataFilename + ".subsample", 'w+') as f:
        for idx in subsampleIndexes:  
            f.write(str(BRcolour[idx]) + '\t' + str(magDifference[idx]) + '\n')

    # write fit to file
    with open(outDataFilename + ".fit", 'w+') as f:
        for idx in range(len(x)):
            f.write(str(x[idx]) + '\t' + str(y[idx]) + '\n')

def plotMollweide(images, err, logger, bins, hard, outImageFilename, outDataFilename):
    '''
    make Mollweide RA/DEC projection plot given a list of images 
    '''
    RA = []
    DEC = []
    for f in images:
        im = FITSFile(f, err) 
        im.openFITSFile()
        im.getHeaders(0)

        RA.append(im.headers["RA_CENT"])
        DEC.append(im.headers["DEC_CENT"])

    fig = plt.Figure((10, 5))
    ax = fig.add_subplot(111, projection='mollweide')
    ax.set_xlabel('RA')
    ax.set_ylabel('DEC')
    ax.set_xticklabels(np.arange(30,331,30))
    ax.grid(True)

    hist,xedges,yedges = np.histogram2d(DEC, [a - b for a, b in zip(RA, [180]*len(RA))], bins=bins, range=[[-90,90],[-180,180]])	# RA range is from -180 to 180
    X,Y = np.meshgrid(np.radians(yedges),np.radians(xedges))

    image = ax.pcolormesh(X,Y,hist)

    cb = fig.colorbar(image, orientation='horizontal')

    if hard:
        canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)   
        fig.canvas.print_figure(outImageFilename) 
        logger.info("(plotMollweide) Made plot " + outImageFilename) 
    else:
        pass
        # FIXME: add option of soft output

    # write data to file
    with open(outDataFilename, 'w+') as f:
        for idx in range(len(RA)):
            f.write(str(RA[idx]) + '\t' + str(DEC[idx]) + '\n')
