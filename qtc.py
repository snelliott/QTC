#!/usr/bin/env python
import argparse
import multiprocessing

import iotools as io
import obtools as ob
import qctools as qc
import tctools as tc
from pprint import pprint
__updated__ = "2017-06-23"
__author__ = "Murat Keceli"
__logo__ = """
***************************************

     <===>   <=============>   <=>    
  <=>     <=>      <=>      <=>   <=> 
<=>         <=>    <=>     <=>        
<=>         <=>    <=>     <=>        
<=>         <=>    <=>     <=>        
  <=>     <=>      <=>      <=>   <=> 
     <===><>       <=>         <=>   
         <<>>                           
                                      
***************************************
For computation of accurate thermochemistry
By ECP-PACC team                                  
"""

# _mopacexe = 'mopac'
# _nwchemexe = 'nwchem'
# _gaussianexe = 'g09'
# _messpfexe = 'messpf'
# _thermpexe = 'thermp'
# _pac99exe = 'pac99'
# _qcmethod = 'pm3'
# _qcpackage = 'mopac'
# _runqc = False
# _runthermo = False


def get_args():
    """
    Returns args object that contains command line options.
    """
    import argparse
    parser = argparse.ArgumentParser(#formatter_class=argparse.RawDescriptionHelpFormatter,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=
    """
    April 18, 2017

    Performs quantum chemistry calculations to calculate thermochemical parameters.
    Writes NASA polynomials in different formats.
    Provides a unified interface for different codes.
    """)
    parser.add_argument('-i', '--input', type=str,
                        default='qclist.txt',
                        help='List of inchi or smiles for species to be calculated')
    parser.add_argument('-f', '--first', type=int,
                        default=0,
                        help='Beginning index of the species list')
    parser.add_argument('-l', '--last', type=int,
                        help='Ending index of the species list')
    parser.add_argument('-n', '--nproc', type=int,
                        default=1,
                        help='Number of processors, default is one processor')
    parser.add_argument('-m', '--qcmethod', type=str,
                        default='',
                        help='Quantum chemistry method to be used (obsolete, use --rundir)')
    parser.add_argument('-b', '--qcbasis', type=str,
                        default='',
                        help='Basis-set level in quantum chemistry calculations (obsolete, use --rundir)')
    parser.add_argument('-p', '--qcpackage', type=str,
                        default='',
                        help='Quantum chemistry package ("gausian","mopac","nwchem","qcscript") to be used')
    parser.add_argument('-t', '--qctemplate', type=str,
                        default='',
                        help='Template for quantum chemistry input file')
    parser.add_argument('-d', '--qcdirectory', type=str,
                        default='',
                        help='Path for the directory for running qc jobs')
    parser.add_argument('-e', '--qcexe', type=str,
                        default='',
                        help='Path for the executable for qc calculations')
    parser.add_argument('-x', '--xyzpath', type=str,
                        default='',
                        help='Path for the directory for xyz file')
    parser.add_argument('-o', '--qcoutput', type=str,
                        default='',
                        help='Path for the qc output file')
    parser.add_argument('-Q', '--runqc', action='store_true',
                        help='Run quantum chemistry calculation')
    parser.add_argument('-P', '--parseqc', action='store_true',
                        help='Parses quantum chemistry output')
    parser.add_argument('-S', '--subqc', action='store_true',
                        help='Submit quantum chemistry calculations')
    parser.add_argument('-T', '--runthermo', action='store_true',
                        help='Run thermochemistry calculations')
    parser.add_argument('-W', '--writefiles', action='store_true',
                        help='Write .xyz, .ene files')
    parser.add_argument('-I', '--runinteractive', action='store_true',
                        help='Interactive mode for QTC')
    parser.add_argument('-O', '--overwrite', action='store_true',
                        help='Overwrite existing calculations. Be careful, data will be lost.')
    parser.add_argument('-A', '--anharmonic', action='store_true',
                        help='Anharmonic corrections')
    parser.add_argument('--mopac', type=str,
                        default='mopac',
                        help='Path for mopac executable')
    parser.add_argument('--nwchem', type=str,
                        default='nwchem',
                        help='Path for nwchem executable')
    parser.add_argument('--molpro', type=str,
                        default='molpro',
                        help='Path for molpro executable')
    parser.add_argument('--gaussian', type=str,
                        default='g09',
                        help='Path for gaussian executable')
    parser.add_argument('--messpf', type=str,
                        default='messpf',
                        help='Path for MESS partition function executable')
    parser.add_argument('--thermp', type=str,
                        default='thermp',
                        help='Path for thermp executable')
    parser.add_argument('--pac99', type=str,
                        default='pac99',
                        help='Path for pac99 executable')
    parser.add_argument('--qcscript', type=str,
#                        default='/lcrc/project/PACC/test-awj/builddb/bin/qcscript.pl',
                        default='',
                        help='Path for qcscript perl script')
    return parser.parse_args()


def run(s):
    """
    A driver function to run quantum chemistry and thermochemistry calculations based
    on command line options:
    --qcmethod
    --qcpackage
    """
    global parameters
    runqc = parameters['runqc']
    parseqc = parameters['parseqc']
    runthermo = parameters['runthermo']
    runanharmonic = parameters['anharmonic']
    msg = "***************************************\n"
    msg += "{0}\n".format(s)
    mult = ob.get_mult(s)
    mol = ob.get_mol(s)
    smilesname = ob.get_smiles_filename(s)
    smilesdir =  ob.get_smiles_path(mol, mult, method='', basis='', geopath='')
    qcdirectory  = io.join_path(*[smilesdir,parameters['qcdirectory']])
    qctemplate = io.get_path(parameters['qctemplate'])
    qcpackage = parameters['qcpackage']
    qcscript = io.get_path(parameters['qcscript'])
    qclog = smilesname + '_' + qcpackage + '.out'
    xyzpath = parameters['xyzpath']
    xyzfile = None  
    if xyzpath:
        if io.check_file(xyzpath):
            xyzfile = xyzpath
        elif io.check_file(io.join_path(*(smilesdir,xyzpath))):
            xyzfile = io.join_path(*(smilesdir,xyzpath))
        elif io.check_dir(xyzpath):
            try:
                xyzfile = next(io.find_files(xyzpath, '*.xyz'))
            except StopIteration:
                msg += "xyz file not found in {0}".format(xyzpath)
        elif io.check_dir(io.join_path(*(smilesdir,xyzpath))):
            xyzpath = io.join_path(*(smilesdir,xyzpath))
            try:
                xyzfile = next(io.find_files(xyzpath, '*.xyz'))
            except StopIteration:
                msg += "xyz file not found in {0}".format(xyzpath)        
        else:
            msg += "xyz path not found {0}".format(xyzpath)
            return msg
    if xyzfile:
        msg += "Using xyz file in '{0}'\n".format(xyzfile)
        xyz = io.read_file(xyzfile)
        coords = ob.get_coordinates_array(xyz)
        mol = ob.set_xyz(mol, coords)
    print(msg)
    msg = ''
    io.mkdir(qcdirectory)
    cwd = io.pwd()
    if io.check_dir(qcdirectory, 1):
        io.cd(qcdirectory)
        msg += "cd '{0}'\n".format(qcdirectory)
    else:
        msg += ('I/O error, {0} directory not found.\n'.format(qcdirectory))
        return -1
    print(msg)
    msg = ''
    available_packages=['nwchem', 'molpro', 'mopac', 'gaussian', 'extrapolation' ]          
    if runqc:
        if qcpackage in available_packages:
            print('Running {0}'.format(qcpackage))
            msg += qc.run(s, qctemplate, parameters, mult)
        elif qcpackage == 'qcscript':
            msg += "Running qcscript...\n"
            geofile = smilesname + '.geo'
            geo = ob.get_geo(mol)
            io.write_file(geo, geofile)
            if io.check_file(geofile, 1):
                msg += qc.run_qcscript(qcscript, qctemplate, geofile, mult)
        else:
            msg = '{0} package not implemented\n'.format(qcpackage)
            msg += 'Available packages are {0}'.format(available_packages)
            exit(msg)   
        print(msg)
        msg = ''
    if parseqc:
        if io.check_file(qclog, timeout=1,verbose=False):
            out = io.read_file(qclog,aslines=False)
            d = qc.parse_output(out,smilesname, parameters['writefiles'])
            pprint(d)
                                   
    if runthermo:
        groupstext = tc.get_new_groups()
        io.write_file(groupstext, 'new.groups')
        msg += "Parsing qc logfile '{0}'\n".format(io.get_path(qclog))
        newmsg, xyz,freqs,zpe,deltaH,afreqs,xmat = qc.parse_qclog(qclog, qcpackage, anharmonic=runanharmonic)
        msg += newmsg
        if xyz is not None:
            msg += "Optimized xyz in Angstroms:\n{0} \n".format(xyz)
        else:
            runthermo = False
        if freqs is not None:
            msg += "Harmonic frequencies in cm-1:\n {0} \n".format(freqs)
        else:
            runthermo = False        
        if afreqs:
            msg += "Anharmonic frequencies in cm-1:\n {0}\n".format(afreqs)
        else:
            runanharmonic = False        
        if zpe:
            msg += 'ZPE = {0} kcal/mol\n'.format(zpe)
        else:
            runthermo = False        
        if deltaH is not None:
            msg += 'deltaH = {0} kcal/mol\n'.format(deltaH)
        else:
            runthermo = False        
        if xmat is not None:
            msg += 'Xmat = {0} kcal/mol\n'.format(xmat)   
        else:
            runanharmonic = False        
        if runthermo:    
            msg += tc.write_chemkin_polynomial(mol, zpe, xyz, freqs, deltaH, parameters)
    io.cd(cwd)
    print(msg)
    return

    
if __name__ == "__main__":
    from socket import gethostname
    from timeit import default_timer as timer
    from sys import exit
    global parameters
    available_packages=['nwchem', 'molpro', 'mopac', 'gaussian' ]
    start  = timer()
    args = get_args()
    parameters = vars(args)
    if not parameters['qcpackage']:
        if not parameters['qctemplate']:
            if parameters['runqc']:
                exit('Please specify template file with -t')
        else:
            parameters['qcpackage'] = qc.get_package(parameters['qctemplate'])
    if not parameters['qcexe']:
        if parameters['qcpackage'] in available_packages:
            parameters['qcexe'] = parameters[parameters['qcpackage']]
    if parameters['writefiles']:
        parameters['parseqc'] = True
    parameters['qctemplate'] = io.get_path(args.qctemplate)
    parameters['qcexe'] = io.get_path(args.qcexe,executable=True)
    parameters['qcscript'] = io.get_path(args.qcscript)
    parameters['mopac'] = io.get_path(args.mopac,executable=True)
    parameters['nwchem'] = io.get_path(args.nwchem,executable=True)
    parameters['gaussian'] = io.get_path(args.gaussian,executable=True)
    parameters['molpro'] = io.get_path(args.molpro,executable=True)
    parameters['messpf'] = io.get_path(args.messpf,executable=True)
    parameters['thermp'] = io.get_path(args.thermp,executable=True)
    parameters['pac99'] = io.get_path(args.pac99,executable=True)
    beginindex = args.first
    endindex = args.last
    inp = args.input
    nproc = args.nproc
    if io.check_file(inp):
        mylist = io.read_list(inp)
    else:
        mylist = inp.split(',')
    if endindex:
        mylist = mylist[beginindex:endindex]
    else:
        mylist = mylist[beginindex:]        
    print(__logo__)
    print("QTC: Date and time           = {0}".format(io.get_date()))
    print("QTC: Last update             = {0}".format(__updated__))
    print("QTC: Number of processes     = {0}".format(nproc))
    print("QTC: Hostname                = {0}".format(gethostname()))
    print('QTC: Given arguments         =')
    for param in parameters:
        print('                             --{0:20s}\t{1}'.format(param, getattr(args, param)))
    print("QTC: Number of species       = {0}".format(len(mylist)))
    init = timer()
    print("QTC: Initialization time (s) = {0:.2f}".format(init-start))
    if nproc > 1:
        pool = multiprocessing.Pool(nproc)
        pool.map(run, mylist)
    else:
        results = map(run, mylist)
    end = timer()
    print("QTC: Calculations time (s)   = {0:.2f}".format(end - init))
    print("QTC: Total time (s)          = {0:.2f}".format(end-start))
    print("QTC: Date and time           = {0}".format(io.get_date()))

