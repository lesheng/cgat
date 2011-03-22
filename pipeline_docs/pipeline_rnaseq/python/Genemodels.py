import os, sys, re, types, itertools

from SphinxReport.Tracker import *
from SphinxReport.odict import OrderedDict as odict

'''
cuffcompare results.

'''

from RnaseqReport import *

class TrackerGenemodels( TrackerSQL ):
    mPattern = "_gene_expression"

    def getTracks( self, subset = None ):
        return self.getValues( "SELECT DISTINCT track FROM %s" % self.name )

class GeneModelsBenchmark( TrackerGenemodels ):
    name = "agg_agg_agg_cuffcompare_benchmark"

    def getSlices( self, subset = None ):
        '''slice by contig'''
        return ('all',) # self.getValues( "SELECT DISTINCT contig FROM transcripts_compare" )

    def __call__(self, track, slice = None ):
        return self.getRow( """
               SELECT baselevel_sp, baselevel_sn,
                      exonlevel_sp, exonlevel_sn,
                      transcriptlevel_sp, transcriptlevel_sn,
                      intronlevel_sp, intronlevel_sn,
                      locuslevel_sp, locuslevel_sn,
                      100.0 * missedexons_counts / missedexons_total AS missed_exons,
                      100.0 * missedloci_counts / missedloci_total AS missed_loci,
                      100.0 * wrongexons_counts / wrongexons_total AS wrong_exons,
                      100.0 * wrongloci_counts / wrongloci_total AS wrong_loci
                      FROM %(name)s WHERE track = '%(track)s' AND contig = '%(slice)s'
               """ % self.members(locals()))

class GeneModelsCodes( TrackerSQL ):
    mPattern = "_cuffcompare_tracking"
    mAsTables = True

    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")

    def __call__(self, track, slice = None ):
        return self.getValue( """SELECT COUNT(*) FROM %(track)s WHERE code = '%(slice)s'""" )

class GeneModelsSharedLoci( TrackerSQL ):
    '''number of times a locus appears in experiments.'''
    mPattern = "_cuffcompare_loci"
    mAsTables = True
    
    def __call__(self, track, slice = None ):
        return self.getAll( "SELECT nexperiments, count(*) FROM %(track)s group by nexperiments" )

class GeneModelsSharedTransfrags( TrackerSQL ):
    '''number of times a transfrag appears in experiments.'''
    mPattern = "_cuffcompare_tracking"
    mAsTables = True

    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")
    
    def __call__(self, track, slice = None ): 
        return self.getAll( "SELECT nexperiments, count(*) FROM %(track)s WHERE code = '%(slice)s' group by nexperiments" )

class ExpressionByClass( TrackerSQL ):
    '''number of times a transfrag appears in experiments.'''
    mPattern = "_cuffcompare_tracking"
    mAsTables = False

    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")
    
    def __call__(self, track, slice = None ): 
        vals = self.getValues( """SELECT avg(FPKM)
                                      FROM %(track)s_cuffcompare_tracking AS t,
                                           %(track)s_cuffcompare_transcripts AS a
                                      WHERE code = '%(slice)s' AND 
                                      a.transfrag_id = t.transfrag_id
                                      GROUP BY a.transfrag_id""" % locals() )
        return odict( ( ("fpkm", vals), ) )

class TransfragCorrelation( TrackerSQL ):
    '''return correlation table 
    '''
    mPattern = "_reproducibility"

    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")
   
    def __call__(self, track, slice = None ):
        data = self.getAll( """SELECT track1, track2, 
                                      coeff, pvalue, significance,
                                      pairs, both_null, null1, null2, 
                                      method, alternative
                               FROM %(track)s_reproducibility 
                               WHERE code = '%(slice)s'""" )
        return data

class TransfragReproducibility2( TrackerSQL ):
    '''return proportion of transfrags present in a pair of replicates.
    '''

    mPattern = "_reproducibility"
 
    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")
   
    def __call__(self, track, slice = None ):
        data = self.getAll( """SELECT track1, track2, 
                                      ROUND( CAST( not_null AS FLOAT) / (pairs-both_null),2) AS pcalled,
                                      ROUND( coeff, 2) as correlation
                               FROM %(track)s_reproducibility 
                               WHERE code = '%(slice)s'""" )
        return data

class TransfragReproducibility( TrackerSQL ):
    '''return proportion of transfrags present in a pair of replicates.
    '''

    mPattern = "_reproducibility"
 
    def getSlices( self, subset = None ):
        return tuple("=cjeiopruxs.*")
   
    def __call__(self, track, slice = None ):
        data = self.getDict( """SELECT track1 || '_x_' || track2 AS tracks, 
                                      ROUND( CAST( not_null AS FLOAT) / (pairs-both_null),2) AS pcalled,
                                      ROUND( coeff, 2) as correlation
                               FROM %(track)s_reproducibility 
                               WHERE code = '%(slice)s'""" )
        return data

class GenesetSummary( SingleTableTrackerRows ):
    table = "geneset_stats"
    column = "track"