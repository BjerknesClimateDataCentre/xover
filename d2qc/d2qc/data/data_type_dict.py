#######################################################
#
# Get NODC - identifiers for variables and units in
# data files, primarily used by mockimport.py
#
#######################################################


class DataTypeDict():
    # These are available from:
    # https://goo.gl/S4cfre

    conversions={
        'TCARBN'     : 'SDN:P01::TCO2MSXX',
        'ALKALI'     : 'SDN:P01::MDMAP014',
        'OXYGEN'     : 'SDN:P01::DOKGWITX',
        'NITRAT'     : 'SDN:P01::MDMAP005',
        'PHSPHT'     : 'SDN:P01::MDMAP906',
        'SILCAT'     : 'SDN:P01::MDMAP012',
        'SALNTY'     : 'SDN:P01::PSLTZZ01',
        'CTDSAL'     : 'SDN:P01::PSLTZZ01',
        'CTDOXY'     : 'SDN:P01::DOKGWITX',
        'PH_TOT'     : 'SDN:P01::PHTLSX25', # TODO: This is at 25°C. Alt: SDN:P01::PHMASSXX
        'THETA'      : 'SDN:P01::POTMCV01', # TODO: Computed using UNESCO 1983 algorithm. Check this!!
        'DOC'        : 'SDN:P01::COCOKGXX',
        'CFC_11'     : 'SDN:P01::FR11GCKG',
        'CFC_12'     : 'SDN:P01::FR12GCKG',
        'G2tco2'     : 'SDN:P01::TCO2MSXX',
        'G2talk'     : 'SDN:P01::MDMAP014',
        'G2oxygen'   : 'SDN:P01::DOKGWITX',
        'G2nitrate'  : 'SDN:P01::MDMAP005',
        'G2phosphate': 'SDN:P01::MDMAP906',
        'G2silicate' : 'SDN:P01::MDMAP012',
        'G2salinity' : 'SDN:P01::PSLTZZ01',
        'G2phts25p0' : 'SDN:P01::PHTLSX25',
        'G2theta'    : 'SDN:P01::POTMCV01',
        'G2doc'      : 'SDN:P01::COCOKGXX',
        'G2cfc11'    : 'SDN:P01::FR11GCKG',
        'G2cfc12'    : 'SDN:P01::FR12GCKG',
        'DBAR'       : '', # Only millibar in the definitions
        'ITS-90'     : 'SDN:P06::UPAA',
        'PSS-78'     : 'SDN:S06::S0600083',
        'UMOL/KG'    : 'SDN:P06::KGUM',
        'PMOL/KG'    : 'SDN:P06::KGPM',
        'FMOL/KG'    : 'SDN:P06::FGKG',
        'tco2'     : 'SDN:P01::TCO2MSXX',
        'talk'     : 'SDN:P01::MDMAP014',
        'oxygen'   : 'SDN:P01::DOKGWITX',
        'nitrate'  : 'SDN:P01::MDMAP005',
        'phosphate': 'SDN:P01::MDMAP906',
        'silicate' : 'SDN:P01::MDMAP012',
        'salinity' : 'SDN:P01::PSLTZZ01',
        'phts25p0' : 'SDN:P01::PHTLSX25',
        'theta'    : 'SDN:P01::POTMCV01',
        'doc'      : 'SDN:P01::COCOKGXX',
        'cfc11'    : 'SDN:P01::FR11GCKG',
        'cfc12'    : 'SDN:P01::FR12GCKG',
    }

    @classmethod
    def getIdentFromVar(cls, var_name):
        return cls.conversions.get(var_name) or ""
