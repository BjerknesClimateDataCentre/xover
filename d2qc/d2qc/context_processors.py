
def globals(request):
    """Constants available to every template page"""


    global_vars = {
        # Site name
        'SITE_HEADER': "GLODAP Crossover QC tools",
    }
    return global_vars
