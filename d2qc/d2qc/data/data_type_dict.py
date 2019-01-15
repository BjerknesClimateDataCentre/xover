#######################################################
#
# Get NODC - identifiers for variables and units in
# data files, primarily used by mockimport.py
#
#######################################################

class MetaDict(type):
    def __iter__(self):
        for key in DataTypeDict.conversions:
            yield key
    def __getitem__(self, key):
        return DataTypeDict.getIdentFromVar(key)

class DataTypeDict(metaclass=MetaDict):
    # These are available from the bodc vocabulary search at:
    # https://www.bodc.ac.uk/resources/vocabularies/vocabulary_search/
    # https://www.bodc.ac.uk/resources/vocabularies/vocabulary_search/P01/

    conversions={
        'TCARBN'       : 'SDN:P01::PCO2XXXX',
        'ALKALI'       : 'SDN:P01::ALKYZZXX',
        'OXYGEN'       : 'SDN:P01::DOXMZZXX',
        'NITRAT'       : 'SDN:P01::NTRAZZXX',
        'PHSPHT'       : 'SDN:P01::PHOSZZXX',
        'SILCAT'       : 'SDN:P01::SLCAZZXX',
        'SALNTY'       : 'SDN:P01::PSALST01', # absolute salinity SDN:P01::ASLTZZ01
        'CTDSAL'       : 'SDN:P01::PSALST01',
        'CTDOXY'       : 'SDN:P01::DOXMZZXX',
        'PH_TOT'       : 'SDN:P01::PHFRSXXX',
        'THETA'        : 'SDN:P01::POTMCV01',
        'DOC'          : 'SDN:P01::CORGZZZX',
        'CFC_11'       : 'SDN:P01::MDMAP001',
        'CFC_12'       : 'SDN:P01::MDMAP002',
        'G2tco2'       : 'SDN:P01::PCO2XXXX',
        'G2talk'       : 'SDN:P01::ALKYZZXX',
        'G2oxygen'     : 'SDN:P01::DOXMZZXX',
        'G2nitrate'    : 'SDN:P01::NTRAZZXX',
        'G2phosphate'  : 'SDN:P01::PHOSZZXX',
        'G2silicate'   : 'SDN:P01::SLCAZZXX',
        'G2salinity'   : 'SDN:P01::PSALST01',
        'G2phts25p0'   : 'SDN:P01::PHTLSX25',
        'G2theta'      : 'SDN:P01::SIGTEQ01',
        'G2doc'        : 'SDN:P01::CORGZZZX',
        'G2cfc11'      : 'SDN:P01::MDMAP001',
        'G2cfc12'      : 'SDN:P01::MDMAP002',
        'tco2'         : 'SDN:P01::PCO2XXXX',
        'talk'         : 'SDN:P01::ALKYZZXX',
        'oxygen'       : 'SDN:P01::DOKGWITX',
        'nitrate'      : 'SDN:P01::MDMAP005',
        'phosphate'    : 'SDN:P01::PHOSZZXX',
        'silicate'     : 'SDN:P01::SLCAZZXX',
        'salinity'     : 'SDN:P01::PSALST01',
        'phts25p0'     : 'SDN:P01::PHTLSX25',
        'theta'        : 'SDN:P01::SIGTEQ01',
        'doc'          : 'SDN:P01::CORGZZZX',
        'cfc11'        : 'SDN:P01::MDMAP001',
        'cfc12'        : 'SDN:P01::MDMAP002',
        'CTDTMP'       : 'SDN:P01::TEMPPR01',
        'NO2+NO3'      : 'SDN:P01::NTRZYYDZ',
        'NITRIT'       : 'SDN:P01::NTRIZZXX',
        'aou'          : 'SDN:P01::AOUXXXXX',
        'tdn'          : 'SDN:P01::MDMAP013',
        'pcfc11'       : 'SDN:P01::PF11GCTX',
        'pressure'     : 'SDN:P01::PRESPR01',
        'gamma'        : 'SDN:P01::NEUTDENS',
        'he3err'       : 'SDN:P01::S3HHMXTX',
        'sigma1'       : 'SDN:P01::POTDENS1',
        'cfc113'       : 'SDN:P01::MDMAP003',
        'pcfc12'       : 'SDN:P01::PF12GCTX',
        'sigma3'       : 'SDN:P01::POTDENS3',
        'c14'          : 'SDN:P01::D14CMIXX',
        'psf6'         : 'SDN:P01::PSF6XXXX',
        'he3'          : 'SDN:P01::DHE3XX01',
        'c14err'       : 'SDN:P01::D14CMIER',
        'neon'         : 'SDN:P01::NECNMASS',
        'neonerr'      : 'SDN:P01::NECNMAER',
        'pcfc113'      : 'SDN:P01::P113GCTX',
        'sf6'          : 'SDN:P01::PSF6XXXX',
        'pccl4'        : 'SDN:P01::PCCL4XXX',
        'sigma2'       : 'SDN:P01::POTDENS2',
        'sigma4'       : 'SDN:P01::POTDENS4',
        'ccl4'         : 'SDN:P01::CCL4AFX1',
        'toc'          : 'SDN:P01::MDMAP011',
        'temperature'  : 'SDN:P01::TEMPPR01',
        'he'           : 'SDN:P01::HECNMASS',
        'c13'          : 'SDN:P01::D13COPXX',
        'nitrite'      : 'SDN:P01::NTRIZZXX',
        'o18'          : 'SDN:P01::D18OSDWT', # Alt:  D18OMXDG (in dissolved O2)
        'sigma0'       : 'SDN:P01::POTDENS0',
        'don'          : 'SDN:P01::MDMAP008',
        'h3'           : 'SDN:P01::ACTVM012',
        'heerr'        : 'SDN:P01::HECNMAER',
        'h3err'        : 'SDN:P01::DHE3XXER',
        'phtsinsitutp' : 'SDN:P01::PHFRSXXX',
        'chla'         : 'SDN:P01::CPHLZZXX',

        # Units
        'DBAR'       : 'SDN:P06::UPDB',
        'ITS-90'     : 'SDN:P06::UPAA',
        'PSS-78'     : 'SDN:S06::S0600083',
        'UMOL/KG'    : 'SDN:P06::KGUM',
        'PMOL/KG'    : 'SDN:P06::KGPM',
        'FMOL/KG'    : 'SDN:P06::FGKG',
    }



    @classmethod
    def getIdentFromVar(cls, var_name):
        return cls.conversions.get(var_name) or ""
